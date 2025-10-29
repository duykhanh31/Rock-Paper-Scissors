import socket, threading, queue, time

HOST = '0.0.0.0'
PORT = 12345
BEST_OF = 3  # best-of-N rounds (phải là số lẻ)

lock = threading.Lock()
waiting_queue = queue.Queue()
clients = {}  # socket -> name

def send_line(conn, text):
    try:
        conn.sendall((text + '\n').encode())
    except:
        pass
