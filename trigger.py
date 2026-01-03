#!/usr/bin/env python3
import socket
import sys


def send_trigger(query):
    HOST = "127.0.0.1"
    PORT = 9999

    message = f"search:{query}"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode())
            data = s.recv(1024)

        print(f"Sent: '{query}'")
        print(f"Response: {data.decode()}")

    except ConnectionRefusedError:
        print("Error: Could not connect to Stealth Automation.")
        print("Make sure Chrome is open and the extension is loaded.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python trigger.py "Your Search Query"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    send_trigger(query)
