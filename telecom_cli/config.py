RATES = {
    "domestic": 1.5,
    "roaming": 8.0,
    "international": 12.0
}

DEFAULT_FRAUD_THRESHOLD = 3600

MALFORMED_THRESHOLD = 0.10

LOG_FILE = "telecom.log"

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"

REPORT_FILE = "report.json"

VALID_CALL_TYPES = [
    "domestic",
    "roaming",
    "international"
]

ROUND_DIGITS = 2
