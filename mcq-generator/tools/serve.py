"""Serve quiz files locally via Docker + nginx."""
import os
import shutil
import socket
import subprocess
import sys


def cmd_serve(base: str, port: int = 8080) -> None:
    if not shutil.which("docker"):
        print("Error: Docker is not installed or not in PATH.")
        sys.exit(1)

    abs_base = os.path.abspath(base)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    print(f"Serving {abs_base}")
    print(f"  Local:  http://localhost:{port}")
    print(f"  LAN:    http://{local_ip}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        subprocess.run([
            "docker", "run", "--rm",
            "-p", f"{port}:80",
            "-v", f"{abs_base}:/usr/share/nginx/html:ro",
            "nginx:alpine",
        ])
    except KeyboardInterrupt:
        print("\nStopped.")
