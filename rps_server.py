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
def recv_line(conn, timeout=30):
    conn.settimeout(timeout)
    data = b''
    try:
        while True:
            chunk = conn.recv(1)
            if not chunk:
                return None
            if chunk == b'\n':
                break
            data += chunk
        return data.decode().strip()
    except socket.timeout:
        return None
    except:
        return None

def judge(move1, move2):
    if move1 == move2:
        return 0
    wins = { 'R':'S', 'P':'R', 'S':'P' }
    return 1 if wins[move1] == move2 else -1

def handle_game(p1_conn, p1_name, p2_conn, p2_name):
    rounds_needed = (BEST_OF // 2) + 1
    score1 = score2 = 0
    round_no = 0
    try:
        send_line(p1_conn, f'PAIR|{p2_name}')
        send_line(p2_conn, f'PAIR|{p1_name}')
        while score1 < rounds_needed and score2 < rounds_needed:
            round_no += 1
            send_line(p1_conn, f'MOVE_REQUEST|{round_no}')
            send_line(p2_conn, f'MOVE_REQUEST|{round_no}')
            m1 = recv_line(p1_conn, timeout=25)
            if m1 is None:
                send_line(p2_conn, 'OPPONENT_LEFT|')
                break
            m2 = recv_line(p2_conn, timeout=25)
            if m2 is None:
                send_line(p1_conn, 'OPPONENT_LEFT|')
                break
            try:
                _, mv1 = m1.split('|')
                _, mv2 = m2.split('|')
                mv1, mv2 = mv1.strip().upper(), mv2.strip().upper()
                res = judge(mv1, mv2)
                if res == 1:
                    score1 += 1; outcome1, outcome2 = 'win', 'lose'
                elif res == -1:
                    score2 += 1; outcome1, outcome2 = 'lose', 'win'
                else:
                    outcome1 = outcome2 = 'tie'
                send_line(p1_conn, f'ROUND_RESULT|{outcome1}|{mv1}|{mv2}|{score1}|{score2}')
                send_line(p2_conn, f'ROUND_RESULT|{outcome2}|{mv2}|{mv1}|{score2}|{score1}')
            except:
                send_line(p1_conn, 'ERROR|Bad move')
                send_line(p2_conn, 'ERROR|Bad move')
                break
        if score1 > score2:
            send_line(p1_conn, f'GAME_OVER|you_win|{score1}|{score2}')
            send_line(p2_conn, f'GAME_OVER|you_lose|{score2}|{score1}')
        elif score2 > score1:
            send_line(p1_conn, f'GAME_OVER|you_lose|{score1}|{score2}')
            send_line(p2_conn, f'GAME_OVER|you_win|{score2}|{score1}')
        else:
            send_line(p1_conn, f'GAME_OVER|draw|{score1}|{score2}')
            send_line(p2_conn, f'GAME_OVER|draw|{score2}|{score1}')
    finally:
        try: p1_conn.close()
        except: pass
        try: p2_conn.close()
        except: pass

def client_thread(conn, addr):
    try:
        line = recv_line(conn, timeout=20)
        if not line or not line.startswith('HELLO|'):
            send_line(conn, 'ERROR|Missing HELLO')
            conn.close()
            return
        _, name = line.split('|',1)
        name = name.strip()
        with lock:
            clients[conn] = name
        send_line(conn, 'WAIT|')
        waiting_queue.put((conn, name))
    except:
        try: conn.close()
        except: pass

def pairing_worker():
    while True:
        try:
            p1 = waiting_queue.get()
            p2 = waiting_queue.get()
            if not p1 or not p2:
                continue
            p1_conn, p1_name = p1
            p2_conn, p2_name = p2
            threading.Thread(target=handle_game, args=(p1_conn,p1_name,p2_conn,p2_name), daemon=True).start()
        except:
            time.sleep(0.1)

def main():
    threading.Thread(target=pairing_worker, daemon=True).start()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(100)
    print(f'RPS Server listening on {HOST}:{PORT}')
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print('Server stopped.')
    finally:
        s.close()

if __name__ == '__main__':
    main()