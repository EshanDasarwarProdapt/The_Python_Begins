"""FastAPI application for the NimbusTech ticket dashboard."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ticket_api.models import TicketCreate, TicketUpdate
from ticket_api.store import TicketStore


app = FastAPI(title="NimbusTech Ticket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = TicketStore()


@app.get("/")
def health_check() -> dict:
    """Return a basic API status payload."""
    return {"message": "NimbusTech Ticket API is running", "status": "ok"}


@app.get("/tickets")
def list_tickets() -> list[dict]:
    """Return every ticket."""
    return store.get_all()


@app.get("/tickets/breached")
def list_breached_tickets() -> list[dict]:
    """Return tickets whose SLA is breached."""
    return store.get_breached()


@app.get("/tickets/summary")
def ticket_summary() -> dict:
    """Return the dashboard summary."""
    return store.summary()


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict:
    """Return one ticket or raise a 404 error."""
    ticket = store.get_by_id(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate) -> dict:
    """Create and return a ticket."""
    return store.create(ticket.model_dump())


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, changes: TicketUpdate) -> dict:
    """Update a ticket's allowed fields or raise a 404 error."""
    update_data = changes.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=422, detail="Provide status or priority_raw")

    ticket = store.update(ticket_id, update_data)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: str) -> dict:
    """Delete a ticket or raise a 404 error."""
    if not store.delete(ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted"}
