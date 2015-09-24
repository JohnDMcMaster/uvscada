from uvscada.mygeiger import MyGeiger
import argparse
import csv
import datetime
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a count csv')
    parser.add_argument('--port', '-p', default='/dev/ttyUSB0', help='')
    parser.add_argument('out', nargs="?", default='/dev/stdout', help='')
    args = parser.parse_args()

    mg = MyGeiger(port=args.port)
    f = open(args.out, 'w')
    cw = csv.writer(f)
    cw.writerow(['t', 'cpm'])
    f.flush()
    i = 0
    while True:
        cpm = mg.cpm()
        cw.writerow([time.time(), datetime.datetime.utcnow().isoformat(), i, cpm])
        f.flush()
        i += 1
    f.close()

