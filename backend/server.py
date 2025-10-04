
# backend/server.py
import os
import io
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
OUTPUTS_DIR = APP_ROOT / "outputs"
THUMBS_DIR = OUTPUTS_DIR / "thumbs"
SETTINGS_FILE = APP_ROOT / "settings.json"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(FRONTEND_DIR))

# -------- Settings helpers --------
def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "nsfw_allowed": True,
        "provider_order": ["LOCAL"],
        "output_dir": str(OUTPUTS_DIR),
        "thumb_size": 320
    }

def save_settings(data):
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def make_thumb(img_path, size):
    try:
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((size, size))
        out_name = THUMBS_DIR / (Path(img_path).stem + "_th.jpg")
        im.save(out_name, "JPEG", quality=85)
        return out_name.name
    except Exception:
        return None

def save_image_pil(image, basename_prefix="img"):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    name = f"{basename_prefix}_{ts}.png"
    path = OUTPUTS_DIR / name
    image.save(path, "PNG")
    thumb_name = make_thumb(path, load_settings().get("thumb_size", 320))
    return str(path.name), thumb_name

# -------- API --------

@app.get("/api/status")
def api_status():
    s = load_settings()
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat()+"Z",
        "settings": s,
        "outputs_count": len([p for p in OUTPUTS_DIR.iterdir() if p.is_file() and p.suffix.lower() in [".png",".jpg",".jpeg",".webp",".gif"]])
    })

@app.get("/api/outputs")
def api_outputs():
    out = []
    for p in OUTPUTS_DIR.iterdir():
        if p.is_file():
            out.append({
                "name": p.name,
                "size": p.stat().st_size,
                "mtime": p.stat().st_mtime,
                "thumb": (THUMBS_DIR / (p.stem + "_th.jpg")).name if (THUMBS_DIR / (p.stem + "_th.jpg")).exists() else None
            })
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(out)

@app.delete("/api/outputs/<name>")
def api_outputs_delete(name):
    target = OUTPUTS_DIR / name
    if not target.exists():
        return jsonify({"error":"not found"}), 404
    target.unlink()
    th = THUMBS_DIR / (Path(name).stem + "_th.jpg")
    if th.exists():
        th.unlink()
    return jsonify({"status":"deleted","name":name})

@app.get("/outputs/<path:filename>")
def serve_outputs(filename):
    return send_from_directory(str(OUTPUTS_DIR), filename, as_attachment=False)

@app.get("/thumbs/<path:filename>")
def serve_thumbs(filename):
    return send_from_directory(str(THUMBS_DIR), filename, as_attachment=False)

@app.get("/api/settings")
def api_settings_get():
    return jsonify(load_settings())

@app.post("/api/settings")
def api_settings_post():
    incoming = request.get_json(force=True, silent=True) or {}
    s = load_settings()
    s.update({k:v for k,v in incoming.items() if k in ["nsfw_allowed","provider_order","output_dir","thumb_size"]})
    # output_dir change allowed
    out_dir = Path(s.get("output_dir", str(OUTPUTS_DIR)))
    out_dir.mkdir(parents=True, exist_ok=True)
    # update globals if changed
    global OUTPUTS_DIR, THUMBS_DIR
    OUTPUTS_DIR = out_dir
    THUMBS_DIR = out_dir / "thumbs"
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    save_settings(s)
    return jsonify({"status":"ok","settings":s})

@app.post("/api/images/generate")
def api_images_generate():
    """
    Simple local generator: creates a canvas with gradient and writes prompt text.
    Body JSON: { prompt, width?, height?, bg? }
    """
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error":"prompt required"}), 400
    w = int(data.get("width", 768))
    h = int(data.get("height", 768))
    bg = data.get("bg", "#151515")

    # create gradient background
    img = Image.new("RGB", (w,h), bg)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        shade = int(30 + (y/h)*80)
        draw.line([(0,y),(w,y)], fill=(shade,0,0))

    # text overlay
    text = prompt[:200]
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textsize(text, font=font)
    margin = 16
    box = [(margin, h - th - 2*margin), (margin+tw+20, h - margin)]
    draw.rectangle(box, fill=(0,0,0,160))
    draw.text((margin+10, h - th - margin - 2), text, fill=(255,255,255), font=font)

    name, thn = save_image_pil(img, "gen")
    return jsonify({"status":"ok","file":name,"thumb":thn})

@app.post("/api/images/transform")
def api_images_transform():
    """
    Multipart form:
    - image: file
    - ops: JSON string with operations in order, e.g.:
      {
        "grayscale": true,
        "blur": 2.0,
        "rotate": 15,
        "flip_h": true,
        "flip_v": false,
        "pixelate": 6,
        "text": {"value":"Hello","x":20,"y":20,"size":28,"color":"#ffffff"},
        "crop": {"x":10,"y":10,"w":512,"h":512}
      }
    - mask: optional grayscale mask PNG to blend (where white keeps original, black applies effect stronger)
    """
    if "image" not in request.files:
        return jsonify({"error":"image file required"}), 400
    f = request.files["image"]
    try:
        img = Image.open(io.BytesIO(f.read())).convert("RGBA")
    except Exception as e:
        return jsonify({"error":f"cannot open image: {e}"}), 400

    ops_json = request.form.get("ops") or "{}"
    try:
        ops = json.loads(ops_json)
    except Exception:
        ops = {}

    # Work on a copy
    out = img.copy()

    # CROP
    if "crop" in ops and isinstance(ops["crop"], dict):
        x = int(ops["crop"].get("x", 0))
        y = int(ops["crop"].get("y", 0))
        w = int(ops["crop"].get("w", out.width))
        h = int(ops["crop"].get("h", out.height))
        x2, y2 = max(0,x), max(0,y)
        w = max(1, min(w, out.width - x2))
        h = max(1, min(h, out.height - y2))
        out = out.crop((x2,y2,x2+w,y2+h))

    # ROTATE
    if ops.get("rotate"):
        out = out.rotate(float(ops["rotate"]), expand=True, fillcolor=(0,0,0,0))

    # FLIP
    if ops.get("flip_h"):
        out = ImageOps.mirror(out)
    if ops.get("flip_v"):
        out = ImageOps.flip(out)

    # GRAYSCALE
    if ops.get("grayscale"):
        out = ImageOps.grayscale(out).convert("RGBA")

    # BLUR
    if ops.get("blur"):
        out = out.filter(ImageFilter.GaussianBlur(radius=float(ops["blur"])))

    # PIXELATE
    if ops.get("pixelate"):
        factor = max(2, int(ops["pixelate"]))
        small = out.resize((max(1,out.width//factor), max(1,out.height//factor)), resample=Image.NEAREST)
        out = small.resize((out.width, out.height), Image.NEAREST)

    # TEXT
    if isinstance(ops.get("text"), dict):
        t = ops["text"]
        value = str(t.get("value","")).strip()
        if value:
            x = int(t.get("x", 10)); y = int(t.get("y", 10))
            size = int(t.get("size", 28))
            color = t.get("color", "#ffffff")
            try:
                font = ImageFont.truetype("arial.ttf", size)
            except Exception:
                font = ImageFont.load_default()
            d = ImageDraw.Draw(out)
            d.text((x,y), value, fill=color, font=font)

    # Optional MASK blend: if provided, blend original and processed using mask
    if "mask" in request.files:
        try:
            mask = Image.open(io.BytesIO(request.files["mask"].read())).convert("L").resize(out.size)
            out = Image.composite(img.resize(out.size).convert("RGBA"), out, mask)
        except Exception:
            pass

    # Save
    out = out.convert("RGB")
    name, thn = save_image_pil(out, "edit")
    return jsonify({"status":"ok","file":name,"thumb":thn})

# ---------- Frontend routing ----------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def static_proxy(path):
    # Prevent API conflicts
    if path.startswith("api/") or path.startswith("outputs/") or path.startswith("thumbs/"):
        abort(404)
    # Default file
    if path == "" or path.endswith("/"):
        path = "index.html"
    target = FRONTEND_DIR / path
    if target.exists():
        # Serve from frontend folder
        rel_dir = str(FRONTEND_DIR)
        return send_from_directory(rel_dir, path)
    abort(404)

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3001"))
    print(f"ANDIO Local Server running on http://{host}:{port}")
    print(f"Outputs: {OUTPUTS_DIR}")
    app.run(host=host, port=port, debug=False)
