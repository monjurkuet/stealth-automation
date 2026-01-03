#!/usr/bin/env python3
import socket
import sys
from typing import Optional


def send_trigger(platform: str, query: str):
    """Send automation trigger to native host."""
    HOST = "127.0.0.1"
    PORT = 9999

    message = f"start_task:{query}:{platform}"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode())
            data = s.recv(1024)

        print(f"Sent: Platform='{platform}', Query='{query}'")
        print(f"Response: {data.decode()}")

    except ConnectionRefusedError:
        print("Error: Could not connect to Stealth Automation.")
        print("Make sure Chrome is open and extension is loaded.")
    except Exception as e:
        print(f"Error: {e}")


def list_platforms():
    """List available platforms."""
    HOST = "127.0.0.1"
    PORT = 9999
    message = "list_platforms::"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode())
            data = s.recv(4096)

        print("Available platforms:")
        print(data.decode())
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trigger.py list                    # List available platforms")
        print("  python trigger.py <platform> <query>      # Run automation")
        print("")
        print("Examples:")
        print('  python trigger.py duckduckgo "stealth automation"')
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_platforms()
    else:
        platform = sys.argv[1]
        if len(sys.argv) < 3:
            print(f'Error: Query required for platform "{platform}"')
            print(f'Usage: python trigger.py {platform} "your search query"')
            sys.exit(1)

        query = " ".join(sys.argv[2:])
        send_trigger(platform, query)
