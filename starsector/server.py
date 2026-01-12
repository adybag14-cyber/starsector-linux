import http.server
import socketserver
import os

PORT = 8090

class ForcedRangeHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            file = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        file_size = os.fstat(file.fileno()).st_size
        range_header = self.headers.get('Range')
        if not range_header:
            self.range = None
            self.send_response(200)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Content-Length", str(file_size))
            self.end_headers()
            return file

        if not range_header.startswith("bytes="):
            self.send_error(400, "Invalid Range header")
            file.close()
            return None

        range_value = range_header.replace("bytes=", "").strip()
        if "-" not in range_value:
            self.send_error(400, "Invalid Range header")
            file.close()
            return None

        start_str, end_str = range_value.split("-", 1)
        if start_str == "" and end_str == "":
            self.send_error(400, "Invalid Range header")
            file.close()
            return None

        if start_str == "":
            length = int(end_str)
            start = max(file_size - length, 0)
            end = file_size - 1
        else:
            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1

        if start >= file_size or end < start:
            self.send_error(416, "Requested Range Not Satisfiable")
            file.close()
            return None

        end = min(end, file_size - 1)
        self.send_response(206)
        self.send_header("Content-type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        file.seek(start)
        self.wfile.flush()
        self.range = (start, end)
        return file

    def copyfile(self, source, outputfile):
        if getattr(self, "range", None):
            start, end = self.range
            remaining = end - start + 1
            bufsize = 64 * 1024
            while remaining > 0:
                read_size = min(bufsize, remaining)
                data = source.read(read_size)
                if not data:
                    break
                outputfile.write(data)
                remaining -= len(data)
        else:
            super().copyfile(source, outputfile)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Server on {PORT}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

with ThreadedTCPServer(("", PORT), ForcedRangeHandler) as httpd:
    httpd.serve_forever()
