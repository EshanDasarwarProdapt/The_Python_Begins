import json
import csv
import logging

from models import Subscriber


def load_subscribers(json_path):
    with open(json_path, "r") as file:
        data = json.load(file)

    subscribers = {}

    for item in data:
        subscriber = Subscriber(
            item["msisdn"],
            item["plan_type"]
        )

        subscribers[item["msisdn"]] = subscriber

    return subscribers


def parse_cdr_line(row):
    required_fields = [
        "msisdn",
        "call_type",
        "duration_sec"
    ]

    for field in required_fields:
        if field not in row or row[field] == "":
            raise ValueError(f"Missing field: {field}")

    try:
        duration = int(row["duration_sec"])
    except ValueError:
        raise ValueError(
            f"Invalid duration: {row['duration_sec']}"
        )

    return {
        "msisdn": row["msisdn"],
        "call_type": row["call_type"],
        "duration_sec": duration
    }


def load_cdrs(csv_path):

    cdrs = []
    malformed_count = 0
    total_count = 0

    with open(csv_path, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:
            total_count += 1

            try:
                cdr = parse_cdr_line(row)
                cdrs.append(cdr)

            except ValueError as error:
                logging.warning(str(error))
                malformed_count += 1

    return cdrs, malformed_count, total_count


def write_report(report, output_path):

    with open(output_path, "w") as file:
        json.dump(
            report,
            file,
            indent=2
        )
