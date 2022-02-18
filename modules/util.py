import os
import csv

# -*- coding: utf-8 -*-
# General purpose helper code

# Define a progressbar
# This function has been shamelessly borrowed from the forum posting cited below -- many thanks to its author.
# @see https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 80, fill = '#', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)    
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def date_ranges_from_file(file):
    # verify the file is readable
    if not os.access(file, os.R_OK):
        raise RuntimeError("Unable to read dates from file ", file)

    dates = []
    with open(file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            # Single timestamp per line
            if len(row) == 1:
                dates.append({'begin': row[0].strip(), 'end': row[0].strip(), 'interval': '1s'})
            # Date range per line
            if len(row) == 3:
                dates.append({'begin': row[0].strip(), 'end': row[1].strip(), 'interval': row[2].strip()})
    return dates
