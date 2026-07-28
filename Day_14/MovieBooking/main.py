"""FastAPI application for the Movie Ticket Booking API.

Endpoints
--------
GET    /bookings          — list all bookings
POST   /bookings          — book a seat (with validation & business-rule checks)
DELETE /bookings/{id}     — cancel a booking and restore the seat
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import BookingCreate
from store import BookingStore

app = FastAPI(title="Movie Ticket Booking API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = BookingStore()


# ── helpers ───────────────────────────────────────────────────────────────

@app.exception_handler(ValueError)
def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    """Return 400 for business-rule violations (already booked, etc.)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


# ── routes ────────────────────────────────────────────────────────────────

@app.get("/")
def health_check() -> dict:
    """Return a basic API status payload."""
    return {"message": "Movie Ticket Booking API is running", "status": "ok"}


@app.get("/bookings")
def list_bookings() -> list[dict]:
    """Return every booking."""
    return store.get_all_bookings()


@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate) -> dict:
    """Book a seat.

    Validates that:
      • All required fields are present (via Pydantic)
      • The seat is not already booked for the same showTime (business rule)
      • The show exists in inventory

    Uses a two-file atomic transaction (inventory → log) with rollback.
    """
    try:
        return store.create_booking(
            movie_name=payload.movieName,
            show_time=payload.showTime,
            seat_number=payload.seatNumber,
            customer_name=payload.customerName,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str) -> dict:
    """Cancel a booking and restore the seat to availability."""
    try:
        cancelled = store.cancel_booking(booking_id)
        return {"message": "Booking cancelled", "booking": cancelled}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── run ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)