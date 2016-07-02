import os
import sys
import csv

def csv_read(filename):
    with open(filename, "rb") as f:
        return list(csv.reader(f))

def compare(file1, file2):
    data1 = csv_read(file1)
    data2 = csv_read(file2)

    header_format = "{:^10} | {:^26} | {:^26} | {:^19} | {:^22}"
    row_format = "{:<10} | {:<26} | {:<26} | {:>+5.1f} {:>6} {:<6} | {:>+8.1f} {:>8} {:<8}"
    print(header_format.format("id", "start", "end", "time compare", "distance compapre"))
    print("-" * 106)

    for i in range(len(data1)):
        tid1, start1, end1, duration1, distance1 = data1[i]
        tid2, start2, end2, duration2, distance2 = data2[i]
        if tid1 != tid2 or start1 != start2 or end1 != end2:
            raise Exception("compare() error:%d: id,start,end columns in both file should be the same, but: %s %s. " \
                    "Make sure you are comparing the right files", i + 1, data1[i], data2[i])
        if duration1 != duration2 or distance1 != distance2:
            time_diff = float(duration1) - float(duration2)
            distance_diff = float(distance1) - float(distance2)
            print(row_format.format(tid1, start1, end1, time_diff, duration1, duration2, distance_diff, distance1, distance2))


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "please provide two files to compare"
        sys.exit(1)

    compare(sys.argv[1], sys.argv[2])

