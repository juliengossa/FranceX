
import csv
import sys
import argparse
from inpi import Inpi
import time

parser = argparse.ArgumentParser(
    prog='inpi-excavator',
    description='Retrieve PI data from INPI')
parser.add_argument('-u', '--username')
parser.add_argument('-p', '--password')
parser.add_argument('-s', '--search')
parser.add_argument('--size', default=500, type=int)
parser.add_argument('-l', '--limit', default=5, type=int)
parser.add_argument('-c', '--csv')
parser.add_argument('-n', '--notice', action='store_true')
parser.add_argument('-r', '--recovery')

args = parser.parse_args()

inpi = Inpi(args.username,args.password)

noticesurls = []

if args.search:
    results = inpi.search(args.search, limit=args.limit, size=args.size)

    csvwriter = csv.writer(sys.stdout, delimiter=';',quotechar='"')
    csvwriter.writerow(inpi.get_searchvar())
    for m in results:
        csvwriter.writerow(inpi.mark2array(m))
        noticesurls.append(m['xml']['href'])

if args.csv:
    with open(args.csv) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        for row in csvreader:
            noticesurls.append(row['url'])

if args.notice:
    csvwriter = csv.writer(sys.stdout, delimiter=';',quotechar='"')
    csvwriter.writerow(inpi.get_noticevar())

    start = int(args.recovery if args.recovery is not None else 0)
    for i,url in enumerate(noticesurls[start:]):

        print("Retrieving "+str(i+start)+"/"+str(len(noticesurls))+" : "+url, file=sys.stderr)
        while True:
            try:
                notice = inpi.get_notice(url)
                time.sleep(0.5)
                break
            except IOError:
                print("Too many requests. Waiting 5 minute.", file=sys.stderr)
                time.sleep(300)

        csvwriter.writerow(inpi.notice2array(notice))
        sys.stdout.flush()
        sys.stderr.flush()
