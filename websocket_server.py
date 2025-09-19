import asyncio
import websockets
import ssl
import json
import base64
import logging
import threading
import os

class WebSocketStreamer:
    def __init__(self, host='192.168.137.200', port=9998,
                 ssl_cert='fullchain.crt', ssl_key='server.key', ssl_root='rootCA.crt'):
        self.host = host
        self.port = port
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.ssl_root = ssl_root
        self.clients = set()
        self.frame_queue = None
        self.running = False
        self.use_ssl = False
        
        if self.ssl_cert and self.ssl_key:
            if os.path.isfile(self.ssl_cert) and os.path.isfile(self.ssl_key):
                self.use_ssl = True
                logging.info(f"[WSS] SSL ABILITATO - Certificato: {self.ssl_cert}, Chiave: {self.ssl_key}")
            else:
                logging.warning(f"[WS] Certificati non trovati - {self.ssl_cert}: {os.path.isfile(self.ssl_cert)}, {self.ssl_key}: {os.path.isfile(self.ssl_key)}")
                logging.warning("[WS] Avvio in modalità non sicura (HTTP)")
                self.ssl_cert = None
                self.ssl_key = None
        else:
            logging.warning("[WS] Certificati non specificati nelle variabili, avvio senza SSL")
            self.ssl_cert = None
            self.ssl_key = None

        # Check root CA if SSL is enabled
        if self.use_ssl and self.ssl_root and not os.path.isfile(self.ssl_root):
            logging.warning(f"[WSS] Root CA non trovata: {self.ssl_root}")
            self.ssl_root = None

    async def register(self, ws):
        self.clients.add(ws)
        proto = "WSS" if self.use_ssl else "WS"
        logging.info(f"[{proto}] Client connesso. Totale: {len(self.clients)}")

    async def unregister(self, ws):
        self.clients.discard(ws)
        proto = "WSS" if self.use_ssl else "WS"
        logging.info(f"[{proto}] Client disconnesso. Totale: {len(self.clients)}")

    async def handler(self, ws, path):
        await self.register(ws)
        try:
            await ws.wait_closed()
        finally:
            await self.unregister(ws)

    async def broadcast_loop(self):
        proto = "WSS" if self.use_ssl else "WS"
        logging.info(f"[{proto}] Loop invio frame avviato")
        while self.running:
            if self.frame_queue and not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                msg = json.dumps({"data": base64.b64encode(frame).decode('utf-8')})
                disconnected = set()
                for ws in self.clients.copy():
                    try:
                        await ws.send(msg)
                    except:
                        disconnected.add(ws)
                for ws in disconnected:
                    self.clients.discard(ws)
                self.frame_queue.task_done()
            else:
                await asyncio.sleep(0.01)

    async def start(self, frame_queue):
        self.frame_queue = frame_queue
        self.running = True

        ssl_context = None
        if self.use_ssl and self.ssl_cert and self.ssl_key:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile='fullchain.crt', keyfile=self.ssl_key)
            
            # Per certificati auto-firmati, configurazione più permissiva
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            logging.info(f"[WSS] Certificato e chiave caricati (modalità permissiva per self-signed)")

            if self.ssl_root:
                try:
                    ssl_context.load_verify_locations(cafile=self.ssl_root)
                    ssl_context.verify_mode = ssl.CERT_OPTIONAL  # Per self-signed
                    logging.info(f"[WSS] Root CA caricata: {self.ssl_root}")
                except Exception as e:
                    logging.error(f"[WSS] Errore caricamento Root CA: {e}")
                    # Continua senza Root CA per self-signed

        loop = asyncio.get_event_loop()
        server = await websockets.serve(self.handler, self.host, self.port, ssl=ssl_context)
        loop.create_task(self.broadcast_loop())
        proto = "WSS" if self.use_ssl else "WS"
        logging.info(f"[{proto}] Server avviato su {self.host}:{self.port}")
        await asyncio.Future()  # run forever

def run_ws_server(frame_queue, host='192.168.137.200', port=9998,
                  ssl_cert='fullchain.crt', ssl_key='server.key', ssl_root='rootCA.crt'):
    def _start():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ws = WebSocketStreamer(host, port, ssl_cert, ssl_key, ssl_root)
        loop.run_until_complete(ws.start(frame_queue))
    threading.Thread(target=_start, daemon=True).start()
