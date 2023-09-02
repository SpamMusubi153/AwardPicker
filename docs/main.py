
# from dataclass import dataclass
import string
import base64
import csv

from datetime import datetime

from browser import document, window, alert
# from browser.local_storage import storage

# Read the spreadsheet file from localstorage.

SPREADSHEET_LOCALSTORAGE_KEY = "spreadsheet"

def retrieve_spreadsheet(event):

    def display_file_error(message=None, remedy=None):
        document["file_error_dialog"].style.display = "block"
        document["file_success"].style.display = "none"
        document["upload_label"].textContent = "Upload a spreadsheet:"

        if message is not None:
            document["file_error_message"].textContent = message

        if remedy is not None:
            document["file_error_remedy"].textContent = remedy

    filesize = document["spreadsheet_upload"].files[0].size

    # Validate the file
    # For performance, if the file is greater than 3MB, display an error and request a smaller file.
    if filesize > 2000000:
        display_file_error("Unfortunately, this file is too big!", "Please try making a copy of the file in Excel that only contains data from the most recent month.")
        return
    
    if not (document["spreadsheet_upload"].files[0].type == "text/csv"):
        display_file_error("Unfortunately, the file you uploaded wasn't a CSV.", "Try opening your file in Excel and exporting it as a CSV (Comma Separated Values) file.")
        return
    

    # By this point, the file should have passed all tests.
    document["file_error_dialog"].style.display = "none"
    document["file_success"].style.display = "block"
    document["upload_label"].textContent = "Upload another spreadsheet:"
    
    # Create a function to handle the processing of the file after loading.
    def on_read_load(event):
        spreadsheet = event.target.result
        
        main(spreadsheet)

    # Read the file
    reader = window.FileReader.new()
    reader.readAsText(document["spreadsheet_upload"].files[0])
    reader.bind("load", on_read_load)



document["spreadsheet_upload"].bind("change", retrieve_spreadsheet)


def main(spreadsheet):

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

    # @dataclass
    class Record:
        month : int
        specialist : string
        class_name : string

        def __init__(self, month:int, specialist:string, class_name:string):
            self.month = month
            self.specialist = specialist
            self.class_name = class_name


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

    def get_spreadsheet_reader(spreadsheet):
        reader = csv.reader(spreadsheet, delimiter=',', quotechar='"')
        return reader
    
    reader = get_spreadsheet_reader(spreadsheet)

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
