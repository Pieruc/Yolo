import os
import queue
import threading
import logging
import argparse
from ssl_utils import generate_self_signed_cert
from tcp_server import start_tcp_server
from websocket_server import run_ws_server
from yolo_detector_all import run_detection
from utils import detect_webcams

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--webcam', type=int, default=0)
    parser.add_argument('--video', type=str)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--ssl', action='store_true')
    parser.add_argument('--auto-cert', action='store_true')
    parser.add_argument('--websocket-port', type=int, default=9998)
    parser.add_argument('--resize-factor', type=float, default=0.4)
    parser.add_argument('--jpeg-quality', type=int, default=50)
    parser.add_argument('--test-mode', action='store_true')
    parser.add_argument('--list-webcams', action='store_true')
    parser.add_argument('--cert', type=str, default="fullchain.crt", help='File certificato SSL')
    parser.add_argument('--key', type=str, default="server.key", help='File chiave privata SSL')
    
    args = parser.parse_args()

    # Lista webcam disponibili
    if args.list_webcams:
        cams = detect_webcams()
        for c in cams:
            print(f"Webcam {c['index']}: {c['width']}x{c['height']} @ {c['fps']}fps")
        return

    # Sorgente video
    video_source = args.video if args.video else args.webcam

    # Configurazione SSL
    ssl_cert = ssl_key = ssl_root = None
    if args.ssl:
        if args.auto_cert:
            ssl_cert, ssl_key = generate_self_signed_cert()
            ssl_root = ssl_cert  # auto-cert usa il certificato stesso come root
        else:
            crt_files = [f for f in os.listdir('.') if f.endswith('.crt')]
            key_files = [f for f in os.listdir('.') if f.endswith('.key')]
            root_files = [f for f in os.listdir('.') if f.endswith('.pem')]
            if crt_files and key_files and root_files:
                ssl_cert = crt_files[0]
                ssl_key = key_files[0]
                ssl_root = root_files[0]
                logging.info(f"[SSL] Cert: {ssl_cert}, Key: {ssl_key}, Root: {ssl_root}")
            else:
                logging.warning("[SSL] Mancano certificato, chiave o root, WSS non sarà abilitato")


    # Code condivise
    send_queue = queue.Queue(maxsize=100)
    frame_queue = queue.Queue(maxsize=30)

    # Avvio TCP server in background
    threading.Thread(
        target=start_tcp_server,
        args=(send_queue,),
        daemon=True
    ).start()

    # Avvio WebSocket server in background
    threading.Thread(
        target=run_ws_server,
        kwargs={
            'frame_queue': frame_queue,
            'host': '192.168.137.200',
            'port': args.websocket_port,
            'ssl_cert': 'fullchain.crt',
            'ssl_key': 'server.key',
            'ssl_root': 'rootCA.crt'
        },
        daemon=True
    ).start()


    logging.info("Server avviato, inizio detection...")

    # Loop detection (rimane nel main thread)
    run_detection(
        send_queue,
        frame_queue,
        video_source=video_source,
        resize_factor=args.resize_factor,
        jpeg_quality=args.jpeg_quality,
        show_video=args.gui,
        test_mode=args.test_mode
    )

if __name__ == "__main__":
    main()
