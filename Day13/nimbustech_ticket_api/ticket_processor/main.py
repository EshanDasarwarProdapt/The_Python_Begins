import argparse
import logging
import sys

from ticket_processor.processor import (
    build_summary,
    check_abort_condition,
    load_csv,
    process_tickets,
    save_report,
)


def setup_logging() -> None:
    """
    Configure application logging.

    Parameters:
        None.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters:
        None.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="NimbusTech ticket processing tool",
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw ticket CSV file",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path for generated JSON report",
    )

    return parser.parse_args()


def main() -> None:
    """
    Execute ticket processing workflow.

    Parameters:
        None.

    Returns:
        None.
    """
    setup_logging()

    logger = logging.getLogger(__name__)

    args = parse_arguments()

    logger.info("Ticket processing started")

    try:
        rows = load_csv(args.input)

        logger.info(
            "Rows loaded: %s",
            len(rows),
        )

        tickets, invalid_rows = process_tickets(rows)

        logger.info(
            "Invalid rows found: %s",
            len(invalid_rows),
        )

        if check_abort_condition(
            len(rows),
            invalid_rows,
        ):
            logger.error(
                "Abort triggered. Invalid row ratio exceeds allowed limit.",
            )
            sys.exit(1)

        summary = build_summary(
            len(rows),
            tickets,
            invalid_rows,
        )

        save_report(
            args.output,
            tickets,
            invalid_rows,
            summary,
        )

        logger.info(
            "Report successfully written: %s",
            args.output,
        )

    except FileNotFoundError as error:
        logger.error(error)
        sys.exit(1)

    except ValueError as error:
        logger.error(error)
        sys.exit(1)

    except Exception:
        logger.exception(
            "Unexpected error occurred during processing",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
