import socket, threading, sys

SERVER = '127.0.0.1'  
PORT = 12345

def send_line(conn, text):
    conn.sendall((text + '\n').encode())

def recv_line(conn):
    data = b''
    while True:
        chunk = conn.recv(1)
        if not chunk:
            return None
        if chunk == b'\n':
            break
        data += chunk
    return data.decode().strip()