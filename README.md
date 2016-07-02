# osrm-test
`/route` API service of two OSRM instance (generated from same profile and osm.pbf) give different (`duration` `distance`) result even though they are both given same start and end coordinates.

# How to test?
1. First install OSRM. (Note: default install location is `/usr/local/bin`. If your is different, please modify OSRMRunner.OSRM_BIN_DIR variable in osrm.py)
2. Open osrm.py and edit some variable as you like, then run osrm.py:
```
python osrm.py
```
3. After osrm.py run finish it should generate two files in `./result`  directory: `./result/t1.csv`, `./result/t2.csv` .
4. Run `compare_result.py` script to see the differences:
```
python compare_result.py result/t1.csv result/t2.csv
```
5. Run `check_osrm_files.py` to see osrm generated files md5 diffs:
```
python check_osrm_files.py tmp/t1 tmp/t2
```

# Some Notes
1. An OSRM instance is always return same result for same input. (only `/route` API tested.)
2. Most of input will give same result among different instance. But different pairwise instances disagree on different subset of input.