"""Two-file transaction-backed booking store.

Uses the same transaction / rollback pattern as the classic bookstore order flow:
  • seats-inventory.json  — tracks available seats per movie+showTime
  • bookings-log.json     — append-only log of confirmed bookings

Every booking decrements inventory first, then appends to the log.
If the log append fails, the inventory change is rolled back.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4


DATA_DIR = Path(__file__).resolve().parent / "data"
INVENTORY_PATH = DATA_DIR / "seats-inventory.json"
BOOKINGS_PATH = DATA_DIR / "bookings-log.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _composite_key(movie: str, show: str) -> str:
    """Return a deterministic key for a movie+show combination."""
    return f"{movie}__{show}"


def _read_json(path: Path) -> Any:
    """Read a JSON file, returning its parsed content."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_json_atomic(path: Path, data: Any) -> None:
    """Atomically write *data* to *path* via a temp-file + rename."""
    fd, tmp_path_str = tempfile.mkstemp(
        dir=str(path.parent),
        suffix=".tmp",
    )
    with open(fd, "w", encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
    shutil.move(tmp_path_str, str(path))


# ---------------------------------------------------------------------------
# store
# ---------------------------------------------------------------------------

class BookingStore:
    """Persistence layer for movie bookings."""

    # ── listing ──────────────────────────────────────────────────────────

    def get_all_bookings(self) -> list[dict]:
        """Return every booking in the log."""
        return list(_read_json(BOOKINGS_PATH))

    def get_inventory(self) -> dict[str, dict]:
        """Return the full inventory keyed by composite key."""
        return _read_json(INVENTORY_PATH)

    # ── booking (create) ─────────────────────────────────────────────────

    def create_booking(self, movie_name: str, show_time: str,
                       seat_number: int, customer_name: str) -> dict:
        """Book a seat with a two-file atomic transaction.

        Raises
        ------
        ValueError
            If the seat is already taken or the show does not exist.
        RuntimeError
            If the transaction fails and requires a rollback.
        """
        key = _composite_key(movie_name, show_time)

        # ---- phase 1: verify & decrement inventory ----
        inventory = _read_json(INVENTORY_PATH)
        show = inventory.get(key)
        if show is None:
            raise ValueError(f"Show not found: '{movie_name}' at '{show_time}'")

        if seat_number not in show["availableSeats"]:
            raise ValueError(
                f"Seat {seat_number} is already booked for "
                f"'{movie_name}' at '{show_time}'"
            )

        # Take the seat out of inventory.
        show["availableSeats"].remove(seat_number)
        inventory[key] = show

        booking_id = f"BK-{uuid4().hex[:8].upper()}"
        booking = {
            "id": booking_id,
            "movieName": movie_name,
            "showTime": show_time,
            "seatNumber": seat_number,
            "customerName": customer_name,
        }

        # ---- phase 2: write inventory first ----
        try:
            _write_json_atomic(INVENTORY_PATH, inventory)
        except OSError as exc:
            raise RuntimeError(
                f"Failed to update inventory: {exc}"
            ) from exc

        # ---- phase 3: append to bookings log ----
        try:
            bookings = _read_json(BOOKINGS_PATH)
            bookings.append(booking)
            _write_json_atomic(BOOKINGS_PATH, bookings)
        except (OSError, json.JSONDecodeError) as exc:
            # ROLLBACK — restore the seat in inventory
            rollback_inv = _read_json(INVENTORY_PATH)
            rollback_inv[key]["availableSeats"].append(seat_number)
            rollback_inv[key]["availableSeats"].sort()
            try:
                _write_json_atomic(INVENTORY_PATH, rollback_inv)
            except OSError:
                raise RuntimeError(
                    "CRITICAL: inventory decremented but booking log failed. "
                    "Manual reconciliation required. "
                    f"Affected seat: {seat_number} for '{movie_name}' at '{show_time}'."
                ) from exc
            raise RuntimeError(
                f"Booking log write failed — transaction rolled back: {exc}"
            ) from exc

        return booking

    # ── cancellation ─────────────────────────────────────────────────────

    def cancel_booking(self, booking_id: str) -> dict:
        """Cancel a booking and restore the seat to availability.

        Raises
        ------
        ValueError
            If the booking ID does not exist.
        """
        # Read both data files.
        bookings = _read_json(BOOKINGS_PATH)
        inventory = _read_json(INVENTORY_PATH)

        # Find the booking.
        booking = next((b for b in bookings if b["id"] == booking_id), None)
        if booking is None:
            raise ValueError(f"Booking not found: {booking_id}")

        # Remove from bookings list.
        bookings = [b for b in bookings if b["id"] != booking_id]

        # Restore seat in inventory.
        key = _composite_key(booking["movieName"], booking["showTime"])
        if key in inventory:
            seats = inventory[key]["availableSeats"]
            if booking["seatNumber"] not in seats:
                seats.append(booking["seatNumber"])
                seats.sort()
            inventory[key] = inventory[key]

        # Write bookings first (the "primary" record).
        try:
            _write_json_atomic(BOOKINGS_PATH, bookings)
        except OSError as exc:
            raise RuntimeError(f"Failed to update bookings log: {exc}") from exc

        # Then write inventory.
        try:
            _write_json_atomic(INVENTORY_PATH, inventory)
        except OSError as exc:
            # Rollback the bookings change.
            bookings_rollback = _read_json(BOOKINGS_PATH)
            bookings_rollback.append(booking)
            _write_json_atomic(BOOKINGS_PATH, bookings_rollback)
            raise RuntimeError(
                f"Inventory update failed — cancellation rolled back: {exc}"
            ) from exc

        return booking