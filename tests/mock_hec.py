import http.server
import json
from pathlib import Path

HEC_FILE = Path("/srv/output/hec.ndjson")
HEC_FILE.parent.mkdir(parents=True, exist_ok=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length)
        text = data.decode("utf-8", errors="replace")

        def write_events(events):
            with HEC_FILE.open("a", encoding="utf-8") as f:
                for ev in events:
                    json.dump(ev, f)
                    f.write("\n")

        try:
            payload = json.loads(text)
            if isinstance(payload, list):
                write_events(payload)
            else:
                write_events([payload])
        except Exception:
            chunks = text.replace("}{", "}|{").split("|")
            parsed = []
            for chunk in chunks:
                try:
                    parsed.append(json.loads(chunk))
                except Exception:
                    parsed.append({"raw": chunk})
            write_events(parsed)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"text":"Success","code":0}')

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", 8088), Handler)
    server.serve_forever()
