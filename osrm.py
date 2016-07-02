#!/usr/bin/python
import os
import socket
import subprocess
import shutil
import urllib2
import json
import logging
import errno
import time
import csv


class OSRMRunner(object):
    OSRM_BIN_DIR = "/usr/local/bin"

    def __init__(self, working_dir, speed_profile, orig_osm_filename, port, stxxl_filename, stxxl_size):
        self.bin_osrm_extract = os.path.join(self.OSRM_BIN_DIR, "osrm-extract")
        self.bin_osrm_contract = os.path.join(self.OSRM_BIN_DIR, "osrm-contract")
        self.bin_osrm_routed = os.path.join(self.OSRM_BIN_DIR, "osrm-routed")

        self._check_bin(self.bin_osrm_extract)
        self._check_bin(self.bin_osrm_contract)
        self._check_bin(self.bin_osrm_routed)

        self.working_dir = os.path.abspath(working_dir)
        self.speed_profile = os.path.abspath(speed_profile)
        self.orig_osm_filename = os.path.abspath(orig_osm_filename)
        self.osm_symlink = os.path.join(self.working_dir, os.path.basename(self.orig_osm_filename))
        self.port = port
        self.stxxl_filename = os.path.abspath(stxxl_filename)
        self.stxxl_size = stxxl_size

        self.osrm_filename = OSRMRunner.parse_osrm_filename(orig_osm_filename)

        self.server_popen = None  # osrm-routed subprocess.Popen object.

    def run(self):
        """ Pass overwrite=True to force it run anyway even when workding_dir already exists.
        """
        self._check_osrm_routed_process(self.port)
        self._check_stxxl_file(self.stxxl_filename)

        self._create_working_dir(self.working_dir)

        self.link_osm_file()
        self.create_stxxl_config()
        self.osrm_extract()
        self.osrm_contract()
        self.osrm_routed()

    @staticmethod
    def parse_osrm_filename(osm_filename):
        filename = os.path.basename(osm_filename)
        if len(osm_filename) <= 8 or filename[-8:] != ".osm.pbf":
            raise Exception("osm filename is not valid (should be xxx.osm.pbf): %s" % (osm_filename,))
        return filename[:-8] + ".osrm"

    def _check_bin(self, bin_file):
        if not os.path.isfile(bin_file):
            msg = "osrm bin %s not found at: %s" % (os.path.basename(bin_file), bin_file)
            logging.info(msg)
            raise Exception(msg)

    def _create_working_dir(self, working_dir):
        if not self._ensure_dir(working_dir):
            msg = "OSRM working directory already exists: %s. Please delete it first" \
                  " or Use osrm_routed() instead of run()!" % working_dir
            logging.error(msg)
            raise Exception(msg)

    def _check_stxxl_file(self, stxxl_filename):
        self._ensure_dir(os.path.dirname(stxxl_filename))
        if os.path.exists(stxxl_filename):
            msg = "OSRM stxxl file already exists: %s" % stxxl_filename
            raise Exception(msg)

    def _check_osrm_routed_process(self, port):
        if check_server("127.0.0.1", port):
            raise Exception("port %s is already used by other program." % (port,))

    def _ensure_dir(self, dirname):
        try:
            os.makedirs(dirname)
            return True
        except os.error as e:
            if e.errno != errno.EEXIST:
                raise e
            return False

    def create_stxxl_config(self):
        # create stxxl configuration
        logging.info("Creating STXXL configuration")
        content = "disk=%s,%s,syscall" % (self.stxxl_filename, self.stxxl_size)
        with open(os.path.join(self.working_dir, ".stxxl"), 'w') as f:
            f.write(content)

    def link_osm_file(self):
        """ Because osrm-extract always generate osrm-related files in the same directory as osm_file
         so we need to make a symbolic link to osm_file from working directory """
        if os.path.exists(self.osm_symlink):
            os.remove(self.osm_symlink)
        os.symlink(self.orig_osm_filename, self.osm_symlink)

    def osrm_extract(self):
        logging.info("Running osrm-extract ...")
        cmd = "osrm-extract %s -p %s" % (self.osm_symlink, self.speed_profile)
        subprocess.check_call(cmd, cwd=self.working_dir, shell=True)
        logging.info("--- Completed osrm-extract ---")

    def osrm_contract(self):
        logging.info("Running osrm-contract ...")
        cmd = "osrm-contract %s" % (self.osrm_filename,)
        subprocess.check_call(cmd, cwd=self.working_dir, shell=True)
        logging.info("--- Completed osrm-contract ---")

    def osrm_routed(self):
        self._check_osrm_routed_process(self.port)

        if self.server_popen is not None:
            logging.warn("osrm-routed server is already running: PID %s" % (self.server_popen.pid,))
            return

        logging.info("Launching OSRM server...")
        self.server_popen = subprocess.Popen(['osrm-routed', '-p', str(self.port), self.osrm_filename],
                                             cwd=self.working_dir)
        time.sleep(5)  # waiting for intialization of osrm-routed.

    def close_server(self):
        if self.server_popen is None:
            logging.warn("Server is not running. Do nothing.")
            return

        logging.info("Close OSRM server...")
        self.server_popen.kill()

    def cleanup(self):
        logging.info("Cleaning OSRM ...")
        self.close_server()

        logging.info("Delete working dir: %s", self.working_dir)
        shutil.rmtree(self.working_dir, ignore_errors=True)
        try:
            logging.info("Delete stxxl file: %s", self.working_dir)
            os.remove(self.stxxl_filename)
        except OSError as e:
            if e.errno == errno.ENOENT:
                logging.info("stxxl file not found: %s, ignored.", self.stxxl_filename)
            else:
                raise e
        logging.info("Cleaned!")

    def routes(self, start, end):
        url = "http://localhost:%s/route/v1/driving/%s;%s" % (self.port, start, end)
        try:
            r = urllib2.urlopen(url)
            text = r.read()
            return json.loads(text)
        except urllib2.HTTPError as e:
            logging.error("osrm /route api error: %s", url)
            raise e

    def first_route_summary(self, start, end):
        data = self.routes(start, end)
        duration = data['routes'][0]['duration']
        distance = data['routes'][0]['distance']
        return duration, distance


def check_server(address, port):
    s = socket.socket()
    try:
        s.connect((address, port))
        s.close()
        return True
    except socket.error as e:
        return False


def test(test_id, port, sample_data_file, speed_profile, osm_filename,
         working_basedir="./tmp", result_dir="./result", stxxl_dir="./tmp-stxxl", stxxl_size=1000):
    test_id = str(test_id)
    logging.info("start test #%s, port: %s", test_id, port)

    working_dir = os.path.join(working_basedir, test_id)
    stxxl_filename = os.path.join(stxxl_dir, test_id + ".stxxl")

    osrm = OSRMRunner(working_dir, speed_profile, osm_filename, port, stxxl_filename, stxxl_size)
    osrm.run()
    # NOTE: you can use osrm.osrm_routed() instead of osrm.run()
    #       to avoid re-generating osrm files every time.

    result_fields = ['id', 'start', 'end', 'duration', 'distance']
    result_file = os.path.join(result_dir, test_id + ".csv")

    with open(sample_data_file, "rb") as r, open(result_file, "wb") as w:
        reader = csv.DictReader(r)
        writer = csv.writer(w)
        writer.writerow(result_fields)

        for row in reader:
            tid = row['id']
            start = row['start_lng'] + "," + row['start_lat']
            end = row['end_lng'] + "," + row['end_lat']

            logging.info("Testing id#%s ...", tid)

            try:
                duration, distance = osrm.first_route_summary(start, end)
                writer.writerow([tid, start, end, duration, distance])
            except urllib2.HTTPError as e:
                logging.info("[Fail] test id#%s, msg: %s", tid, e.msg)

    logging.info("end test #%s. Note: (osrm-routed -p %s) still running so you can manually test againt.",
                 test_id, port)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    speed_profile = "./profiles/car.lua"
    osm_filename = "./indonesia-jakarta.osm.pbf"
    test_data_file = "sample.csv"

    # NOTE: here it keeps osrm-routed server remainning open so you can manually test abnormal cases.
    test("t1", 20086, test_data_file, speed_profile, osm_filename)
    test("t2", 20087, test_data_file, speed_profile, osm_filename)
