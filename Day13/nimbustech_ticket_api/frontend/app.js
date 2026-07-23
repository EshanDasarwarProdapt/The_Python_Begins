const API_BASE_URL = "http://127.0.0.1:8000";

const elements = {
  ticketList: document.querySelector("#ticket-list"),
  table: document.querySelector("#tickets-table"),
  emptyState: document.querySelector("#empty-state"),
  message: document.querySelector("#message"),
  breachedToggle: document.querySelector("#breached-toggle"),
  form: document.querySelector("#ticket-form"),
  total: document.querySelector("#total-count"),
  valid: document.querySelector("#valid-count"),
  breached: document.querySelector("#breached-count"),
};

function showMessage(message, isError = true) {
  elements.message.textContent = message;
  elements.message.classList.toggle("success", !isError);
}

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (!response.ok) {
      throw new Error(
        `The service at ${API_BASE_URL} does not provide ${path} `
        + `(${response.status}). Start the NimbusTech API from this project.`,
      );
    }
    return response.status === 204 ? null : response.json();
  } catch (error) {
    const message = error instanceof TypeError
      ? `Could not reach the ticket API at ${API_BASE_URL}. Is Uvicorn running?`
      : error.message;
    showMessage(message);
    throw error;
  }
}

function renderTickets(tickets) {
  elements.ticketList.replaceChildren();
  elements.table.hidden = tickets.length === 0;
  elements.emptyState.hidden = tickets.length !== 0;

  tickets.forEach((ticket) => {
    const row = document.createElement("tr");
    row.classList.toggle("breached", ticket.sla_breached);
    row.innerHTML = `
      <td>${ticket.ticket_id}</td><td>${ticket.customer_name}</td><td>${ticket.category}</td>
      <td>${ticket.priority_raw}${ticket.sla_breached ? '<span class="badge">SLA breached</span>' : ""}</td>
      <td><select aria-label="Status for ${ticket.ticket_id}"><option>open</option><option>in progress</option><option>closed</option></select></td>
      <td>${ticket.sla_hours}h</td><td><button class="delete" type="button">Delete</button></td>`;
    const statusSelect = row.querySelector("select");
    statusSelect.value = ticket.status;
    statusSelect.addEventListener("change", () => updateStatus(ticket.ticket_id, statusSelect.value));
    row.querySelector(".delete").addEventListener("click", () => deleteTicket(ticket.ticket_id));
    elements.ticketList.append(row);
  });
}

async function loadDashboard() {
  const path = elements.breachedToggle.checked ? "/tickets/breached" : "/tickets";
  try {
    const [tickets, summary] = await Promise.all([request(path), request("/tickets/summary")]);
    elements.total.textContent = summary.total_rows;
    elements.valid.textContent = summary.valid_tickets;
    elements.breached.textContent = summary.breached_count;
    renderTickets(tickets);
  } catch (_) { /* The request helper has already shown a useful message. */ }
}

async function updateStatus(ticketId, status) {
  try {
    await request(`/tickets/${ticketId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
    showMessage("Ticket updated.", false);
    loadDashboard();
  } catch (_) { loadDashboard(); }
}

async function deleteTicket(ticketId) {
  try {
    await request(`/tickets/${ticketId}`, { method: "DELETE" });
    showMessage("Ticket deleted.", false);
    loadDashboard();
  } catch (_) { /* The request helper has already shown a useful message. */ }
}

document.querySelector("#new-ticket-button").addEventListener("click", () => {
  elements.form.hidden = !elements.form.hidden;
});
elements.breachedToggle.addEventListener("change", loadDashboard);
elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(elements.form));
  values.sla_hours = Number(values.sla_hours);
  try {
    await request("/tickets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
    elements.form.reset();
    elements.form.hidden = true;
    showMessage("Ticket created.", false);
    loadDashboard();
  } catch (_) { /* The request helper has already shown a useful message. */ }
});

loadDashboard();
