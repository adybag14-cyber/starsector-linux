import http.server
import socketserver
import os

PORT = 8090

class ForcedRangeHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # We override this to ensure the header is written
        # Check if we already sent it to avoid duplicates
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs.st_size
        range_header = self.headers.get('Range')
        self.range = None

        if range_header and range_header.startswith("bytes="):
            range_spec = range_header.replace("bytes=", "").strip()
            start_str, end_str = range_spec.split("-", 1)
            try:
                if start_str:
                    start = int(start_str)
                    end = int(end_str) if end_str else file_len - 1
                elif end_str:
                    suffix_len = int(end_str)
                    if suffix_len <= 0:
                        raise ValueError
                    start = max(0, file_len - suffix_len)
                    end = file_len - 1
                else:
                    raise ValueError
            except ValueError:
                self.send_error(400, "Invalid Range header")
                f.close()
                return None

            if start >= file_len:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{file_len}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                f.close()
                return None

            end = min(end, file_len - 1)
            self.range = (start, end)
            self.send_response(206)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_len}")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            f.seek(start)
            return f

        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(file_len))
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        if self.range:
            start, end = self.range
            remaining = end - start + 1
            bufsize = 64 * 1024
            while remaining > 0:
                read_size = min(bufsize, remaining)
                chunk = source.read(read_size)
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
            return
        super().copyfile(source, outputfile)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Server on {PORT}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
    allow_reuse_address = True

with ThreadedTCPServer(("", PORT), ForcedRangeHandler) as httpd:
    httpd.serve_forever()
