#!/usr/bin/env python3
"""Serve quiz files locally via Docker + nginx."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile

PORT = 8080
ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(ROOT, "server")
OUTPUT_DIR = os.path.join(ROOT, "output")

NGINX_CONF = """\
server {
    listen 80;
    server_name localhost;
    root /srv/server;

    location = / {
        try_files /index.html =404;
    }

    location = /files.json {
        alias /srv/server/files.json;
        default_type application/json;
    }

    location /output/ {
        alias /srv/output/;
        try_files $uri =404;
    }
}
"""


def build_files_json(output_dir: str, dest: str) -> None:
    """Write a JSON array of HTML filenames found in output/ into server/."""
    files = sorted(
        f for f in os.listdir(output_dir)
        if f.endswith(".html")
    ) if os.path.isdir(output_dir) else []
    with open(dest, "w") as fh:
        json.dump(files, fh)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT

    if not shutil.which("docker"):
        print("Error: Docker is not installed or not in PATH.")
        sys.exit(1)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    # Generate files.json so the index page can list quizzes
    files_json_path = os.path.join(SERVER_DIR, "files.json")
    build_files_json(OUTPUT_DIR, files_json_path)

    print(f"Index:  {SERVER_DIR}/index.html")
    print(f"Quizzes: {OUTPUT_DIR}/")
    print(f"  Local:  http://localhost:{port}")
    print(f"  LAN:    http://{local_ip}:{port}")
    print("Press Ctrl+C to stop.")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(NGINX_CONF)
        conf_path = f.name

    try:
        subprocess.run([
            "docker", "run", "--rm",
            "-p", f"{port}:80",
            "-v", f"{SERVER_DIR}:/srv/server:ro",
            "-v", f"{OUTPUT_DIR}:/srv/output:ro",
            "-v", f"{conf_path}:/etc/nginx/conf.d/default.conf:ro",
            "nginx:alpine",
        ])
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        os.unlink(conf_path)
        if os.path.exists(files_json_path):
            os.unlink(files_json_path)


if __name__ == "__main__":
    main()
