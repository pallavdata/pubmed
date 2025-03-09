import argparse
from pubmed import fetch, log
import sys

if len(sys.argv) <= 1:
    print('You can use "ENTER" to use default value\n')
    query = input("Query : ")
    if not query:
        print("Empty Query") 
    debug = input("Debug [Default:n][Input:y/n]: ")
    if not debug in ["","y","n"]:
        print('"y","n" or Empty input allowed')
    force = input("Add article without author [Default:n][Input:y/n]: ")
    if force == "y":
        force = True
    elif force == "n" or force == "":
        force = False
    else:
        print('"y","n" or Empty input allowed')
    count = input("Max numbers of article to parse[Default:ALL][Input:any integer]: ")
    if count == "ALL" or not count:
        count = None
    elif count.isdigit():
        count = int(count)
    else:
        print('Integer or Empty input allowed')
    file = input("File Path [Default:Print in the console] : ")
    if debug == "y":
        log(True)
    obj = fetch(query,force, count)
    obj.save(file)
else:
    parser = argparse.ArgumentParser(
        description="Fetch MetaData of the PUBMED Papers")

    parser.add_argument("-d", "--debug", dest="debug",
                        action="store_true", help="debug the program")
    parser.add_argument("-q", "--query", dest="query",
                        type=str, help="query to get papers")
    parser.add_argument("-f", "--file", dest="file", type=str,
                        help="Path of the output file.")
    parser.add_argument("--force", dest="force",
                        action='store_true', help="Force article to be added even if author is not present")
    parser.add_argument("--c","--count", dest="count",
                        type=int, help="Number of article. By default all")
    parser.add_argument("-e", "--ext", dest="extension",
                        action='store_true', help='.json, .csv and .xlsx')

    args = parser.parse_args()

    if args.extension:
        print('Extension Supported: .json, .csv and .xlsx')
        if args.query:
            print('remove -e or --ext to run the program')
    if not args.extension:
        if args.debug:
            log(True)
        if args.query:
            obj = fetch(args.query,args.force, args.count)
            obj.save(args.file)
        else:
            print("EMPTY QUERY")
