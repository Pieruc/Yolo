import socket
import threading
import queue
import logging

def handle_tcp_client(conn, addr, send_queue):
    logging.info(f"[TCP] Connessione da {addr}")
    try:
        while True:
            try:
                message = send_queue.get(timeout=1.0)
                conn.sendall((message + "\n").encode('utf-8'))
                send_queue.task_done()
            except queue.Empty:
                continue
            except (ConnectionResetError, BrokenPipeError):
                logging.warning(f"[TCP] Client {addr} disconnesso")
                break
    finally:
        conn.close()

def start_tcp_server(send_queue, host='0.0.0.0', port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    logging.info(f"[TCP] Server in ascolto su {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_tcp_client, args=(conn, addr, send_queue), daemon=True).start()
