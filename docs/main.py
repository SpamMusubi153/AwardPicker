
# from dataclass import dataclass
import json
import string

from datetime import datetime

from browser import document, window
from browser.local_storage import storage

# Variables to store results
# Storage Format = {
#                   Specialist Name : [List of Records],
# 
#                  }
sorted_by_specialist = {}
storage["sorted_by_specialist"] = "{}"
storage["sorted_by_specialist_chart_created"] = "False"

# Storage Format = {
#                   Class Name : [List of Records],
#                  }
sorted_by_class = {}
storage["sorted_by_class"] = "{}"
storage["sorted_by_class_chart_created"] = "False"

storage["current_app_month"] = str(0)
storage["current_app_year"] = str(0)

storage["number_of_classes"] = str(0)


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
    year : int
    day : int
    specialist : string
    class_name : string

    def __init__(self, month:int, year:int, day:int, specialist:string, class_name:string):
        self.month = month
        self.year = year
        self.day = day
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

                    # Save the most recent year and month to display it in the first generated graphs. 
                    current_year = current_date.year
                    current_month = current_date.month
                    # If the current year is the newest year, save the year, and indicate that the month needs to be updated too.
                    if current_year > int(storage["current_app_year"]):
                        storage["current_app_year"] = str(current_year)
                        storage["current_app_month"] = str(0)

                    if current_month > int(storage["current_app_month"]):
                        storage["current_app_month"] = str(current_month)

                elif j == 1:
                    current_specialist = column

                else:
                    if column == "":
                        continue

                    # Remove any extraneous spaces.
                    column.replace(" ", "")
                    
                    current_record = Record(current_date.month, current_date.year, current_date.day, current_specialist, column)
                    add_result(current_record)

                    # Keep track of the number of classes in the data.
                    storage["number_of_classes"] = str(int(storage["number_of_classes"]) + 1)

    storage["sorted_by_specialist"] = json.dumps(sorted_by_specialist)
    storage["sorted_by_class"] = json.dumps(sorted_by_class)

    display_results()


def display_results(event=None):

    sorted_by_specialist = storage["sorted_by_specialist"]
    sorted_by_specialist = json.dumps(sorted_by_specialist)
    sorted_by_class = storage["sorted_by_class"]
    sorted_by_class = json.dumps(sorted_by_class)

    # Graph the results by class
    bar_labels = list(sorted_by_class.keys())

    # Create a list of data for the currently selected month
    current_data = []
    for key in bar_labels:
        current_key_data = sorted_by_class[key]

        for record in current_key_data:
            if record.month == int(storage["current_app_month"]) and record.year == int(storage["current_app_year"]):
                continue
            else:
                current_key_data.remove(record)
        current_data.append(current_key_data)


    # Tally the data for the current month
    bar_data = [len(current_records_list) for current_records_list in current_data]

    bar_metric_name = "Number of 4-Star or 5-Star Days in Specialists"

    month = datetime(int(storage['current_app_year']), int(storage['current_app_month']), 1).strftime("%B")

    document["currentMonth"].textContent = f"{month}, {storage['current_app_year']}"

    SORTED_BY_SPECIALIST_CHART_ID = "byClassChart"

    # If the chart was not previously created, create it now
    if storage["sorted_by_specialist_chart_created"] == "False":
        create_bar_chart(SORTED_BY_SPECIALIST_CHART_ID, bar_labels, bar_data, bar_metric_name)
        storage["sorted_by_specialist_chart_created"] = "True"
    
    # Otherwise, update the already created chart.
    else:
        chart = window.Chart.getChart(SORTED_BY_SPECIALIST_CHART_ID)
        chart.destroy()

        create_bar_chart(SORTED_BY_SPECIALIST_CHART_ID, bar_labels, bar_data, bar_metric_name)
        # chart.data.datasets[0] = bar_data
        # chart.update()



def previous_month_handler(event=None):
    if int(storage["current_app_month"]) == 1:
        storage["current_app_month"] = "12"
        storage["current_app_year"] = str(int(storage["current_app_year"]) - 1)

    else:
        storage["current_app_month"] = str(int(storage["current_app_month"]) - 1)

    display_results()

document["previousMonthButton"].bind("click", previous_month_handler)

def next_month_handler(event=None):
    if int(storage["current_app_month"]) == 12:
        storage["current_app_month"] = "1"
        storage["current_app_year"] = str(int(storage["current_app_year"]) + 1)

    else:
        storage["current_app_month"] = str(int(storage["current_app_month"]) + 1)

    display_results()

document["nextMonthButton"].bind("click", next_month_handler)