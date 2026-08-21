import os
from langchain_core.tools import tool

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace'))

def _get_safe_path(filename: str) -> str:
    """Ensure the path is within the workspace directory."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    if not target_path.startswith(WORKSPACE_DIR):
        raise ValueError(f"Access to '{filename}' denied. Outside of sandbox.")
    return target_path

@tool
def list_files() -> str:
    """List all files currently in the workspace."""
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "Workspace is empty."
        return "Files in workspace:\n" + "\n".join([f"- {f}" for f in files])
    except Exception as e:
        return f"Error listing files: {e}"

@tool
def read_file(filename: str) -> str:
    """Read text content from a specified workspace file."""
    try:
        path = _get_safe_path(filename)
        if not os.path.exists(path):
            return f"File '{filename}' does not exist."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def write_file(filename: str, content: str) -> str:
    """Write text content to a specified workspace file."""
    try:
        path = _get_safe_path(filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filename}."
    except Exception as e:
        return f"Error writing file: {e}"

@tool
def delete_file(filename: str) -> str:
    """
    Delete a target file from the workspace.
    This is a destructive tool and requires human-in-the-loop confirmation before execution.
    """
    try:
        path = _get_safe_path(filename)
        if not os.path.exists(path):
            return f"File '{filename}' does not exist."
        os.remove(path)
        return f"Successfully deleted {filename}."
    except Exception as e:
        return f"Error deleting file: {e}"

file_tools = [list_files, read_file, write_file, delete_file]
