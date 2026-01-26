#!/usr/bin/env python3
import sys

import requests


def send_trigger(platform: str, query: str):
    """Send automation trigger to native host."""
    URL = "http://127.0.0.1:9427/execute"

    payload = {"action": "start_task", "platform": platform, "query": query}

    try:
        response = requests.post(URL, json=payload, timeout=180)
        response.raise_for_status()

        print(f"Sent: Platform='{platform}', Query='{query}'")
        print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Stealth Automation.")
        print("Make sure the server is running.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def list_platforms():
    """List available platforms."""
    URL = "http://127.0.0.1:9427/list_platforms"

    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()

        print("Available platforms:")
        print(response.text)
    except requests.exceptions.RequestException as e:
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
