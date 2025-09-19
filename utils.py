import cv2
import logging

def detect_webcams(max_test=5):
    cams = []
    logging.info("[UTILS] Ricerca webcam...")
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                cams.append({"index": i, "width": width, "height": height, "fps": fps})
            cap.release()
    if not cams:
        logging.warning("[UTILS] Nessuna webcam trovata")
    return cams
