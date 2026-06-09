"""
Launch script — serves landing.html on port 8000, Streamlit app on port 8501.
Usage:  python run.py
"""
import http.server
import socketserver
import subprocess
import threading
import webbrowser
import time
import os

BASE         = os.path.dirname(os.path.abspath(__file__))
LANDING_FILE = os.path.join(BASE, 'landing.html')
LANDING_PORT = 8000
APP_PORT     = 8501


class LandingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            with open(LANDING_FILE, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()

    def log_message(self, *args):
        pass


def serve_landing():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', LANDING_PORT), LandingHandler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    t = threading.Thread(target=serve_landing, daemon=True)
    t.start()

    time.sleep(0.4)
    webbrowser.open(f'http://localhost:{LANDING_PORT}')
    print(f'Landing page → http://localhost:{LANDING_PORT}')
    print(f'App          → http://localhost:{APP_PORT}')
    print('Press Ctrl+C to stop.')

    subprocess.run(
        ['streamlit', 'run', 'app_simple.py',
         f'--server.port={APP_PORT}',
         '--server.headless=true'],   # prevents Streamlit from opening its own browser tab
        cwd=BASE
    )
