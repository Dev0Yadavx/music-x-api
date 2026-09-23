import base64
import os
import re
import requests
from flask import Flask, request, jsonify, render_template_string
from Crypto.Cipher import DES

app = Flask(__name__)

BASE_URL = "https://www.jiosaavn.com/api.php"
DES_KEY = b"38346591"

# Cloud Hosting ke liye Indian Geo-Spoofing & Web Browser Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Referer": "https://www.jiosaavn.com/",
    "Origin": "https://www.jiosaavn.com",
    "X-Forwarded-For": "49.37.0.1",  # Indian Jio IP header spoof
    "Cookie": "L=hindi%2Cbhojpuri%2Charyanvi%2Cpunjabi%2Cenglish; gdpr_acceptable=true"
}

def decrypt_url(cipher_text: str) -> dict:
    try:
        cipher = DES.new(DES_KEY, DES.MODE_ECB)
        decrypted = cipher.decrypt(base64.b64decode(cipher_text))
        pad_len = decrypted[-1]
        base_link = decrypted[:-pad_len].decode("utf-8")
        return {
            "96kbps": base_link.replace("_96.mp4", "_96.mp4"),
            "160kbps": base_link.replace("_96.mp4", "_160.mp4"),
            "320kbps": base_link.replace("_96.mp4", "_320.mp4")
        }
    except Exception:
        return {"96kbps": "", "160kbps": "", "320kbps": ""}

def format_image(img_url: str) -> dict:
    if not img_url:
        return {"low": "", "medium": "", "high": "", "ultra": ""}
    img_url = img_url.replace("http://", "https://")
    low = re.sub(r'_\d+x\d+\.(jpg|png)', '_50x50.\\1', img_url)
    medium = re.sub(r'_\d+x\d+\.(jpg|png)', '_150x150.\\1', img_url)
    high = re.sub(r'_\d+x\d+\.(jpg|png)', '_500x500.\\1', img_url)
    if "_500x500" not in high:
        high = img_url.replace("150x150", "500x500").replace("50x50", "500x500")
        low = img_url.replace("500x500", "50x50").replace("150x150", "50x50")
        medium = img_url.replace("500x500", "150x150").replace("50x50", "150x150")
    return {"low": low, "medium": medium, "high": high, "ultra": high}

def format_song(song: dict) -> dict:
    enc_url = song.get("more_info", {}).get("encrypted_media_url", "")
    return {
        "id": song.get("id"),
        "title": song.get("title", "").replace("&quot;", '"').replace("&amp;", "&"),
        "subtitle": song.get("subtitle", ""),
        "type": "song",
        "album": song.get("more_info", {}).get("album", ""),
        "album_id": song.get("more_info", {}).get("album_id", ""),
        "primary_artists": song.get("more_info", {}).get("artistMap", {}).get("primary_artists", []),
        "year": song.get("year", ""),
        "duration": song.get("more_info", {}).get("duration", "0"),
        "language": song.get("language", ""),
        "has_lyrics": song.get("more_info", {}).get("has_lyrics", "false"),
        "lyrics_id": song.get("more_info", {}).get("lyrics_id", song.get("id")),
        "image": format_image(song.get("image", "")),
        "download_url": decrypt_url(enc_url) if enc_url else {}
    }

def fetch_jio(params: dict):
    params.update({
        "_format": "json", 
        "_marker": "0", 
        "api_version": "4", 
        "ctx": "web6dot0"
    })
    res = requests.get(BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=12)
    try:
        return res.json()
    except Exception:
        return {}

def resolve_song_data(identifier: str):
    res = fetch_jio({"__call": "song.getDetails", "pids": identifier})
    if identifier in res:
        return res[identifier]
    token_res = fetch_jio({"__call": "webapi.get", "token": identifier, "type": "song"})
    if "songs" in token_res and len(token_res["songs"]) > 0:
        return token_res["songs"][0]
    return None

# Root documentation UI
@app.route("/", methods=["GET"])
def index():
    html_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Music x Api Docs</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --pink: #ff2e93;
                --yellow: #ffd000;
                --green-neon: #39ff14;
                --bg: #07040a;
                --glass-bg: rgba(22, 12, 28, 0.65);
                --glass-border: rgba(255, 255, 255, 0.12);
                --text-main: #f8fafc;
                --text-muted: #cbd5e1;
                --gradient-py: linear-gradient(135deg, #ff2e93 0%, #ffd000 100%);
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: var(--bg); color: var(--text-main); padding: 20px 14px; min-height: 100vh; }
            .container { max-width: 900px; margin: 0 auto; }
            header {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 22px;
                margin-bottom: 22px;
            }
            h1 {
                font-size: 26px;
                font-weight: 800;
                background: var(--gradient-py);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .cards-list { display: flex; flex-direction: column; gap: 14px; }
            .card {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(18px);
                border-radius: 16px;
                padding: 16px 18px;
            }
            .input-wrapper { display: flex; align-items: center; gap: 8px; background: #030205; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 6px 10px; }
            .input-wrapper input { flex: 1; background: transparent; border: none; color: var(--yellow); font-family: monospace; font-size: 13px; outline: none; }
            .btn { background: var(--gradient-py); color: #000; border: none; padding: 6px 16px; font-weight: 800; border-radius: 8px; cursor: pointer; }
            .inline-tester { display: none; margin-top: 14px; border-top: 1px dashed rgba(255, 255, 255, 0.15); padding-top: 12px; }
            .tester-bar { display: flex; justify-content: space-between; margin-bottom: 8px; }
            .json-viewer { background: #030105; border: 1px solid rgba(57, 255, 20, 0.25); border-radius: 10px; padding: 12px; max-height: 280px; overflow-y: auto; font-family: monospace; font-size: 12px; color: var(--green-neon); white-space: pre-wrap; word-break: break-all; }
            .btn-close { background: rgba(255,255,255,0.1); color:#fff; border:none; padding:2px 8px; border-radius:6px; cursor:pointer; }
            .bulk-card { background: var(--glass-bg); border: 1px solid rgba(255, 208, 0, 0.3); border-radius: 18px; padding: 18px; margin-top: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
            .btn-bulk { background: rgba(57, 255, 20, 0.1); color: var(--green-neon); border: 1px solid rgba(57, 255, 20, 0.3); padding: 8px 16px; border-radius: 10px; font-weight: 700; cursor: pointer; }
            .toast { position: fixed; top: 20px; right: 20px; background: var(--gradient-py); color: #000; padding: 8px 16px; border-radius: 8px; font-weight: 800; display: none; z-index: 9999; }
        </style>
    </head>
    <body>
        <div class="toast" id="toast">Copied!</div>
        <div class="container">
            <header>
                <h1>Music x Api Docs (Global Cloud Engine)</h1>
            </header>
            <div class="cards-list">
                <div class="card">
                    <div style="font-weight:700; margin-bottom:8px;">Search Songs (Global & Regional Bypass)</div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-search" value="/search?query=kesariya&page=1&limit=5">
                        <button class="btn" onclick="runInlineTest('search', 'url-search')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-search">
                        <div class="tester-bar"><span style="color:var(--green-neon);font-weight:700;" id="status-search">READY</span><button class="btn-close" onclick="closeTest('search')">✕</button></div>
                        <pre class="json-viewer" id="json-search"></pre>
                    </div>
                </div>

                <div class="card">
                    <div style="font-weight:700; margin-bottom:8px;">Home Regional (Hindi, Bhojpuri, Haryanvi)</div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-home" value="/home?languages=hindi,bhojpuri,haryanvi" readonly>
                        <button class="btn" onclick="runInlineTest('home', 'url-home')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-home">
                        <div class="tester-bar"><span style="color:var(--green-neon);font-weight:700;" id="status-home">READY</span><button class="btn-close" onclick="closeTest('home')">✕</button></div>
                        <pre class="json-viewer" id="json-home"></pre>
                    </div>
                </div>

                <div class="card">
                    <div style="font-weight:700; margin-bottom:8px;">Song Stream Decrypt (320kbps)</div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-song" value="/song?id=c9_7sW8q">
                        <button class="btn" onclick="runInlineTest('song', 'url-song')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-song">
                        <div class="tester-bar"><span style="color:var(--green-neon);font-weight:700;" id="status-song">READY</span><button class="btn-close" onclick="closeTest('song')">✕</button></div>
                        <pre class="json-viewer" id="json-song"></pre>
                    </div>
                </div>
            </div>

            <div class="bulk-card">
                <div><b>All Endpoints Hub</b><br><small style="color:var(--text-muted)">Single click copy for apps</small></div>
                <button class="btn-bulk" onclick="copyAll('android')">Copy All (Android)</button>
                <button class="btn-bulk" style="color:#ff55a3;border-color:#ff55a3;" onclick="copyAll('web')">Copy All (Web)</button>
            </div>
        </div>

        <script>
            function copyAll(target) {
                const fields = document.querySelectorAll('.ep-field');
                const list = [];
                fields.forEach(input => {
                    list.push(target === 'android' ? input.value : window.location.origin + input.value);
                });
                navigator.clipboard.writeText(list.join('\\n')).then(() => {
                    const t = document.getElementById('toast');
                    t.innerText = "All " + target.toUpperCase() + " Endpoints Copied!";
                    t.style.display = 'block';
                    setTimeout(() => t.style.display = 'none', 1600);
                });
            }
            function closeTest(k) { document.getElementById('tester-' + k).style.display = 'none'; }
            function runInlineTest(k, id) {
                const path = document.getElementById(id).value;
                const tester = document.getElementById('tester-' + k);
                const jsonBox = document.getElementById('json-' + k);
                tester.style.display = 'block';
                jsonBox.innerText = 'Requesting ' + path + '...';
                fetch(path).then(r => r.json()).then(d => {
                    jsonBox.innerText = JSON.stringify(d, null, 2);
                }).catch(e => { jsonBox.innerText = 'Error: ' + e; });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_page)

# --- 1. HOME ---
@app.route("/home", methods=["GET"])
def home():
    langs = request.args.get("languages", "hindi,bhojpuri,haryanvi")
    data = fetch_jio({"__call": "webapi.getLaunchData", "languages": langs})
    for section in ["new_albums", "top_playlists", "new_trending", "charts"]:
        if section in data and isinstance(data[section], list):
            for item in data[section]:
                if "image" in item:
                    item["image"] = format_image(item.get("image", ""))
    return jsonify({
        "status": "success",
        "code": 200,
        "languages": langs.split(","),
        "new_trending": data.get("new_trending", []),
        "top_playlists": data.get("top_playlists", []),
        "new_albums": data.get("new_albums", []),
        "charts": data.get("charts", [])
    }), 200

# --- 2. SEARCH SONGS (SMART CLOUD FALLBACK) ---
@app.route("/search", methods=["GET"])
def search_songs():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)

    # 1. Primary Direct Song Search
    data = fetch_jio({"__call": "search.getResults", "q": query, "p": page, "n": limit})
    results = [format_song(s) for s in data.get("results", [])]

    # 2. Cloud Fallback: Agar results empty aate hain toh autocomplete engine use karein
    if not results:
        auto_data = fetch_jio({"__call": "autocomplete.get", "query": query})
        songs_data = auto_data.get("songs", {}).get("data", [])
        for s in songs_data:
            results.append({
                "id": s.get("id"),
                "title": s.get("title", "").replace("&quot;", '"').replace("&amp;", "&"),
                "subtitle": s.get("description", ""),
                "type": "song",
                "album": s.get("more_info", {}).get("album", ""),
                "year": s.get("more_info", {}).get("year", ""),
                "image": format_image(s.get("image", "")),
                "download_url": decrypt_url(s.get("more_info", {}).get("encrypted_media_url", "")) if s.get("more_info", {}).get("encrypted_media_url") else {}
            })

    return jsonify({"status": "success", "code": 200, "total": len(results), "results": results}), 200

# --- 3. AUTOCOMPLETE ---
@app.route("/search/all", methods=["GET"])
def search_all():
    query = request.args.get("query", "")
    data = fetch_jio({"__call": "autocomplete.get", "query": query})
    return jsonify({"status": "success", "code": 200, "data": data}), 200

# --- 4. SONG DETAILS ---
@app.route("/song", methods=["GET"])
def song():
    song_id = request.args.get("id", "")
    song_data = resolve_song_data(song_id)
    if song_data:
        return jsonify({"status": "success", "code": 200, "data": format_song(song_data)}), 200
    return jsonify({"status": "error", "code": 404, "message": "Song not found"}), 404

# --- 5. ALBUM DETAILS ---
@app.route("/album", methods=["GET"])
def album():
    album_id = request.args.get("id", "")
    data = fetch_jio({"__call": "content.getAlbumDetails", "albumid": album_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Album not found"}), 404

# --- 6. PLAYLIST DETAILS ---
@app.route("/playlist", methods=["GET"])
def playlist():
    playlist_id = request.args.get("id", "")
    data = fetch_jio({"__call": "playlist.getDetails", "listid": playlist_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Playlist not found"}), 404

# --- 7. LYRICS ---
@app.route("/lyrics", methods=["GET"])
def lyrics():
    song_id = request.args.get("id", "")
    song_info = resolve_song_data(song_id)
    lyrics_id = song_id
    if song_info:
        lyrics_id = song_info.get("more_info", {}).get("lyrics_id", song_info.get("id", song_id))

    data = fetch_jio({"__call": "lyrics.getLyrics", "lyrics_id": lyrics_id})
    if data and "lyrics" in data:
        clean_lyrics = data.get("lyrics", "").replace("<br>", "\n").replace("<br/>", "\n").replace("&amp;", "&")
        return jsonify({"status": "success", "code": 200, "has_lyrics": True, "lyrics": clean_lyrics}), 200
    return jsonify({"status": "error", "code": 404, "message": "Lyrics unavailable"}), 404

# 24/7 Cloud Port Runner
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
