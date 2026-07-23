import argparse
import logging
import sys
import datetime

from config import (
    DEFAULT_FRAUD_THRESHOLD,
    MALFORMED_THRESHOLD,
    LOG_FILE,
    LOG_FORMAT
)

from io_utils import (
    load_subscribers,
    load_cdrs,
    write_report
)

from reporting import build_report


def main():

    parser = argparse.ArgumentParser(
        description="Orbit Mobile Telecom CDR Billing CLI"
    )

    parser.add_argument(
        "--subscribers",
        required=True
    )

    parser.add_argument(
        "--cdrs",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--fraud-threshold-sec",
        type=int,
        default=DEFAULT_FRAUD_THRESHOLD
    )

    args = parser.parse_args()


    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format=LOG_FORMAT
    )


    logging.info("Billing process started")


    subscribers = load_subscribers(
        args.subscribers
    )


    cdrs, malformed_count, total_count = load_cdrs(
        args.cdrs
    )


    if total_count > 0:

        malformed_percentage = (
            malformed_count / total_count
        )

        if malformed_percentage > MALFORMED_THRESHOLD:

            logging.critical(
                "Malformed CDR rows exceeded 10%"
            )

            sys.exit(1)


    report = build_report(
        subscribers,
        cdrs,
        args.fraud_threshold_sec
    )


    write_report(
        report,
        args.output
    )


    logging.info("Billing report generated")


    print()
    print("===== Orbit Mobile Daily Summary =====")
    print()

    print(
        f"Total Subscribers : {len(subscribers)}"
    )

    print(
        f"Processed CDRs : {len(cdrs)}"
    )

    print(
        f"Malformed Rows : {malformed_count}"
    )

    print(
        f"Unknown Subscribers : {len(report['unknown_subscribers'])}"
    )

    print(
        f"Fraud Suspects : {len(report['fraud_suspects'])}"
    )

    print()

    print(
        f"Report saved : {args.output}"
    )


if __name__ == "__main__":

    print("==============================")
    print("Orbit Mobile Billing CLI")
    print(
        f"Date : {datetime.date.today()}"
    )
    print("==============================")

    main()
