import http.server
import socketserver
import os

PORT = 8090

class ForcedRangeHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        # We override this to ensure the header is written
        # Check if we already sent it to avoid duplicates
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        super().end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Server on {PORT}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 128

with ThreadedTCPServer(("", PORT), ForcedRangeHandler) as httpd:
    httpd.serve_forever()
