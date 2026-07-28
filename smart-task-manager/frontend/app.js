// ============================================================================
// Smart Task Manager — Frontend Logic (app.js)
//
// This file is written for students learning "JavaScript Essentials" and
// "Asynchronous JavaScript". Every function has a comment above it explaining
// WHAT it does, WHY it exists, and (for async functions) WHAT part of the
// async/await lesson it demonstrates.
//
// Big picture: this file talks to a FastAPI backend running on our own
// computer. Every time we need data from the server (or want to send data
// TO the server) we use fetch(), which returns a Promise. We use the
// "async/await" style instead of ".then()" chains because it reads like
// normal top-to-bottom code, which is easier for beginners to trace.
// ============================================================================

// This constant is the single place where our frontend "meets" the backend.
// If the backend ever moved to a different address, this is the only line
// we'd need to change.
const API_BASE_URL = "http://127.0.0.1:8000";

// ----------------------------------------------------------------------
// Grab references to the HTML elements we'll need to read from or write to.
// Doing this once at the top (instead of re-querying the DOM everywhere)
// keeps the rest of the code short and easy to read.
// ----------------------------------------------------------------------
const errorBanner = document.getElementById("error-banner");

const taskForm = document.getElementById("task-form");
const formHeading = document.getElementById("form-heading");
const titleInput = document.getElementById("task-title");
const descriptionInput = document.getElementById("task-description");
const priorityInput = document.getElementById("task-priority");
const statusInput = document.getElementById("task-status");
const deadlineInput = document.getElementById("task-deadline");
const saveBtn = document.getElementById("save-btn");
const cancelEditBtn = document.getElementById("cancel-edit-btn");

const searchInput = document.getElementById("search-input");
const filterPriority = document.getElementById("filter-priority");
const filterStatus = document.getElementById("filter-status");

const taskListEl = document.getElementById("task-list");
const emptyStateEl = document.getElementById("empty-state");

const statTotal = document.getElementById("stat-total");
const statPending = document.getElementById("stat-pending");
const statInProgress = document.getElementById("stat-in-progress");
const statCompleted = document.getElementById("stat-completed");
const statHighPriority = document.getElementById("stat-high-priority");

// This variable is the "memory" of whether we are creating a brand new task
// or editing an existing one. When it is null, the form is in "create" mode.
// When it holds a task's id, the form is in "edit" mode. Keeping this as a
// single shared variable (instead of duplicating the form) is what lets us
// reuse ONE <form> for both add and edit.
let editingTaskId = null;

// A small timer "handle" used by our search debounce logic below. We store
// it outside any function so it survives between keystrokes.
let searchDebounceTimer = null;

// ============================================================================
// ERROR HANDLING HELPERS
// ============================================================================

// Shows a friendly message in the error banner at the top of the page.
// We use this instead of alert() so the page doesn't get interrupted by a
// blocking popup every time something goes wrong.
function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
}

// Hides the error banner. We call this whenever a new action starts, so
// old error messages don't linger on screen after the problem is fixed.
function clearError() {
  errorBanner.textContent = "";
  errorBanner.classList.add("hidden");
}

// ============================================================================
// FORMATTING HELPERS (small, "pure" functions — no server calls here)
// ============================================================================

// Turns a "YYYY-MM-DD" deadline string into a friendly date like "Jul 26, 2026".
// We need this because the backend stores dates in a plain machine-friendly
// format, but humans prefer reading dates the way we normally write them.
function formatDeadline(deadlineString) {
  if (!deadlineString) {
    return "No deadline";
  }
  // Adding "T00:00:00" avoids timezone shifting the date to the previous day.
  const date = new Date(deadlineString + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// Converts a status string like "In Progress" into a CSS-friendly class
// suffix like "in-progress". This keeps our badge styling logic simple.
function statusToClassSuffix(status) {
  return status.toLowerCase().replace(/\s+/g, "-");
}

// ============================================================================
// API FUNCTIONS
// Every function below talks to the FastAPI backend using fetch().
// They are all declared as "async function" and use "await" inside so that
// the code pauses at the network call WITHOUT freezing the browser tab.
// While we wait for the server to reply, the rest of the page (animations,
// clicks, typing) keeps working perfectly fine — that is the whole point of
// asynchronous JavaScript.
// ============================================================================

// Fetches the list of tasks from the backend, using whatever search/filter
// values are currently selected on the page. This demonstrates a GET request
// with query string parameters built from user input.
//
// ASYNC LESSON: we AWAIT the fetch() call, which pauses THIS function only
// (not the whole browser) until the server responds. We also AWAIT
// response.json() because turning the raw response body into a JavaScript
// object is itself an asynchronous step.
async function fetchTasks() {
  // Read the current filter values straight from the form controls.
  const search = searchInput.value.trim();
  const priority = filterPriority.value;
  const status = filterStatus.value;

  // Build the query string, only including parameters that actually have
  // a value (the backend expects empty filters to simply be omitted).
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (priority) params.set("priority", priority);
  if (status) params.set("status", status);

  const url = `${API_BASE_URL}/tasks?${params.toString()}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to load tasks.");
    }

    const tasks = await response.json();
    renderTasks(tasks);
  } catch (error) {
    showError(error.message || "Something went wrong while loading tasks.");
  }
}

// Sends a brand-new task to the backend with a POST request.
//
// ASYNC LESSON: notice there is no page reload anywhere in this function.
// We AWAIT the server's response, then use plain JavaScript to update the
// page (refresh the list, refresh the stats). This is the core idea behind
// building a "single page" experience with fetch().
async function createTask(taskData) {
  const response = await fetch(`${API_BASE_URL}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taskData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to create task.");
  }

  return response.json();
}

// Sends updated fields for an existing task with a PUT request.
//
// ASYNC LESSON: just like createTask(), we AWAIT the network call so the
// function "pauses" until the server confirms the update, then we return
// the freshly updated task object back to whoever called us.
async function updateTask(taskId, taskData) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taskData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to update task.");
  }

  return response.json();
}

// Deletes a task on the backend with a DELETE request.
//
// ASYNC LESSON: the backend returns "204 No Content" on success, which
// means there is no JSON body to read. We AWAIT the fetch() itself, but we
// deliberately skip awaiting response.json() here, because there is nothing
// to parse — trying to do so would throw an error.
async function deleteTaskOnServer(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to delete task.");
  }
}

// Fetches the summary statistics (totals by status/priority) from the
// backend and writes them into the statistics panel on the page.
//
// ASYNC LESSON: this is a good example of "fire an async function and let
// it update the page whenever the server gets back to us" — the rest of
// the script keeps running normally while we wait.
async function fetchStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks/stats`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to load statistics.");
    }

    const stats = await response.json();
    renderStats(stats);
  } catch (error) {
    showError(error.message || "Something went wrong while loading statistics.");
  }
}

// ============================================================================
// RENDERING FUNCTIONS
// These functions take data we already have (no network calls here) and
// update the HTML on the page to match. Keeping "get data" and "show data"
// separate makes the code much easier to follow.
// ============================================================================

// Writes the statistics numbers into the little boxes at the top of the page.
function renderStats(stats) {
  statTotal.textContent = stats.total;
  statPending.textContent = stats.by_status["Pending"] || 0;
  statInProgress.textContent = stats.by_status["In Progress"] || 0;
  statCompleted.textContent = stats.by_status["Completed"] || 0;
  statHighPriority.textContent = stats.by_priority["High"] || 0;
}

// Builds and inserts one task "card" into the page for every task we were
// given, or shows the "No tasks found" empty state if the list is empty.
// This function is called every time we get a fresh list of tasks from the
// server (after loading the page, searching, filtering, or editing).
function renderTasks(tasks) {
  // Clear out whatever was there before so we don't end up with duplicates.
  taskListEl.innerHTML = "";

  if (tasks.length === 0) {
    emptyStateEl.classList.remove("hidden");
    return;
  }
  emptyStateEl.classList.add("hidden");

  tasks.forEach((task) => {
    const card = document.createElement("div");
    card.className = "task-card";

    const priorityClass = `badge-priority-${task.priority.toLowerCase()}`;
    const statusClass = `badge-status-${statusToClassSuffix(task.status)}`;

    // Using textContent (set below) instead of raw string concatenation into
    // innerHTML keeps this safe from characters like <, >, or & in task
    // titles/descriptions breaking the page's HTML structure.
    card.innerHTML = `
      <h3></h3>
      <p class="task-description"></p>
      <div class="badges">
        <span class="badge ${priorityClass}">${task.priority}</span>
        <span class="badge ${statusClass}">${task.status}</span>
      </div>
      <div class="deadline">Deadline: ${formatDeadline(task.deadline)}</div>
      <div class="card-actions">
        <button type="button" class="btn btn-small btn-edit">Edit</button>
        <button type="button" class="btn btn-small btn-delete">Delete</button>
      </div>
    `;

    // Fill in the title and description as plain text (safe from HTML injection).
    card.querySelector("h3").textContent = task.title;
    card.querySelector(".task-description").textContent = task.description || "No description";

    // Wire up the Edit button to load this task into the form above.
    card.querySelector(".btn-edit").addEventListener("click", () => {
      startEditingTask(task);
    });

    // Wire up the Delete button to confirm, then delete, then refresh.
    card.querySelector(".btn-delete").addEventListener("click", () => {
      handleDeleteClick(task.id, task.title);
    });

    taskListEl.appendChild(card);
  });
}

// ============================================================================
// FORM HANDLING
// ============================================================================

// Copies a task's details into the form fields and switches the form into
// "edit" mode by remembering the task's id in editingTaskId. This is what
// lets one shared <form> serve both "Add" and "Edit" purposes.
function startEditingTask(task) {
  editingTaskId = task.id;

  titleInput.value = task.title;
  descriptionInput.value = task.description || "";
  priorityInput.value = task.priority;
  statusInput.value = task.status;
  deadlineInput.value = task.deadline || "";

  formHeading.textContent = "Edit Task";
  saveBtn.textContent = "Update";
  cancelEditBtn.classList.remove("hidden");

  // Scroll up so the student can see the form is now filled in.
  taskForm.scrollIntoView({ behavior: "smooth" });
}

// Resets the form back to blank "create a new task" mode. Used both by the
// Cancel button and automatically after a successful save.
function resetForm() {
  editingTaskId = null;
  taskForm.reset();
  formHeading.textContent = "Add a New Task";
  saveBtn.textContent = "Save Task";
  cancelEditBtn.classList.add("hidden");
}

// Runs whenever the Add/Edit form is submitted. Reads the field values,
// decides (based on editingTaskId) whether to call createTask() or
// updateTask(), and then refreshes the task list and stats.
//
// ASYNC LESSON: this is an "event handler" that is itself async. We AWAIT
// our own createTask()/updateTask() functions above, which in turn AWAIT
// fetch(). That "chain of awaiting" is normal — async/await composes nicely,
// one function pausing for another, all without blocking the browser.
async function handleFormSubmit(event) {
  // Stop the browser's default behavior of reloading the page on submit —
  // we want to handle everything ourselves with JavaScript + fetch().
  event.preventDefault();
  clearError();

  const taskData = {
    title: titleInput.value.trim(),
    description: descriptionInput.value.trim(),
    priority: priorityInput.value,
    status: statusInput.value,
    // Send null instead of an empty string when no deadline was picked.
    deadline: deadlineInput.value || null,
  };

  if (!taskData.title) {
    showError("Please enter a title for the task.");
    return;
  }

  try {
    if (editingTaskId === null) {
      // No task is being edited, so this is a brand-new task.
      await createTask(taskData);
    } else {
      // A task id is set, so we are updating that existing task.
      await updateTask(editingTaskId, taskData);
    }

    resetForm();

    // Refresh both the visible list and the statistics panel so the page
    // reflects the change immediately, without ever reloading.
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    showError(error.message || "Something went wrong while saving the task.");
  }
}

// Runs when the user clicks a task's Delete button. Confirms with the user
// first (so a stray click doesn't destroy data), then calls the backend.
//
// ASYNC LESSON: we AWAIT deleteTaskOnServer() so we only refresh the list
// AFTER the server confirms the task is really gone — this avoids showing
// a task in the list that no longer actually exists on the server.
async function handleDeleteClick(taskId, taskTitle) {
  const confirmed = confirm(`Delete the task "${taskTitle}"? This cannot be undone.`);
  if (!confirmed) {
    return;
  }

  clearError();

  try {
    await deleteTaskOnServer(taskId);
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    showError(error.message || "Something went wrong while deleting the task.");
  }
}

// ============================================================================
// SEARCH / FILTER HANDLING
// ============================================================================

// Called every time the user types in the search box. Instead of calling
// the API on every single keystroke (wasteful and can cause results to
// arrive out of order), we "debounce" it: wait until the user has paused
// typing for 300ms before actually fetching.
function handleSearchInput() {
  // Cancel any previously scheduled fetch so only the LATEST keystroke
  // actually triggers a request.
  clearTimeout(searchDebounceTimer);

  searchDebounceTimer = setTimeout(() => {
    fetchTasks();
  }, 300);
}

// Called immediately when either filter dropdown changes. Unlike search
// typing, a dropdown change is a single deliberate action, so we fetch
// right away with no debounce needed.
function handleFilterChange() {
  fetchTasks();
}

// ============================================================================
// STARTUP
// This is where everything kicks off once the page has loaded.
// ============================================================================

// Wires up all of our event listeners to the functions above.
function setupEventListeners() {
  taskForm.addEventListener("submit", handleFormSubmit);
  cancelEditBtn.addEventListener("click", resetForm);
  searchInput.addEventListener("input", handleSearchInput);
  filterPriority.addEventListener("change", handleFilterChange);
  filterStatus.addEventListener("change", handleFilterChange);
}

// The very first thing that runs. It wires up event listeners, then loads
// the initial task list and statistics from the server.
//
// ASYNC LESSON: this function AWAITS two async calls back to back. Because
// we use await (instead of firing both and hoping for the best), the code
// reads top-to-bottom just like synchronous code would, even though real
// network requests are happening in between each line.
async function init() {
  setupEventListeners();
  await fetchTasks();
  await fetchStats();
}

// Kick everything off. Since app.js is loaded with "defer", the HTML is
// already fully parsed by the time this line runs, so every element
// lookup near the top of this file (getElementById, etc.) is guaranteed
// to succeed.
init();
