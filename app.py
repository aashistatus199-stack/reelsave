import re
import subprocess
import time
from collections import defaultdict

from flask import Flask, Response, jsonify, request, send_from_directory
import yt_dlp

app = Flask(__name__, static_folder="static")

URL_RE = re.compile(r"^https?://(www\.)?instagram\.com/(reel|reels|p)/[\w-]+/?(\?.*)?$")
HITS = defaultdict(list)
LIMIT, WINDOW = 10, 60  # 10 requests per minute per IP


def too_many():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    now = time.time()
    HITS[ip] = [t for t in HITS[ip] if now - t < WINDOW]
    if len(HITS[ip]) >= LIMIT:
        return True
    HITS[ip].append(now)
    return False


def valid(url):
    return bool(url and URL_RE.match(url.strip()))


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/info")
def info():
    if too_many():
        return jsonify(error="Too many requests. Wait a minute and try again."), 429
    url = (request.json or {}).get("url", "").strip()
    if not valid(url):
        return jsonify(error="Paste a public Instagram reel link."), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            data = ydl.extract_info(url, download=False)
    except Exception:
        return jsonify(error="Couldn't fetch this reel. It may be private or removed."), 422
    heights = sorted({f["height"] for f in data.get("formats", []) if f.get("height")}, reverse=True)
    return jsonify(
        title=(data.get("title") or "Instagram reel")[:120],
        uploader=data.get("uploader") or "",
        thumbnail=data.get("thumbnail"),
        heights=heights,
    )


@app.get("/api/download")
def download():
    if too_many():
        return "Too many requests.", 429
    url = request.args.get("url", "").strip()
    fmt = request.args.get("format", "mp4")
    height = request.args.get("height", "")
    if not valid(url) or fmt not in ("mp4", "mp3"):
        return "Invalid request.", 400

    cmd = ["yt-dlp", "-q", "--no-playlist", "-o", "-"]
    if fmt == "mp3":
        cmd += ["-f", "bestaudio", "-x", "--audio-format", "mp3"]
        mime, ext = "audio/mpeg", "mp3"
    else:
        cap = f"[height<={int(height)}]" if height.isdigit() else ""
        cmd += ["-f", f"bv*{cap}+ba/b{cap}", "--merge-output-format", "mp4",
                "--downloader-args", "ffmpeg:-movflags frag_keyframe+empty_moov"]
        mime, ext = "video/mp4", "mp4"
    cmd.append(url)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def stream():
        try:
            while chunk := proc.stdout.read(64 * 1024):
                yield chunk
        finally:
            proc.kill()

    return Response(
        stream(),
        mimetype=mime,
        headers={"Content-Disposition": f'attachment; filename="reel.{ext}"'},
    )


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
