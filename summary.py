# == summary.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to make a summary of monitor.csv
"""
import sys
from datetime import datetime
from pathlib import Path
from dateutil import parser

DEBUG = len(sys.argv) == 2 and sys.argv[1].lower() == 'debug'

INPUT = Path("monitor.csv")

# indexes to splitted monitor.csv items
DT = 0   # datetime
LON = 1  # longitude
LAT = 2  # latitude
ENGINEON = 3  # engineOn
V12 = 4  # 12V%
ODO = 5  # odometer
SOC = 6  # SOC%
CHARGING = 7  # charging
PLUGGED = 8  # plugged


def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(line)


def same_year(d_1: datetime, d_2: datetime):
    """ return if same year """
    return d_1.year == d_2.year


def same_month(d_1: datetime, d_2: datetime):
    """ return if same month """
    if d_1.month != d_2.month:
        return False
    return d_1.year == d_2.year


def same_week(d_1: datetime, d_2: datetime):
    """ return if same week """
    if d_1.isocalendar().week != d_2.isocalendar().week:
        return False
    return d_1.year == d_2.year


def same_day(d_1: datetime, d_2: datetime):
    """ return if same day """
    if d_1.day != d_2.day:
        return False
    if d_1.month != d_2.month:
        return False
    return d_1.year == d_2.year


def compute_deltas(prefix, current, first):
    """ compute_deltas """
    debug("compute_deltas")
    debug("PREV: " + str(first))
    debug("CURR: " + str(current))
    delta_odo = round(current[1] - first[1], 1)
    charged = first[2]
    discharged = first[3]
    if charged > 0 or discharged < 0 or delta_odo > 1.0:
        print(f"{prefix:17} driven: {delta_odo:5.1f} charged: {charged:+4}% discharged: {discharged:4}%")  # noqa pylint:disable=line-too-long


def init(current_day, odo):
    """ init tuple with initial charging and discharging """
    return (current_day, odo, 0, 0)


def add(values, delta_soc):
    """ add delta_soc """
    if delta_soc == 0:
        return values
    if delta_soc > 0:
        return (values[0], values[1], values[2] + delta_soc, values[3])
    return (values[0], values[1], values[2], values[3] + delta_soc)


def handle_line(  # pylint: disable=too-many-arguments
    line, prev_line, first_d, first_w, first_m, first_y
):
    """ handle_line """
    split = line.split(',')
    current_day = parser.parse(split[DT])
    odo = float(split[ODO].strip())
    soc = int(split[SOC].strip())

    current_day_values = init(current_day, odo)
    if not first_d:
        return (
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values
        )

    # take into account delta SOC per line
    split2 = prev_line.split(',')
    soc2 = int(split2[SOC].strip())
    delta_soc = soc - soc2
    if delta_soc != 0:
        debug("Delta SOC: " + str(delta_soc))
        first_d = add(first_d, delta_soc)
        first_w = add(first_w, delta_soc)
        first_m = add(first_m, delta_soc)
        first_y = add(first_y, delta_soc)

    if not same_day(current_day, first_d[0]):
        compute_deltas(
            "DAY   " + first_d[0].strftime("%Y-%m-%d"),
            current_day_values,
            first_d
        )
        first_d = init(current_day, odo)
        if not same_week(current_day, first_w[0]):
            compute_deltas(
                "WEEK  " + str(first_y[0].year) + " W" +
                str(first_w[0].isocalendar().week),
                current_day_values,
                first_w
            )
            first_w = first_d
        if not same_month(current_day, first_m[0]):
            compute_deltas(
                "MONTH " + first_m[0].strftime("%Y-%m"),
                current_day_values,
                first_m
            )
            first_m = first_d
        if not same_year(current_day, first_y[0]):
            compute_deltas(
                "YEAR  " + str(first_y[0].year),
                current_day_values,
                first_y
            )
            first_y = first_d

    return (first_d, first_w, first_m, first_y)


def summary():
    """ summary of monitor.csv file """

    with INPUT.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        prev_index = -1
        prev_line = ''
        first_day = ()
        first_week = ()
        first_month = ()
        first_year = ()
        for line in inputfile:
            line = line.strip()
            linecount += 1
            debug(str(linecount) + ': LINE=[' + line + ']')
            index = line.find(',')
            if index < 0 or prev_index < 0 or index != prev_index or \
                    prev_line[prev_index:] != line[index:]:
                if prev_index >= 0:
                    (first_day, first_week, first_month, first_year) = \
                        handle_line(
                        line,
                        prev_line,
                        first_day,
                        first_week,
                        first_month,
                        first_year
                    )

            prev_index = index
            prev_line = line

        # also compute last last day/week/month
        temp_line = "2999" + prev_line[4:]
        debug("Handling last values")
        handle_line(
            temp_line,
            prev_line,
            first_day,
            first_week,
            first_month,
            first_year
        )


summary()  # do the work