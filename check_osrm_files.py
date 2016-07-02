import sys
import os

import hashlib


def flist(path):
    return [os.path.join(path, f) for f in sorted(os.listdir(path))]

def md5sum(filename):
    m = hashlib.md5()
    m.update(open(filename, "rb").read())
    return m.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "please provide two osrm files dir to compare md5 hash."
        sys.exit(1)

    dir1 = sys.argv[1]
    dir2 = sys.argv[2]

    lst1 = flist(dir1)
    lst2 = flist(dir2)

    for i in range(len(lst1)):
        f1 = lst1[i]
        f2 = lst2[i]

        m1 = md5sum(f1)
        m2 = md5sum(f2)

        b1 = os.path.basename(f1)
        b2 = os.path.basename(f2)

        if b1 != b2:
            print("Error: two osrm files dir have different set of files")
            sys.exit(1)

        if m1 == m2:
            print(u"{:<42} {}  {:<32} {:<32}".format(os.path.basename(lst1[i]), u'\u2714', m1, m2))
        else:
            print(u"{:<42} {}  {:<32} {:<32}".format(os.path.basename(lst1[i]), u'\u2718', m1, m2))



