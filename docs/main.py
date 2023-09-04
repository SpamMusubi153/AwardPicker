
# from dataclass import dataclass
import string

from datetime import datetime
# import base64
import random

from browser import document, window
from browser.local_storage import storage

# TODO: Later, configure the program to automatically load previously stored data.
# window.localStorage.clear()

# Store the month and year currently selected for display by the user
storage["current_app_month"] = str(0)
storage["current_app_year"] = str(0)

# The first graph created for each uploaded file should have its month and year automatically determined.
storage["first_graph_from_file"] = str("True")



def retrieve_file(event=None):

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
    # To stay within localstorage bounds, display an error if the file size is greater than 2MB.
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

    # Save the date the file was last modified
    date_modified = datetime.strptime(document["spreadsheet_upload"].files[0]["lastModifiedDate"].toString().split(" GMT")[0], "%a %b %d %Y %H:%M:%S")
    document["file_current_as_of_time"] = f"This data was current as of {date_modified.strftime('%B %m, %Y')}"
    
    # Create a function to handle the processing of the file after loading.
    def on_read_load(event):
        spreadsheet = event.target.result

        storage["first_graph_from_file"] = str("True")
        storage["data"] = spreadsheet
        process_file()

    # Read the file
    reader = window.FileReader.new()
    reader.readAsText(document["spreadsheet_upload"].files[0])
    reader.bind("load", on_read_load)

document["spreadsheet_upload"].bind("change", retrieve_file)


def _display_results(sorted_by_specialist, sorted_by_class):

    def search_by_month_and_year(record):
        return (record.month == int(storage["current_app_month"])) and (record.year == int(storage["current_app_year"]))

    def get_current_records_count(dictionary_to_search, search_function=search_by_month_and_year) -> list:

        keys = list(dictionary_to_search)

        current_data = []
        for key in keys:
            current_key_data = dictionary_to_search[key]
            current_class_success_count = 0

            for record in current_key_data:

                # If the record matches the current month and year, count it for the current graph
                if search_function(record):
                    current_class_success_count += 1
                else:
                    continue

            current_data.append(current_class_success_count)

        return current_data
    
    def get_current_record_count_by_specialist(list_of_specialist_names:list, dictionary_to_search:dict) -> list:

        def account_for_specialist_search(record):
            return search_by_month_and_year(record) and (record.specialist == specialist)

        current_data = []

        for specialist in list_of_specialist_names:

            current_data.append(get_current_records_count(dictionary_to_search, account_for_specialist_search))

        return current_data


    
    # Graph the results by specialist
    SEGMENT_BY_SPECIALIST_CHART_ID = "bySpecialistChart"
    def segment_by_specialist_graph():
        bar_labels = list(sorted_by_class.keys())

        # Retrieve data for the current month
        bar_data = get_current_record_count_by_specialist(list(sorted_by_specialist.keys()), sorted_by_class)

        # The title of the current graph
        bar_metric_names = [f"{key} 4 or 5 Star Days" for key in list(sorted_by_specialist.keys())]

        # Retrieve the full month name
        month = datetime(int(storage['current_app_year']), int(storage['current_app_month']), 1).strftime("%B")

        # If the chart already exists, update its data
        try:
            chart = window.Chart.getChart(SEGMENT_BY_SPECIALIST_CHART_ID)
            chart.data.datasets[0].data = bar_data
            chart.update()

        # Otherwise, create the chart from scratch
        except:
            create_bar_chart(SEGMENT_BY_SPECIALIST_CHART_ID, bar_labels, bar_data, bar_metric_names)

        # Update the app to display the current month and year of the chart.
        document["currentMonth"].textContent = f"{month}, {storage['current_app_year']}"


    # Graph the results by class
    SORTED_BY_CLASS_CHART_ID = "byClassChart"
    def graph_by_class():
        bar_labels = list(sorted_by_class.keys())

        # Retrieve data for the current month
        bar_data = get_current_records_count(sorted_by_class)

        # The title of the current graph
        bar_metric_name = "Number of 4 or 5-Star Days in Specialists"

        # Retrieve the full month name
        month = datetime(int(storage['current_app_year']), int(storage['current_app_month']), 1).strftime("%B")

        # If the chart already exists, update its data
        try:
            chart = window.Chart.getChart(SORTED_BY_CLASS_CHART_ID)
            chart.data.datasets[0].data = bar_data
            chart.update()

        # Otherwise, create the chart from scratch
        except:
            create_bar_chart(SORTED_BY_CLASS_CHART_ID, bar_labels, [bar_data], [bar_metric_name])

        # Update the app to display the current month and year of the chart.
        document["currentMonth"].textContent = f"{month}, {storage['current_app_year']}"

    graph_by_class()
    segment_by_specialist_graph()

# Unfortunately, dataclasses are not implemented by Brython. This may change on a future date.
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

def process_file(event=None, callback=_display_results):

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

    assert "data" in storage, "A spreadsheet file under the \"data\" key could not be found in localstorage."

    # Retrieve the file from localstorage and decode it into text.
    spreadsheet = storage["data"]
    # spreadsheet = base64.b64decode(spreadsheet).decode("utf-8")

    # A function to sort records into dictionaries organized by specialist and class name.
    def add_result(record : Record):

        # Add the record to the sorted_by_specialist dictionary.
        if record.specialist in sorted_by_specialist:
            sorted_by_specialist[record.specialist].append(record)

        # If the current specialist key does not exist, create it before appending the record.
        else:
            sorted_by_specialist[record.specialist] = []
            sorted_by_specialist[record.specialist].append(record)


        # Add the result to the sorted_by_class dictionary.
        if record.class_name in sorted_by_class:
            sorted_by_class[record.class_name].append(record)

        # If the current class name key does not exist, create it before appending the record.
        else:
            sorted_by_class[record.class_name] = []
            sorted_by_class[record.class_name].append(record)
            

    # Split the rows from the text by line.
    rows = spreadsheet.split("\n")

    # Process every row of the provided CSV File
    for i, row in enumerate(rows):

        # Remove any quotation characters that separate teacher names
        row = row.replace('"', "")
        row = row.replace('\r', "")


        # Skip over the header row
        if i == 0:
            continue

        # Retrieve the columns by splitting the CSV file by comma (,).
        columns = row.split(",")

        # If the columns contain a valid amount of data, extract its data.
        if len(columns) > 2:
            current_date = None
            current_specialist = None

            for j, column in enumerate(columns):

                # Extract the date from the first column of each row that applies to all data in the row.
                if j == 0:                
                    current_date = datetime.strptime(column, "%m/%d/%Y %H:%M:%S")

                    # If this is the first time creating a graph from the uploaded file, automatically pick the latest month and year.
                    if storage["first_graph_from_file"] == "True":

                        # Save the most recent year and month to display it in the first generated graphs. 
                        current_year = current_date.year
                        current_month = current_date.month

                        # If the current year is the newest year, save the year, and indicate that the month needs to be updated too.
                        if current_year > int(storage["current_app_year"]):
                            storage["current_app_year"] = str(current_year)
                            storage["current_app_month"] = str(0)

                        if current_month > int(storage["current_app_month"]):
                            storage["current_app_month"] = str(current_month)

                # Extract the specialist name in the second column that applies to all data in the row.
                elif j == 1:
                    current_specialist = column

                else:

                    # If the column is empty, pass over it.
                    if column == "":
                        continue

                    # Remove any extraneous spaces in the column.
                    column.replace(" ", "")

                    # Create and save a record of the 
                    current_record = Record(current_date.month, current_date.year, current_date.day, current_specialist, column)
                    add_result(current_record)

    storage["first_graph_from_file"] = "False"
    callback(sorted_by_specialist, sorted_by_class)


def create_bar_chart(canvas_id, bar_labels, bar_data:list, bar_metric_names:list):
    """Creates a bar chart in a canvas provided its id, the labels of the bars, the 
    data for the bars, and the name of the metric the bars represent."""

    ctx = document[canvas_id]

    window.Chart.new(ctx, {
        "type" : "bar",
        "data" : {
            "labels" : bar_labels,
            "datasets" : create_bar_chart_datasets(bar_data, bar_metric_names)
        },

        "options" : {
            "scales" : {
                "y" : {
                    "beginAtZero" : True
                },

                # "yAxes": {
                #     "stepSize": 1
                # }
            }
        }
    })

def create_bar_chart_datasets(bar_data:list, bar_metric_names:list):
    dataset = []

    for i in range(len(bar_data)):
        current_dataset = {}
        current_dataset["label"] = bar_metric_names[i]
        current_dataset["data"] = bar_data[i]
        current_dataset["borderWidth"] = 1
        current_dataset["borderRadius"] = 2

        dataset.append(current_dataset)

    return dataset

def previous_month_handler(event=None):
    if int(storage["current_app_month"]) == 1:
        storage["current_app_month"] = "12"
        storage["current_app_year"] = str(int(storage["current_app_year"]) - 1)

    else:
        storage["current_app_month"] = str(int(storage["current_app_month"]) - 1)

    process_file()

document["previousMonthButton"].bind("click", previous_month_handler)

def next_month_handler(event=None):
    if int(storage["current_app_month"]) == 12:
        storage["current_app_month"] = "1"
        storage["current_app_year"] = str(int(storage["current_app_year"]) + 1)

    else:
        storage["current_app_month"] = str(int(storage["current_app_month"]) + 1)

    process_file()

document["nextMonthButton"].bind("click", next_month_handler)


def select_class_handler(event=None):

    def process_data(class_names, class_count):
        all_entries = []

        for i, class_name in enumerate(class_names):

            for j in range(class_count[i]):
                all_entries.append(class_name)

        return all_entries
    
    def retrieve_data():
        SEGMENT_BY_SPECIALIST_CHART_ID = "bySpecialistChart"
        chart = window.Chart.getChart(SEGMENT_BY_SPECIALIST_CHART_ID)
        class_names = chart.data.labels
        class_count = chart.data.datasets[0].data

        return class_names, class_count
        
        
    class_names, class_count = retrieve_data()
    all_entries = process_data(class_names, class_count)

    print(all_entries)

    selected_entry = all_entries[random.randint(0, len(all_entries) - 1)]

    document["selectedClass"].textContent = selected_entry


document["selectAClass"].bind("click", select_class_handler)
