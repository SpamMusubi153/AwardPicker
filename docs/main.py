
from dataclass import dataclass
import string
import base64
import csv

from datetime import datetime

from browser import document, alert
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

    spreadsheet = get_spreadsheet()

    reader = get_spreadsheet_reader(spreadsheet)


    # Variables to store results
    # Storage Format = {
    #                   Specialist Name : [List of Records],
    # 
    #                  }
    sorted_by_specialist = {}

    # Storage Format = {
    #                   Class Name : [List of Records],
    #                  }
    sorted_by_class = {}

    @dataclass
    class Record:
        month : int
        specialist : string
        class_name : string


    def add_result(record : Record):

        # Add the result to the sorted_by_specialist dictionary.
        # If the current specialist key does not exist, create it = now.
        if sorted_by_specialist[record.specialist] is None:
            sorted_by_specialist[record.specialist] = []
            sorted_by_specialist[record.specialist].append(record)

        
        # Otherwise, if the key exists, just add the record.
        else:
            sorted_by_specialist[record.specialist].append(record)


        # Then, add the result to the sorted_by_class dictionary.
        if sorted_by_class[record.class_name] is None:
            sorted_by_class[record.class_name] = []
            sorted_by_class[record.class_name].append(record)
        else:
            sorted_by_class[record.class_name].append(record)


    for i, row in enumerate(reader):

        # Remove any quotation characters that separate teacher names
        row = row.replace('"', "")

        # Skip over the header row
        if row == 0:
            continue

        current_date = None
        current_specialist = None
        for j in range(len(row)):

            # Extract the date from the first column of each row.
            if j == 0:                
                current_date = datetime.strptime(row[j], "%-m/%-d/%Y %-H:%-I:%-S")

            elif j == 1:
                current_specialist = row[j]

            else:
                current_record = Record(current_date.month, current_specialist, row[j])
                add_result(current_record)

    alert(sorted_by_class)
    alert(sorted_by_specialist)
    alert("Running!")

alert("Python!")
document["spreadsheet_upload"].bind("onchange", main)
