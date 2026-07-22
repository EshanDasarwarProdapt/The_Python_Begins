import json
import csv

subscribers = [
    {"msisdn": "9876543210", "plan_type": "postpaid"},
    {"msisdn": "9812345678", "plan_type": "prepaid"},
    {"msisdn": "9800011122", "plan_type": "postpaid"},
]
with open("subscribers.json", "w") as f:
    json.dump(subscribers, f, indent=2)

cdr_rows = [
    {"msisdn": "9876543210", "call_type": "domestic", "duration_sec": "180"},
    {"msisdn": "9876543210", "call_type": "international", "duration_sec": "4200"},
    {"msisdn": "9812345678", "call_type": "roaming", "duration_sec": "60"},
    {"msisdn": "9812345678", "call_type": "domestic", "duration_sec": "0"},
    {"msisdn": "9800011122", "call_type": "international", "duration_sec": "300"},
    {"msisdn": "9999999999", "call_type": "domestic", "duration_sec": "120"},   # unknown subscriber
    {"msisdn": "9800011122", "call_type": "domestic", "duration_sec": "notanumber"},  # malformed
]
with open("cdrs.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["msisdn", "call_type", "duration_sec"])
    writer.writeheader()
    writer.writerows(cdr_rows)

print("Sample data written: subscribers.json, cdrs.csv")