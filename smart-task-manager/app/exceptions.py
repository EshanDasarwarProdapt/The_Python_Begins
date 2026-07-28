"""
Custom application exceptions.

Single responsibility of this file: define our own exception types so
that the CRUD/router layers can raise a clear, meaningful error
(e.g. "TaskNotFoundException") instead of scattering raw
`HTTPException(status_code=404, ...)` calls everywhere. main.py then
registers a single `@app.exception_handler` that knows how to turn
this exception into a clean JSON response - see main.py for that
"translation" step.

This is a common industry pattern: keep domain-level errors separate
from the HTTP-response details.
"""


class TaskNotFoundException(Exception):
    """Raised whenever code looks up a task by id and doesn't find one."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with id {task_id} not found")
