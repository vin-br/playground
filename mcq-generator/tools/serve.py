"""Serve quiz files locally via Docker + nginx."""
import argparse
import glob
import json
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
    
    # Copy server/index.html to the base directory if it exists
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_index = os.path.join(script_dir, "server", "index.html")
    output_index = os.path.join(abs_base, "index.html")
    
    if os.path.exists(server_index):
        shutil.copy(server_index, output_index)
        print(f"Copied {server_index} → {output_index}")
    
    # Generate files.json listing all .html files (excluding index.html)
    html_files = sorted(glob.glob(os.path.join(abs_base, "*.html")))
    files_list = [os.path.basename(f) for f in html_files if os.path.basename(f) != "index.html"]
    
    files_json_path = os.path.join(abs_base, "files.json")
    with open(files_json_path, "w") as f:
        json.dump(files_list, f, indent=2)
    print(f"Generated {files_json_path} with {len(files_list)} file(s)")

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
            "docker", "run", "-d" ,"--rm",
            "-p", f"{port}:80",
            "-v", f"{abs_base}:/usr/share/nginx/html:ro",
            "nginx:alpine",
        ])
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Serve quiz files locally via Docker + nginx"
    )
    parser.add_argument(
        "base",
        nargs="?",
        default="output",
        help="directory to serve (default: output)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="port to serve on (default: 8080)",
    )
    args = parser.parse_args()
    cmd_serve(args.base, args.port)
