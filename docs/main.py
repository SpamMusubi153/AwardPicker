
import base64
import csv

from datetime import datetime

from browser import document
from browser.local_storage import storage

# Read the spreadsheet file from localstorage.

SPREADSHEET_LOCALSTORAGE_KEY = "spreadsheet"

def get_spreadsheet(localstorage_key):
    encoded_spreadsheet = storage[localstorage_key]

    assert (encoded_spreadsheet is not None), "The spreadsheet could be be retrieved."

    spreadsheet = base64.b64decode(encoded_spreadsheet)

    return spreadsheet

def get_spreadsheet_reader(spreadsheet):
    reader = csv.reader(spreadsheet, delimiter=',', quotechar='"')
    return reader


def main():

    print("Main program loaded.")

    # Wait for the spreadsheet to become accessible from localstorage.
    spreadsheet = None
    while True:
        try:
            spreadsheet = get_spreadsheet()
            break
        except:
            pass

    print(spreadsheet)
    

main()

