"""
Local HTTP Fixture Server for Deterministic Semantic UI Automation Testing.

Provides local HTML pages with form, table, modal, error, dynamic loading, and popup fixtures.
"""

import http.server
import socketserver
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

FIXTURE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>JARVIS Semantic UI Fixture</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .hidden { display: none; }
        .modal { border: 2px solid red; padding: 15px; background: #fff0f0; margin-top: 10px; }
        table, th, td { border: 1px solid #ccc; border-collapse: collapse; padding: 8px; }
    </style>
</head>
<body>
    <h1>Customer Portal</h1>
    <nav>
        <button id="btn_nav_dashboard">Dashboard</button>
        <button id="btn_nav_reports">Reports</button>
        <button id="btn_nav_settings">Settings</button>
        <button id="btn_advanced">Advanced</button>
        <button id="btn_download" style="margin-left: 20px;">Download</button>
    </nav>

    <h2>Registration Form</h2>
    <form id="user_form">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" placeholder="Enter username"><br><br>

        <label for="email">Email:</label>
        <input type="email" id="email" name="email" placeholder="Enter email"><br><br>

        <label for="address">Address:</label>
        <input type="text" id="address" name="address" placeholder="Enter address"><br><br>

        <button type="button" id="btn_submit" onclick="submitForm()">Submit</button>
    </form>

    <h2>Customers Table</h2>
    <table id="customers_table">
        <thead>
            <tr><th>Name</th><th>Email</th><th>Status</th><th>Action</th></tr>
        </thead>
        <tbody>
            <tr><td>John Doe</td><td>john@example.com</td><td>Active</td><td><button onclick="openCustomer('John Doe')">Open</button></td></tr>
            <tr><td>Customer ABC</td><td>abc@corp.com</td><td>Pending</td><td><button onclick="openCustomer('Customer ABC')">Open</button></td></tr>
        </tbody>
    </table>

    <div id="loading_spinner" class="hidden">Loading...</div>

    <div id="error_dialog" class="modal hidden">
        <h3 id="err_title">Error Occurred</h3>
        <p id="err_msg">Connection timeout while uploading document.</p>
        <button onclick="closeModal()">Close</button>
    </div>

    <script>
        function submitForm() {
            document.getElementById('loading_spinner').classList.remove('hidden');
            setTimeout(() => {
                document.getElementById('loading_spinner').classList.add('hidden');
                alert('Saved successfully');
            }, 500);
        }
        function openCustomer(name) {
            document.getElementById('error_dialog').classList.remove('hidden');
        }
        function closeModal() {
            document.getElementById('error_dialog').classList.add('hidden');
        }
    </script>
</body>
</html>
"""


class FixtureHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(FIXTURE_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Quiet logging


class LocalUIFixtureServer:
    """Threaded local HTTP server providing local UI test fixtures."""

    def __init__(self, port: int = 8999):
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(("127.0.0.1", self.port), FixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"Local UI Fixture Server running at http://127.0.0.1:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Local UI Fixture Server stopped.")

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"
