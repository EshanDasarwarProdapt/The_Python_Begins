# NimbusTech Ticket Triage Dashboard

This project processes support-ticket CSV data and exposes its report through a small FastAPI service and a browser dashboard.

## Setup and run

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ticket_processor.main --input data\tickets_raw.csv --output data\tickets_report.json
uvicorn ticket_api.main:app --reload
```

Open `frontend/index.html` directly in a browser while the API is running at `http://127.0.0.1:8000`.

The supplied `tickets_raw.csv` deliberately contains four invalid rows, so the processor correctly aborts because its invalid-row ratio is over 10%. A valid `data/tickets_report.json` is included so the API and dashboard can be tested immediately. Use a cleaned CSV file when regenerating the report for normal use.

## API routes

- `GET /`, `GET /tickets`, `GET /tickets/breached`, `GET /tickets/summary`
- `GET /tickets/{ticket_id}`, `POST /tickets`
- `PATCH /tickets/{ticket_id}`, `DELETE /tickets/{ticket_id}`

Ticket changes are intentionally stored only in memory for this MVP; restarting the API reloads `data/tickets_report.json`.
