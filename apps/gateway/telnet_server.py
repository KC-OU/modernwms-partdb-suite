#!/usr/bin/env python3
"""
===============================================================================
 ModernWMS & PartDB Dedicated Telnet / Handheld Terminal Daemon
 Author: Google Antigravity Agentic Assistant
 Port: 2323 (Telnet / Raw Socket Access for Zebra, Honeywell & CLI scanners)
 Features:
   - True PTY Allocation for ANSI color TUI execution
   - Telnet IAC Option Negotiation (ECHO, SGA, BINARY, NAWS)
   - Multi-Session Concurrent Client Handling
   - Graceful Disconnect & Subprocess Cleanup
===============================================================================
"""

import os
import sys
import socket
import select
import pty
import tty
import termios
import threading
import subprocess
import struct
import fcntl
import signal

def resolve_tui_path():
    env_path = os.environ.get("TUI_SCRIPT")
    if env_path and os.path.exists(env_path):
        return env_path
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cli", "modernwms_tui.py")
    if os.path.exists(local_path):
        return os.path.abspath(local_path)
    return "/root/scripts/modernwms_tui.py"

LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORTS = [int(p) for p in os.environ.get("LISTEN_PORTS", "23,2323").split(",") if p.strip()]
TUI_COMMAND = [sys.executable, resolve_tui_path()]

# Telnet Command Constants (RFC 854)
IAC  = bytes([255])
DONT = bytes([254])
DO   = bytes([253])
WONT = bytes([252])
WILL = bytes([251])
SB   = bytes([250])
SE   = bytes([240])

# Telnet Options
TELOPT_BINARY = bytes([0])   # 8-bit data
TELOPT_ECHO   = bytes([1])   # Echo
TELOPT_SGA    = bytes([3])   # Suppress Go Ahead
TELOPT_TTYPE  = bytes([24])  # Terminal Type
TELOPT_NAWS   = bytes([31])  # Negotiate About Window Size

def handle_telnet_session(client_sock, client_addr):
    """Handles an incoming Telnet connection, allocates a PTY, and bridges I/O."""
    print(f"[Telnet] Incoming connection from {client_addr[0]}:{client_addr[1]}")
    master_fd = None
    slave_fd = None
    proc = None

    try:
        # Telnet negotiation: Character at a time, binary mode, echo handled by app
        client_sock.sendall(IAC + WILL + TELOPT_ECHO)
        client_sock.sendall(IAC + WILL + TELOPT_SGA)
        client_sock.sendall(IAC + WILL + TELOPT_BINARY)
        client_sock.sendall(IAC + DO + TELOPT_BINARY)
        client_sock.sendall(IAC + DO + TELOPT_NAWS)

        master_fd, slave_fd = pty.openpty()

        # Set default terminal window size (80 cols, 25 rows)
        winsize = struct.pack("HHHH", 25, 80, 0, 0)
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

        # Set environment for spawned process
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"

        proc = subprocess.Popen(
            TUI_COMMAND,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=env,
            preexec_fn=os.setsid
        )
        os.close(slave_fd)
        slave_fd = None

        running = True

        def socket_to_pty():
            nonlocal running
            iac_buffer = bytearray()
            in_subnegotiation = False

            while running:
                try:
                    data = client_sock.recv(4096)
                    if not data:
                        break

                    # Filter Telnet IAC sequences
                    clean_data = bytearray()
                    i = 0
                    while i < len(data):
                        b = data[i:i+1]
                        if b == IAC:
                            if i + 1 < len(data):
                                cmd = data[i+1:i+2]
                                if cmd in (DO, DONT, WILL, WONT):
                                    # Skip 3-byte IAC command
                                    i += 3
                                    continue
                                elif cmd == SB:
                                    in_subnegotiation = True
                                    i += 2
                                    continue
                                elif cmd == SE:
                                    in_subnegotiation = False
                                    i += 2
                                    continue
                                elif cmd == IAC:
                                    # Escaped 255 byte
                                    clean_data.append(255)
                                    i += 2
                                    continue
                            i += 2
                            continue

                        if in_subnegotiation:
                            i += 1
                            continue

                        clean_data.append(b[0])
                        i += 1

                    if clean_data and master_fd is not None:
                        os.write(master_fd, clean_data)

                except Exception:
                    break
            running = False

        def pty_to_socket():
            nonlocal running
            while running:
                try:
                    rlist, _, _ = select.select([master_fd], [], [], 0.2)
                    if rlist:
                        output = os.read(master_fd, 4096)
                        if not output:
                            break
                        client_sock.sendall(output)
                    if proc.poll() is not None:
                        break
                except Exception:
                    break
            running = False

        t1 = threading.Thread(target=socket_to_pty, daemon=True)
        t2 = threading.Thread(target=pty_to_socket, daemon=True)
        t1.start()
        t2.start()

        while running and proc.poll() is None:
            select.select([master_fd], [], [], 0.5)

    except Exception as e:
        print(f"[Telnet] Error during session {client_addr}: {e}")
    finally:
        if slave_fd is not None:
            try: os.close(slave_fd)
            except Exception: pass
        if master_fd is not None:
            try: os.close(master_fd)
            except Exception: pass
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except Exception:
                try: proc.kill()
                except Exception: pass
        try:
            client_sock.close()
        except Exception:
            pass
        print(f"[Telnet] Session ended for {client_addr[0]}:{client_addr[1]}")

def start_telnet_server():
    server_sockets = []
    for port in LISTEN_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((LISTEN_HOST, port))
            s.listen(64)
            server_sockets.append(s)
            print(f"✅ ModernWMS & PartDB Telnet Daemon listening on {LISTEN_HOST}:{port}")
        except Exception as e:
            print(f"⚠️  Could not bind on port {port}: {e}")

    if not server_sockets:
        print("❌ Failed to bind on any Telnet ports.")
        sys.exit(1)

    def shutdown_handler(signum, frame):
        print("\n[Telnet] Shutting down Telnet daemon...")
        for s in server_sockets:
            try: s.close()
            except Exception: pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    while True:
        try:
            rlist, _, _ = select.select(server_sockets, [], [], 1.0)
            for s in rlist:
                client_sock, client_addr = s.accept()
                client_thread = threading.Thread(
                    target=handle_telnet_session,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
        except Exception as e:
            if not sys.is_finalizing():
                print(f"[Telnet] Accept error: {e}")
            break

if __name__ == "__main__":
    start_telnet_server()
