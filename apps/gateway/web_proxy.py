#!/usr/bin/env python3
"""
ModernWMS & PartDB Touch Suite HTTP/WebSocket Gateway Proxy
Listens on port 7681.
- Serves /ModernWMS_Touch_Suite.apk directly for 1-click APK download.
- Serves /manifest.json for PWA Web App Installation.
- Transparently proxies all other HTTP & WebSocket traffic to ttyd on port 7682.
"""

import os
import sys
import socket
import select
import threading

LISTEN_PORT = int(os.environ.get("GATEWAY_PORT", "7681"))
TTYD_PORT = int(os.environ.get("TTYD_PORT", "7682"))

def resolve_apk_path():
    env_path = os.environ.get("APK_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mobile", "ModernWMS_Touch_Suite.apk")
    if os.path.exists(local_path):
        return os.path.abspath(local_path)
    return "/root/ModernWMS_Touch_Suite.apk"

APK_PATH = resolve_apk_path()

MANIFEST_JSON = """{
  "name": "ModernWMS Touch Control Suite",
  "short_name": "ModernWMS",
  "start_url": "/",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#0b0f19",
  "theme_color": "#0b0f19"
}"""

def handle_client(client_sock, client_addr):
    try:
        client_sock.settimeout(5.0)
        peek_data = client_sock.recv(4096, socket.MSG_PEEK)
        if not peek_data:
            client_sock.close()
            return

        request_line = peek_data.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        
        # Check if requesting APK file
        if "/ModernWMS_Touch_Suite.apk" in request_line or "/app.apk" in request_line:
            _ = client_sock.recv(4096)  # consume request
            if os.path.exists(APK_PATH):
                file_size = os.path.getsize(APK_PATH)
                header = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: application/vnd.android.package-archive\r\n"
                    f"Content-Disposition: attachment; filename=\"ModernWMS_Touch_Suite.apk\"\r\n"
                    f"Content-Length: {file_size}\r\n"
                    f"Access-Control-Allow-Origin: *\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode('utf-8')
                client_sock.sendall(header)
                if not request_line.startswith("HEAD"):
                    with open(APK_PATH, 'rb') as f:
                        while chunk := f.read(65536):
                            client_sock.sendall(chunk)
            else:
                resp = "HTTP/1.1 404 Not Found\r\nContent-Length: 13\r\n\r\nAPK not found".encode('utf-8')
                client_sock.sendall(resp)
            client_sock.close()
            return

        # Check if requesting Manifest
        if "/manifest.json" in request_line:
            _ = client_sock.recv(4096)
            data_bytes = MANIFEST_JSON.encode('utf-8')
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/manifest+json\r\n"
                f"Content-Length: {len(data_bytes)}\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Connection: close\r\n\r\n"
            ).encode('utf-8')
            client_sock.sendall(header)
            if not request_line.startswith("HEAD"):
                client_sock.sendall(data_bytes)
            client_sock.close()
            return

        # Proxy connection to ttyd on 7682
        ttyd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ttyd_sock.connect(('127.0.0.1', TTYD_PORT))

        client_sock.settimeout(None)
        ttyd_sock.settimeout(None)

        def pipe(src, dst):
            try:
                while True:
                    data = src.recv(32768)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception:
                pass
            finally:
                try: src.shutdown(socket.SHUT_RDWR)
                except Exception: pass
                try: dst.shutdown(socket.SHUT_RDWR)
                except Exception: pass

        t1 = threading.Thread(target=pipe, args=(client_sock, ttyd_sock), daemon=True)
        t2 = threading.Thread(target=pipe, args=(ttyd_sock, client_sock), daemon=True)
        t1.start()
        t2.start()

    except Exception:
        try: client_sock.close()
        except Exception: pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen(128)
    print(f"Gateway Proxy active on port {LISTEN_PORT} -> ttyd target on port {TTYD_PORT}")

    while True:
        try:
            client_sock, client_addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            break
        except Exception:
            pass

if __name__ == '__main__':
    main()
