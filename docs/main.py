
# from dataclass import dataclass
import string

from datetime import datetime

from browser import document, window

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
        
        process_csv_file(spreadsheet)

    # Read the file
    reader = window.FileReader.new()
    reader.readAsText(document["spreadsheet_upload"].files[0])
    reader.bind("load", on_read_load)



document["spreadsheet_upload"].bind("change", retrieve_spreadsheet)


# @dataclass
class Record:
    month : int
    specialist : string
    class_name : string

    def __init__(self, month:int, specialist:string, class_name:string):
        self.month = month
        self.specialist = specialist
        self.class_name = class_name

def create_bar_chart(canvas_id, bar_labels, bar_data, bar_metric_name):
    """Creates a bar chart in a canvas provided its id, the labels of the bars, the 
    data for the bars, and the name of the metric the bars represent."""

    ctx = document[canvas_id]

    window.Chart.new(ctx, {
        "type" : "bar",
        "data" : {
            "labels" : bar_labels,
            "datasets" : [{
                "label" : bar_metric_name,
                "data" : bar_data,
                "borderWidth" : 1,
                "borderRadius" : 2
            }]
        },

        "options" : {
            "scales" : {
                "y" : {
                    "beginAtZero" : True
                }
            }
        }
    })


        

def process_csv_file(spreadsheet):

    def add_result(record : Record):

        # Add the result to the sorted_by_specialist dictionary.
        if record.specialist in sorted_by_specialist.keys():
            sorted_by_specialist[record.specialist].append(record)

        # If the current specialist key does not exist, create it now.
        else:
            sorted_by_specialist[record.specialist] = []
            sorted_by_specialist[record.specialist].append(record)



        # Then, add the result to the sorted_by_class dictionary.
        if record.class_name in sorted_by_class.keys():
            sorted_by_class[record.class_name].append(record)

        # If necessary, create the class name key list.
        else:
            sorted_by_class[record.class_name] = []
            sorted_by_class[record.class_name].append(record)
            

    rows = spreadsheet.split("\n")

    for i, row in enumerate(rows):

        # Remove any quotation characters that separate teacher names
        row = row.replace('"', "")
        row = row.replace('\r', "")


        # Skip over the header row
        if i == 0:
            continue

        columns = row.split(",")
        if len(columns) > 1:
            current_date = None
            current_specialist = None

            for j, column in enumerate(columns):

                # Extract the date from the first column of each row.
                if j == 0:                
                    current_date = datetime.strptime(column, "%m/%d/%Y %H:%M:%S")

                elif j == 1:
                    current_specialist = column

                else:
                    if column == "":
                        continue

                    # Remove any extraneous spaces.
                    column.replace(" ", "")
                    
                    current_record = Record(current_date.month, current_specialist, column)
                    add_result(current_record)
                    
    display_results()


def display_results(event=None)

    # Graph the results by class
    bar_labels = list(sorted_by_class.keys())
    bar_data = [len(sorted_by_class[key]) for key in bar_labels]
    bar_metric_name = "Number of 4-Star or 5-Star Days in Specialists"

    print(bar_labels)
    print(bar_data)
    print(bar_metric_name)

    create_bar_chart("byClassChart", bar_labels, bar_data, bar_metric_name)
    
