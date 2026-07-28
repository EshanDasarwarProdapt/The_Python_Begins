"""Pydantic models for the Movie Ticket Booking API."""

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    """Validate the data accepted when creating a booking."""

    movieName: str = Field(min_length=1)
    showTime: str = Field(min_length=1)
    seatNumber: int = Field(gt=0)
    customerName: str = Field(min_length=1)


class BookingCancel(BaseModel):
    """No body needed for cancellation — ID is in the URL path."""