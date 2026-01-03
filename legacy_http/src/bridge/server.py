import http.server
import socketserver
import json
import threading
import queue
import time

PORT = 8765  # Use the same port as before for consistency


class HttpBridge:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.command_queue = queue.Queue()
        self.results = {}  # Store results by command ID or some identifier
        self.current_command_id = 0
        self.server_thread = None
        self.httpd = None
        self._initialized = True

    def _get_next_command_id(self):
        self.current_command_id += 1
        return self.current_command_id

    def add_command(self, command):
        command_id = self._get_next_command_id()
        command["id"] = command_id
        self.command_queue.put(command)
        print(f"Bridge: Added command {command_id} to queue: {command['action']}")
        return command_id

    def get_result(self, command_id, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if command_id in self.results:
                result = self.results.pop(command_id)
                print(f"Bridge: Retrieved result for command {command_id}")
                return result
            time.sleep(0.1)  # Check every 100ms
        print(f"Bridge: Timeout getting result for command {command_id}")
        return {
            "status": "error",
            "message": f"Timeout waiting for result for command {command_id}",
        }

    def start_server_in_thread(self):
        if self.server_thread and self.server_thread.is_alive():
            print("Bridge: HTTP server already running.")
            return

        Handler = self._create_request_handler()
        self.httpd = socketserver.TCPServer(("", PORT), Handler)
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()
        print(f"Bridge: HTTP server started in background on http://localhost:{PORT}")

    def shutdown_server(self):
        if self.httpd:
            print("Bridge: Shutting down HTTP server...")
            self.httpd.shutdown()
            self.httpd.server_close()
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join()
            print("Bridge: HTTP server shut down.")

    def _create_request_handler(self):
        bridge_instance = self  # Capture instance for handler

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def _set_headers(self):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")  # Crucial for CORS
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header(
                    "Access-Control-Allow-Headers", "X-Requested-With, Content-Type"
                )
                self.end_headers()

            def do_OPTIONS(self):
                self._set_headers()

            def do_GET(self):
                self._set_headers()
                response_content = {"command": None}
                if (
                    self.path == "/command"
                    and not bridge_instance.command_queue.empty()
                ):
                    command = bridge_instance.command_queue.get()
                    response_content["command"] = command
                    print(f"Bridge: Sent command {command['id']} via GET.")
                elif self.path != "/command":
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
                    return

                self.wfile.write(json.dumps(response_content).encode("utf-8"))

            def do_POST(self):
                self._set_headers()
                response_content = {"status": "success"}
                if self.path == "/result":
                    try:
                        content_length = int(self.headers["Content-Length"])
                        post_data = self.rfile.read(content_length)
                        result = json.loads(post_data.decode("utf-8"))
                        command_id = result.get("id")
                        if command_id is not None:
                            bridge_instance.results[command_id] = result
                            print(f"Bridge: Received result for command {command_id}.")
                        else:
                            print(
                                "Bridge: Received POST /result without a command 'id'."
                            )
                            response_content = {
                                "status": "error",
                                "message": "Missing command ID",
                            }

                    except Exception as e:
                        print(f"Bridge: Error processing POST /result: {e}")
                        response_content = {"status": "error", "message": str(e)}
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
                    return

                self.wfile.write(json.dumps(response_content).encode("utf-8"))

        return RequestHandler


if __name__ == "__main__":
    bridge = HttpBridge()
    bridge.start_server_in_thread()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.shutdown_server()
