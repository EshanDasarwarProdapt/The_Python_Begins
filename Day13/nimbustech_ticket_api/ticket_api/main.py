"""FastAPI application for the NimbusTech ticket dashboard."""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ticket_api import crud
from ticket_api.database import engine, get_db
from ticket_api.models import TicketCreate, TicketUpdate
from ticket_api.orm import Ticket


app = FastAPI(title="NimbusTech Ticket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create all database tables on application startup."""
    Ticket.metadata.create_all(bind=engine)


@app.get("/")
def health_check() -> dict:
    """Return a basic API status payload."""
    return {"message": "NimbusTech Ticket API is running", "status": "ok"}


@app.get("/tickets")
def list_tickets(db: Session = Depends(get_db)) -> list[dict]:
    """Return every ticket."""
    return [t.to_dict() for t in crud.get_all_tickets(db)]


@app.get("/tickets/breached")
def list_breached_tickets(db: Session = Depends(get_db)) -> list[dict]:
    """Return tickets whose SLA is breached."""
    return [t.to_dict() for t in crud.get_breached_tickets(db)]


@app.get("/tickets/summary")
def ticket_summary(db: Session = Depends(get_db)) -> dict:
    """Return the dashboard summary."""
    return crud.get_summary(db)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)) -> dict:
    """Return one ticket or raise a 404 error."""
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()


@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)) -> dict:
    """Create and return a ticket."""
    return crud.create_ticket(db, ticket.model_dump()).to_dict()


@app.patch("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: str, changes: TicketUpdate, db: Session = Depends(get_db)
) -> dict:
    """Update a ticket's allowed fields or raise a 404 error."""
    update_data = changes.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=422, detail="Provide status or priority_raw")

    ticket = crud.update_ticket(db, ticket_id, update_data)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()


@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, db: Session = Depends(get_db)) -> dict:
    """Delete a ticket or raise a 404 error."""
    if not crud.delete_ticket(db, ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted"}
