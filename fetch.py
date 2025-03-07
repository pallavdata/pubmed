import argparse
from pubmed import pubmed

parser = argparse.ArgumentParser(description="Fetch MetaData of the PUBMED Papers")

# Add arguments
parser.add_argument("-d","--debug",dest="debug", action="store_true", help="debug the program")
parser.add_argument("-q","--query",dest="query", type=str, help="query to get papers")
parser.add_argument("-f","--file",dest="file", type=str, help="path of the output file")

args = parser.parse_args()

