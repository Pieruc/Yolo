# YOLO Detection Server

Un server Python per il rilevamento di oggetti in tempo reale utilizzando YOLO (You Only Look Once) con supporto per streaming WebSocket e TCP.

## Caratteristiche

- **Rilevamento oggetti in tempo reale** con modelli YOLO personalizzati o preaddestrati
- **Streaming video** tramite WebSocket (WS/WSS)
- **Invio dati detection** tramite TCP JSON
- **Supporto SSL/TLS** con certificati auto-generati
- **Due modalità di rilevamento**:
  - Modello agricolo (`main_agri.py`) - specifico per pomodori, zucchine e banane
  - Modello generico (`main_all.py`) - tutte le classi YOLO standard
- **Interfaccia GUI opzionale** per visualizzazione locale
- **Controllo FPS configurabile**

## Requisiti

### Dipendenze Python
```bash
pip install ultralytics opencv-python torch websockets cryptography
```

### Hardware consigliato
- GPU NVIDIA con supporto CUDA (opzionale ma consigliato per prestazioni migliori)
- Webcam o file video come sorgente

## Installazione

1. Clona o scarica i file del progetto
2. Attiva l'ambiente virtuale Ultralytics:
   ```bash
   source ultralytics/bin/activate
   ```
3. Spostati nella cartella del progetto:
   ```bash
   cd yolo_server
   ```
4. Assicurati di avere i modelli YOLO:
   - `best.pt` - modello personalizzato per agricoltura
   - `yolo11m.pt` - modello YOLO preaddestrato (scaricato automaticamente)

## Utilizzo

### Preparazione ambiente
Prima di eseguire qualsiasi comando, assicurati di:
1. Attivare l'ambiente virtuale:
   ```bash
   source ultralytics/bin/activate
   ```
2. Essere nella cartella del progetto:
   ```bash
   cd yolo_server
   ```

### Modalità Agricola (Pomodori, Zucchine, Banane)
```bash
python main_agri.py [opzioni]
```

### Modalità Generica (Tutte le classi YOLO)
```bash
python main_all.py [opzioni]
```

### Opzioni principali

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `--webcam` | Indice webcam da utilizzare | 0 |
| `--video` | Path del file video | - |
| `--gui` | Mostra finestra video locale | False |
| `--ssl` | Abilita SSL per WebSocket | False |
| `--auto-cert` | Genera certificato SSL automaticamente | False |
| `--websocket-port` | Porta del server WebSocket | 9998 |
| `--resize-factor` | Fattore di ridimensionamento frame | 0.4 |
| `--jpeg-quality` | Qualità compressione JPEG (1-100) | 50 |
| `--test-mode` | Modalità test senza YOLO | False |
| `--list-webcams` | Lista webcam disponibili | False |

### Esempi di utilizzo

**Avvio base con webcam:**
```bash
python main_all.py --gui
```

**Con SSL e certificato auto-generato:**
```bash
python main_agri.py --ssl --auto-cert --gui
```

**Da file video:**
```bash
python main_all.py --video /path/to/video.mp4 --gui
```

**Lista webcam disponibili:**
```bash
python main_all.py --list-webcams
```

## Architettura del Sistema

### Componenti principali

1. **WebSocket Server** (`websocket_server.py`)
   - Streaming video in tempo reale
   - Supporto SSL/TLS
   - Gestione multipli client

2. **TCP Server** (`tcp_server.py`)
   - Invio dati detection in formato JSON
   - Connessioni multiple simultanee

3. **YOLO Detector** (`yolo_detector_*.py`)
   - Rilevamento oggetti in tempo reale
   - Tracking degli oggetti
   - Codifica frame per streaming

4. **SSL Utils** (`ssl_utils.py`)
   - Generazione certificati auto-firmati
   - Configurazione SSL

### Flusso dati

```
Webcam/Video → YOLO Detection → Frame Queue (WebSocket) + Data Queue (TCP)
                                      ↓                        ↓
                                WebSocket Clients      TCP Clients (JSON)
```

## Formato Dati

### JSON Detection (TCP)
```json
{
    "model": 1,
    "class": 0,
    "x_center": 320,
    "y_center": 240,
    "width": 100,
    "height": 80,
    "frame_data": "base64_encoded_jpeg",
    "object_id": 123
}
```

### WebSocket Frame
- Frame JPEG codificati in Base64
- Formato: `{"data": "base64_encoded_jpeg"}`

## Configurazione SSL

### Certificati automatici
```bash
python main_all.py --ssl --auto-cert
```
Il sistema genera automaticamente certificati auto-firmati validi per:
- `localhost`
- IP locale della macchina

### Certificati personalizzati
Posiziona i seguenti file nella directory del progetto:
- `fullchain.crt` - Certificato SSL
- `server.key` - Chiave privata
- `rootCA.crt` - Certificato root CA

## Porte di Default

- **WebSocket**: 9998 (WS) / 9998 (WSS se SSL attivo)
- **TCP**: 9999
- **Host**: `192.168.137.200` (configurabile nel codice)

## Controlli Runtime

Durante l'esecuzione con `--gui`:
- `q`: Termina l'applicazione
- `s`: Abilita/disabilita invio dati TCP

## Modelli YOLO Supportati

### Modello Agricolo (`best.pt`)
- Pomodori (classe 0) - rosso
- Zucchine (classe 1) - verde  
- Banane (classe 2) - giallo

### Modello Generico (`yolo11m.pt`)
- 80 classi COCO standard
- Colori generati automaticamente

## Troubleshooting

### Problemi comuni

**Errore: "Impossibile aprire video/webcam"**
- Verifica che la webcam sia connessa e non utilizzata da altre applicazioni
- Usa `--list-webcams` per vedere le webcam disponibili

**Errore SSL certificati**
- Usa `--auto-cert` per generare certificati automaticamente
- Verifica che i file certificato esistano e siano leggibili

**Performance lente**
- Riduci `--resize-factor` (es. 0.2)
- Diminuisci `--jpeg-quality`
- Usa GPU CUDA se disponibile

**Errore modulo 'cryptography'**
```bash
pip install cryptography
```

## Logging

Il sistema utilizza logging Python con livello INFO. I messaggi includono:
- `[YOLO]` - Operazioni di detection
- `[WS/WSS]` - WebSocket server
- `[TCP]` - TCP server  
- `[SSL]` - Operazioni SSL