
# ANDIO Local Server (vollständig, ohne Platzhalter)

Dieses Paket enthält einen **voll funktionsfähigen lokalen Windows-Server** (Flask/Python) plus **UI** (Editor, Settings, Gallery).  
Alle Ergebnisse werden in `backend/outputs/` gespeichert und in der **Gallery** angezeigt.

## Start (Windows PowerShell)
```powershell
cd backend
.\run-server.ps1
```
Danach öffne `http://localhost:3001/`

## Seiten
- **Home** (`index.html`): Text→Bild Generator (lokal, ohne Cloud)
- **Editor** (`editor.html`): Bild hochladen, Crop, Rotate, Flip, Graustufen, Blur, Pixelate, Text-Overlay, optional Masken
- **Gallery** (`gallery.html`): Alle gespeicherten Ergebnisse, Download & Löschen
- **Settings** (`settings.html`): NSFW-Flag, Provider-Order (nur lokal hier), Output-Verzeichnis und Thumbnail-Größe

## API (Auszug)
- `GET /api/status` — Serverstatus & Settings
- `GET /api/outputs` — Liste gespeicherter Dateien + Thumbs
- `DELETE /api/outputs/<name>` — löscht Datei + Thumb
- `POST /api/images/generate` — erzeugt Bild mit Prompt-Text (lokal, Pillow)
- `POST /api/images/transform` — führt Operationen am hochgeladenen Bild aus (siehe Editor)

## Hinweise
- Keine externen Provider erforderlich. Alles funktioniert offline.
- Thumbnails werden automatisch in `backend/outputs/thumbs/` erzeugt.
