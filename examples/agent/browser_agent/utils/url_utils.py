# -*- coding: utf-8 -*-
"""URL utilities for browser agent."""
import os
import sys
import socket
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.request import url2pathname
from urllib.parse import urlparse
from typing import Tuple, Optional

def _fix_windows_path(path: str) -> str:
    """Fix paths like /C:/... on Windows."""
    if sys.platform == 'win32' and path.startswith('/') and len(path) > 2 and path[2] == ':':
        return path[1:]
    return path

def sanitize_start_url(start_url: str) -> Tuple[str, bool]:
    """
    Sanitize the start URL and detect if it is a local file.
    
    Returns:
        Tuple[str, bool]: (processed_url, is_local_mode)
    
    Raises:
        ValueError: If the start_url is invalid or points to a non-existent file.
    """
    is_local_mode = False
    
    if not start_url.startswith(("http://", "https://", "file://")):
        if os.path.exists(start_url):
            start_url = Path(start_url).absolute().as_uri()
            is_local_mode = True
        else:
            # Not an existing file, check if it's likely a URL
            # Heuristic: must have a dot in the domain part (before first slash), or be localhost
            domain_part = start_url.split('/')[0]
            if "." in domain_part or domain_part.split(':')[0] == "localhost":
                # Special case for local addresses to use http instead of https
                host = domain_part.split(':')[0]
                if host in ("localhost", "127.0.0.1"):
                    prefix = "http://"
                else:
                    prefix = "https://"
                print(f"Incomplete URL detected, prepending {prefix} to {start_url}")
                start_url = prefix + start_url
            else:
                # Neither an existing file nor a likely URL
                if "/" in start_url or start_url.endswith((".html", ".htm")):
                    raise ValueError(f"Local file not found: {start_url}")
                else:
                    raise ValueError(
                        f"Invalid start-url. '{start_url}' is neither a valid web URL nor an existing local file."
                    )
    elif start_url.startswith("file://"):
        is_local_mode = True
        # Cross-platform way to get path from file:// URL
        potential_path = _fix_windows_path(url2pathname(urlparse(start_url).path))

        if not os.path.exists(potential_path):
            raise ValueError(f"Local file not found: {potential_path}")
            
    return start_url, is_local_mode

class LocalFileServer:
    """A simple HTTP server to host local files."""
    def __init__(self, file_uri: str) -> None:
        self.httpd: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.port: int = 0
        self.original_uri: str = file_uri
        self.hosted_url: str = file_uri
        self._ready: threading.Event = threading.Event()
        
        if not file_uri.startswith("file://"):
            return

        file_path_str = _fix_windows_path(url2pathname(urlparse(file_uri).path))
        self.file_path = Path(file_path_str)
        
        if not self.file_path.exists():
            return

        file_parent_dir = str(self.file_path.parent)
        file_name = self.file_path.name
        
        def run_server() -> None:
            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=file_parent_dir, **kwargs)
                def log_message(self, format, *args):
                    return # Silent
            
            try:
                # Bind to port 0 to let OS find a free port
                self.httpd = HTTPServer(('127.0.0.1', 0), Handler)
                self.port = self.httpd.server_address[1]
                self._ready.set()
                self.httpd.serve_forever()
            except Exception as e:
                print(f"Failed to start local server: {e}")
                self._ready.set() # Set even on failure to avoid hanging __init__

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        
        # Wait for server to bind and start
        if self._ready.wait(timeout=5.0) and self.httpd:
            self.hosted_url = f"http://127.0.0.1:{self.port}/{file_name}"
            print(f"Hosting local file {self.original_uri} at {self.hosted_url}")
        else:
            print(f"Warning: Local server failed to start for {self.original_uri}")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.httpd is not None

    def stop(self) -> None:
        """Stop the server."""
        if self.httpd:
            print("Shutting down local server...")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
