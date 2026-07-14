#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import atexit
import os
import subprocess
import sys
from pathlib import Path


def _start_signaling_server():
    """Launch the Socket.IO signaling server alongside Django runserver."""
    if os.environ.get("NEO_CALL_SIGNALING_STARTED") == "1":
        return None

    project_dir = Path(__file__).resolve().parent
    server_script = project_dir / "home" / "server.py"

    if not server_script.exists():
        return None

    env = os.environ.copy()
    env["NEO_CALL_SIGNALING_STARTED"] = "1"

    process = subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=str(project_dir),
        env=env,
    )
    print("Starting signaling server...")
    return process


def _stop_signaling_server(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratic_django.settings')

    if len(sys.argv) > 1 and sys.argv[1].startswith("runserver"):
        signaling_process = _start_signaling_server()
        if signaling_process:
            atexit.register(_stop_signaling_server, signaling_process)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
