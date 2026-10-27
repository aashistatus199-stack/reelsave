# ReelSave

Paste a public Instagram reel link, pick MP4 or MP3, download.

## Folder layout
```
reelsave/
  app.py
  requirements.txt
  static/index.html
```

## Run it
1. Install Python 3.10+ and **ffmpeg** (`sudo apt install ffmpeg` on Ubuntu).
2. `pip install -r requirements.txt`
3. `python app.py`
4. Open http://localhost:8000

## Deploy
- Use a VPS (DigitalOcean, Hetzner, etc.).
- Run with gunicorn: `gunicorn -w 2 -b 0.0.0.0:8000 app:app`
- Put Nginx + HTTPS (Let's Encrypt) in front.
- Keep yt-dlp updated, since Instagram changes often: `pip install -U yt-dlp`
- Replace `you@example.com` in the footer with your real contact email.

## Notes
- Videos are streamed to the user, never stored on your server.
- Rate limit: 10 requests per minute per IP (edit `LIMIT` in app.py).
- Instagram may block datacenter IPs. If downloads start failing, update yt-dlp first.
