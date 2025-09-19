import cv2
import time
import base64
import queue
import logging
import json
import torch

from ultralytics import YOLO

class_colors = {
    0: (0, 0, 255),    # rosso
    1: (0, 255, 0),    # verde
    2: (0, 255, 255),    # giallo
}


def run_detection(send_queue, frame_queue, video_source=0, resize_factor=1,
                  jpeg_quality=50, show_video=False, test_mode=False,
                  target_fps=10, draw_boxes=True):

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"[YOLO] Device selezionato: {device}")

    if not test_mode:
        model = YOLO("best.pt") #modello addestrato per pomodori, zucchine e banane
        #model = YOLO("yolo11m.pt") #modello preaddestrato yolo
        model.to(device)
        logging.info("[YOLO] Modello caricato su %s", device)
    else:
        model = None
        logging.info("[YOLO] Modalità test attiva")

    cap = cv2.VideoCapture(video_source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        logging.error("[YOLO] Impossibile aprire video/webcam")
        return

    frame_count = 0
    send_enabled = True
    last_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            h, w = frame.shape[:2]
            frame_resized = cv2.resize(frame, (int(w*resize_factor), int(h*resize_factor)))

            detections = []

            if model:
                try:
                    results = model.track(frame, device=device, persist=True)
                    for r in results:
                        if r.boxes is not None:
                            for box in r.boxes:
                                cls_id = int(box.cls[0])
                                cls_name = model.names[cls_id] if hasattr(model, "names") else str(cls_id)
                                conf = float(box.conf[0])
                                if conf < 0.2:
                                    continue

                                x1, y1, x2, y2 = map(int, box.xyxy[0])

                                # Scala coordinate
                                rh, rw = frame_resized.shape[:2]
                                x1_r = int(x1 * rw / w)
                                y1_r = int(y1 * rh / h)
                                x2_r = int(x2 * rw / w)
                                y2_r = int(y2 * rh / h)

                                # Disegna bounding box (separato dalla visualizzazione GUI)
                                if draw_boxes:
                                    color = class_colors.get(cls_id, (255, 255, 255))
                                    cv2.rectangle(frame_resized, (x1_r, y1_r), (x2_r, y2_r), color, 2)
                                    label = f"{cls_name}:{conf:.2f}"
                                    cv2.putText(frame_resized, label, (x1_r, y1_r-10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                                # Centro e dimensioni
                                x_center = (x1_r + x2_r) // 2
                                y_center = (y1_r + y2_r) // 2
                                width = x2_r - x1_r
                                height = y2_r - y1_r

                                obj_id = int(box.id[0]) if box.id is not None else 0

                                detections.append({
                                    "model": 1,
                                    "class": cls_id,
                                    "x_center": x_center,
                                    "y_center": y_center,
                                    "width": width,
                                    "height": height,
                                    "frame_data": None,
                                    "object_id": obj_id
                                })

                except Exception as e:
                    logging.error(f"[YOLO] Errore detection: {e}")

            # Encode JPEG una sola volta
            _, buf = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            frame_bytes = buf.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')

            # Inserisci frame_data in ogni detection
            for det in detections:
                det["frame_data"] = frame_base64

            # Send WS frame
            try:
                frame_queue.put(frame_bytes, timeout=0.1)
            except queue.Full:
                pass

            # Send TCP JSON
            if send_enabled:
                for det in detections:
                    try:
                        send_queue.put(json.dumps(det), timeout=0.1)
                    except queue.Full:
                        pass

            # Mostra video (solo se richiesto)
            if show_video:
                cv2.imshow("YOLO", frame_resized)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    send_enabled = not send_enabled
                    logging.info(f"[YOLO] Invio dati: {'abilitato' if send_enabled else 'disabilitato'}")

            # FPS control
            elapsed = time.time() - last_time
            time.sleep(max(1.0 / target_fps - elapsed, 0))
            last_time = time.time()

    except KeyboardInterrupt:
        logging.info("[YOLO] Interruzione manuale ricevuta")

    finally:
        cap.release()
        if show_video:
            cv2.destroyAllWindows()
        logging.info("[YOLO] Loop detection terminato")