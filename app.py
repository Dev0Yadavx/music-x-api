import base64
import os
import re
import requests
from flask import Flask, request, jsonify, render_template_string
from Crypto.Cipher import DES

app = Flask(__name__)

BASE_URL = "https://www.jiosaavn.com/api.php"
DES_KEY = b"38346591"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9"
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
    params.update({"_format": "json", "_marker": "0", "api_version": "4", "ctx": "web6dot0"})
    res = requests.get(BASE_URL, params=params, headers=DEFAULT_HEADERS)
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

@app.route("/", methods=["GET"])
def index():
    html_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Music x Api Docs</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --pink: #ff2e93;
                --yellow: #ffd000;
                --green-neon: #39ff14;
                --pink-glow: rgba(255, 46, 147, 0.4);
                --yellow-glow: rgba(255, 208, 0, 0.35);
                --gradient-py: linear-gradient(135deg, #ff2e93 0%, #ffd000 100%);
                --bg: #07040a;
                --glass-bg: rgba(22, 12, 28, 0.65);
                --glass-border: rgba(255, 255, 255, 0.12);
                --text-main: #f8fafc;
                --text-muted: #cbd5e1;
                --code-bg: #030205;
                --success: #10b981;
                --error: #ef4444;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body {
                background: var(--bg);
                color: var(--text-main);
                padding: 20px 14px;
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(255, 46, 147, 0.16) 0%, transparent 45%),
                    radial-gradient(circle at 90% 80%, rgba(255, 208, 0, 0.12) 0%, transparent 45%);
                background-attachment: fixed;
            }
            .container { max-width: 900px; margin: 0 auto; }
            header {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(24px) saturate(180%);
                border-radius: 20px;
                padding: 22px;
                margin-bottom: 22px;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
                position: relative;
                overflow: hidden;
            }
            header::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; height: 3px;
                background: var(--gradient-py);
            }
            h1 {
                font-size: 26px;
                font-weight: 800;
                letter-spacing: -0.5px;
                background: var(--gradient-py);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .cards-list { display: flex; flex-direction: column; gap: 14px; }
            .card {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(18px);
                border-radius: 16px;
                padding: 16px 18px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
                transition: transform 0.25s ease, border-color 0.25s ease;
            }
            .card:hover {
                border-color: rgba(255, 208, 0, 0.4);
                transform: translateY(-2px);
            }
            .card-meta {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 12px;
            }
            .card-title-box { display: flex; align-items: center; gap: 10px; }
            .method-badge {
                background: var(--gradient-py);
                color: #0b0710;
                font-size: 10.5px;
                font-weight: 800;
                padding: 3px 8px;
                border-radius: 6px;
            }
            .card-title { font-size: 14.5px; font-weight: 700; color: #ffffff; }
            .card-tag {
                font-size: 11px;
                font-weight: 600;
                color: var(--yellow);
                background: rgba(255, 208, 0, 0.1);
                border: 1px solid rgba(255, 208, 0, 0.25);
                padding: 3px 10px;
                border-radius: 20px;
            }
            .input-wrapper {
                display: flex;
                align-items: center;
                gap: 8px;
                background: var(--code-bg);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 6px 10px;
            }
            .input-wrapper input {
                flex: 1;
                background: transparent;
                border: none;
                color: var(--yellow);
                font-family: ui-monospace, monospace;
                font-size: 13px;
                font-weight: 500;
                outline: none;
                width: 100%;
            }
            .btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
            }
            .btn-test {
                background: var(--gradient-py);
                color: #0b0710;
                border: none;
                font-weight: 800;
            }
            .inline-tester {
                display: none;
                margin-top: 14px;
                border-top: 1px dashed rgba(255, 255, 255, 0.15);
                padding-top: 12px;
            }
            .tester-status-bar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            .status-tag-group { display: flex; align-items: center; gap: 8px; }
            .status-tag {
                font-size: 11.5px;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 6px;
            }
            .status-200 { background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.4); }
            .status-err { background: rgba(239, 68, 68, 0.2); color: var(--error); border: 1px solid rgba(239, 68, 68, 0.4); }
            .response-time { font-size: 11px; color: var(--text-muted); font-family: monospace; }
            .btn-close-test {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #fff;
                padding: 3px 9px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                cursor: pointer;
            }
            .json-viewer {
                background: #030105;
                border: 1px solid rgba(57, 255, 20, 0.25);
                border-radius: 10px;
                padding: 12px;
                max-height: 280px;
                overflow-y: auto;
                font-family: ui-monospace, monospace;
                font-size: 12px;
                color: var(--green-neon);
                white-space: pre-wrap;
                word-break: break-all;
            }
            .bulk-copy-card {
                background: var(--glass-bg);
                border: 1px solid rgba(255, 208, 0, 0.3);
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 18px 20px;
                margin-top: 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 14px;
            }
            .bulk-title { font-size: 15px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }
            .bulk-subtitle { font-size: 12px; color: var(--text-muted); }
            .bulk-buttons-group { display: flex; gap: 10px; flex-wrap: wrap; }
            .btn-bulk {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 9px 16px;
                border-radius: 10px;
                font-size: 12.5px;
                font-weight: 700;
                cursor: pointer;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            .btn-bulk-android {
                background: rgba(57, 255, 20, 0.1);
                color: var(--green-neon);
                border-color: rgba(57, 255, 20, 0.35);
            }
            .btn-bulk-web {
                background: rgba(255, 46, 147, 0.12);
                color: #ff55a3;
                border-color: rgba(255, 46, 147, 0.35);
            }
            .styled-divider {
                border: none;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255, 46, 147, 0.5), rgba(255, 208, 0, 0.5), transparent);
                margin: 28px 0 20px;
            }
            .dev-container {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 14px;
            }
            .dev-profile { display: flex; align-items: center; gap: 12px; }
            .dev-avatar-wrapper { position: relative; width: 44px; height: 44px; }
            .dev-avatar {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                border: 2px solid var(--yellow);
                object-fit: cover;
            }
            .fire-badge { position: absolute; bottom: -2px; right: -2px; font-size: 13px; }
            .dev-text { display: flex; flex-direction: column; gap: 2px; }
            .dev-label { font-size: 11px; font-weight: 700; color: var(--pink); text-transform: uppercase; }
            .dev-name { font-size: 13.5px; font-weight: 800; color: #fff; }
            .dev-social-links { display: flex; gap: 10px; }
            .social-btn {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #000;
                color: #fff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 7px 13px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 700;
                text-decoration: none;
            }
            .social-btn svg { width: 15px; height: 15px; fill: #fff; }
            .footer-copyright {
                text-align: center;
                padding: 22px 10px 14px;
                font-size: 12px;
                color: var(--text-muted);
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .heart-anim { display: inline-block; color: var(--pink); animation: heartBeat 1.3s infinite; }
            @keyframes heartBeat {
                0%, 100% { transform: scale(1); }
                28% { transform: scale(1.3); }
            }
            .toast {
                position: fixed;
                top: 24px;
                right: 24px;
                background: var(--gradient-py);
                color: #0b0710;
                font-size: 12.5px;
                font-weight: 800;
                padding: 9px 16px;
                border-radius: 10px;
                display: none;
                z-index: 9999;
            }
            svg { width: 14px; height: 14px; flex-shrink: 0; fill: currentColor; }
        </style>
    </head>
    <body>
        <div class="toast" id="toast">Copied to Clipboard!</div>
        <div class="container">
            <header>
                <h1>
                    <svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
                    Music x Api Docs
                </h1>
            </header>

            <div class="cards-list">
                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Home Feed (Hindi, Bhojpuri, Haryanvi)</span></div>
                        <span class="card-tag">Regional Collections</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-home" value="/home?languages=hindi,bhojpuri,haryanvi" readonly>
                        <button class="btn btn-test" onclick="runInlineTest('home', 'url-home')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-home">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-home">FETCHING...</span><span class="response-time" id="time-home">0ms</span></div><button class="btn-close-test" onclick="closeTest('home')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-home"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Trending & Charts Exclusive</span></div>
                        <span class="card-tag">Viral Modules</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-trending" value="/trending?languages=hindi,bhojpuri,haryanvi" readonly>
                        <button class="btn btn-test" onclick="runInlineTest('trending', 'url-trending')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-trending">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-trending">FETCHING...</span><span class="response-time" id="time-trending">0ms</span></div><button class="btn-close-test" onclick="closeTest('trending')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-trending"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Search Autocomplete (Instant)</span></div>
                        <span class="card-tag">Predictive Search</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-auto" value="/search/all?query=pawan singh">
                        <button class="btn btn-test" onclick="runInlineTest('auto', 'url-auto')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-auto">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-auto">FETCHING...</span><span class="response-time" id="time-auto">0ms</span></div><button class="btn-close-test" onclick="closeTest('auto')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-auto"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Search Songs (320kbps Streams)</span></div>
                        <span class="card-tag">Tracks Search</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-search" value="/search?query=kesariya&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('search', 'url-search')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-search">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-search">FETCHING...</span><span class="response-time" id="time-search">0ms</span></div><button class="btn-close-test" onclick="closeTest('search')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-search"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Search Albums</span></div>
                        <span class="card-tag">Album Query</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-salbum" value="/search/albums?query=ashiqui 2&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('salbum', 'url-salbum')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-salbum">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-salbum">FETCHING...</span><span class="response-time" id="time-salbum">0ms</span></div><button class="btn-close-test" onclick="closeTest('salbum')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-salbum"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Search Playlists</span></div>
                        <span class="card-tag">Playlist Query</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-splaylist" value="/search/playlists?query=bhojpuri dance&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('splaylist', 'url-splaylist')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-splaylist">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-splaylist">FETCHING...</span><span class="response-time" id="time-splaylist">0ms</span></div><button class="btn-close-test" onclick="closeTest('splaylist')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-splaylist"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Song Details & Audio Decrypt</span></div>
                        <span class="card-tag">Direct Media</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-song" value="/song?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('song', 'url-song')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-song">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-song">FETCHING...</span><span class="response-time" id="time-song">0ms</span></div><button class="btn-close-test" onclick="closeTest('song')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-song"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Album Full Details & Tracks</span></div>
                        <span class="card-tag">Album Hub</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-album" value="/album?id=51664531">
                        <button class="btn btn-test" onclick="runInlineTest('album', 'url-album')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-album">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-album">FETCHING...</span><span class="response-time" id="time-album">0ms</span></div><button class="btn-close-test" onclick="closeTest('album')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-album"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Playlist Details & Tracks</span></div>
                        <span class="card-tag">Playlists</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-playlist" value="/playlist?id=1130638706">
                        <button class="btn btn-test" onclick="runInlineTest('playlist', 'url-playlist')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-playlist">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-playlist">FETCHING...</span><span class="response-time" id="time-playlist">0ms</span></div><button class="btn-close-test" onclick="closeTest('playlist')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-playlist"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Artist Profile & Top Hits</span></div>
                        <span class="card-tag">Artist Hub</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-artist" value="/artist?id=459320">
                        <button class="btn btn-test" onclick="runInlineTest('artist', 'url-artist')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-artist">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-artist">FETCHING...</span><span class="response-time" id="time-artist">0ms</span></div><button class="btn-close-test" onclick="closeTest('artist')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-artist"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Lyrics Fetcher</span></div>
                        <span class="card-tag">Synced/Text Lyrics</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-lyrics" value="/lyrics?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('lyrics', 'url-lyrics')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-lyrics">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-lyrics">FETCHING...</span><span class="response-time" id="time-lyrics">0ms</span></div><button class="btn-close-test" onclick="closeTest('lyrics')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-lyrics"></pre>
                    </div>
                </div>

                <div class="card">
                    <div class="card-meta">
                        <div class="card-title-box"><span class="method-badge">GET</span><span class="card-title">Radio / Recommendations Queue</span></div>
                        <span class="card-tag">Autoplay Radio</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-reco" value="/recommendations?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('reco', 'url-reco')">Test</button>
                    </div>
                    <div class="inline-tester" id="tester-reco">
                        <div class="tester-status-bar"><div class="status-tag-group"><span class="status-tag" id="status-reco">FETCHING...</span><span class="response-time" id="time-reco">0ms</span></div><button class="btn-close-test" onclick="closeTest('reco')">✕ Close</button></div>
                        <pre class="json-viewer" id="json-reco"></pre>
                    </div>
                </div>
            </div>

            <div class="bulk-copy-card">
                <div class="bulk-text">
                    <div class="bulk-title">All Endpoints Single Copy Hub</div>
                    <span class="bulk-subtitle">One-click copy for Android App dev & Web Integration</span>
                </div>
                <div class="bulk-buttons-group">
                    <button class="btn-bulk btn-bulk-android" onclick="copyAllEndpoints('android')">Copy All (Android)</button>
                    <button class="btn-bulk btn-bulk-web" onclick="copyAllEndpoints('web')">Copy All (Web)</button>
                </div>
            </div>

            <hr class="styled-divider">

            <div class="dev-container">
                <div class="dev-profile">
                    <div class="dev-avatar-wrapper">
                        <img src="https://avatars.githubusercontent.com/u/257059002?v=4" alt="Developer" class="dev-avatar">
                        <span class="fire-badge">🔥</span>
                    </div>
                    <div class="dev-text">
                        <span class="dev-label">developer:-</span>
                        <span class="dev-name">—͟͞͞ 𝙔ᴀᴅᴀᴠ&lt;\&gt;x- 🇮🇳𒌋ᥫ᭡</span>
                    </div>
                </div>
                <div class="dev-social-links">
                    <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-btn">Telegram</a>
                    <a href="https://github.com/Dev0Yadavx" target="_blank" class="social-btn">GitHub</a>
                </div>
            </div>

            <hr class="styled-divider">

            <footer class="footer-copyright">
                <div>All Copyrights © reserved Music x</div>
                <div>Made with <span class="heart-anim">❤️</span> by —͟͞͞ 𝙔ᴀᴅᴀᴠ&lt;\&gt;x- 🇮🇳𒌋ᥫ᭡</div>
            </footer>
        </div>

        <script>
            function copyAllEndpoints(target) {
                const fields = document.querySelectorAll('.ep-field');
                const list = [];
                const origin = window.location.origin;
                fields.forEach(input => {
                    if (target === 'android') {
                        list.push(input.value);
                    } else {
                        list.push(origin + input.value);
                    }
                });
                const textToCopy = list.join('\\n');
                const label = target === 'android' ? 'All Endpoints Copied (Android Paths)!' : 'All Endpoints Copied (Web URLs)!';
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(textToCopy).then(() => showToast(label));
                } else {
                    const temp = document.createElement("textarea");
                    temp.value = textToCopy;
                    document.body.appendChild(temp);
                    temp.select();
                    document.execCommand("copy");
                    document.body.removeChild(temp);
                    showToast(label);
                }
            }

            function showToast(msg) {
                const toast = document.getElementById('toast');
                toast.innerText = msg;
                toast.style.display = 'block';
                setTimeout(() => toast.style.display = 'none', 1600);
            }

            function closeTest(key) {
                document.getElementById('tester-' + key).style.display = 'none';
            }

            function runInlineTest(key, inputId) {
                const path = document.getElementById(inputId).value;
                const tester = document.getElementById('tester-' + key);
                const statusTag = document.getElementById('status-' + key);
                const timeTag = document.getElementById('time-' + key);
                const jsonBox = document.getElementById('json-' + key);

                tester.style.display = 'block';
                statusTag.className = 'status-tag';
                statusTag.innerText = 'WAITING...';
                jsonBox.innerText = 'Requesting ' + path + ' ...';

                const startTime = performance.now();
                fetch(path)
                    .then(response => {
                        const duration = Math.round(performance.now() - startTime);
                        timeTag.innerText = duration + 'ms';
                        if (response.ok) {
                            statusTag.className = 'status-tag status-200';
                            statusTag.innerText = '200 OK';
                        } else {
                            statusTag.className = 'status-tag status-err';
                            statusTag.innerText = response.status + ' ERROR';
                        }
                        return response.json();
                    })
                    .then(data => {
                        jsonBox.innerText = JSON.stringify(data, null, 2);
                    })
                    .catch(err => {
                        const duration = Math.round(performance.now() - startTime);
                        timeTag.innerText = duration + 'ms';
                        statusTag.className = 'status-tag status-err';
                        statusTag.innerText = 'FAILED';
                        jsonBox.innerText = 'Network error: ' + err;
                    });
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
        "charts": data.get("charts", []),
        "radio": data.get("radio", [])
    }), 200

# --- 2. TRENDING ---
@app.route("/trending", methods=["GET"])
def trending():
    langs = request.args.get("languages", "hindi,bhojpuri,haryanvi")
    data = fetch_jio({"__call": "webapi.getLaunchData", "languages": langs})
    trending_list = data.get("new_trending", [])
    for item in trending_list:
        if "image" in item:
            item["image"] = format_image(item.get("image", ""))
    return jsonify({
        "status": "success",
        "code": 200,
        "languages": langs.split(","),
        "trending": trending_list,
        "charts": data.get("charts", [])
    }), 200

# --- 3. AUTOCOMPLETE ---
@app.route("/search/all", methods=["GET"])
def search_all():
    query = request.args.get("query", "")
    data = fetch_jio({"__call": "autocomplete.get", "query": query})
    return jsonify({"status": "success", "code": 200, "data": data}), 200

# --- 4. SEARCH SONGS ---
@app.route("/search", methods=["GET"])
def search_songs():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)
    data = fetch_jio({"__call": "search.getResults", "q": query, "p": page, "n": limit})
    results = [format_song(s) for s in data.get("results", [])]
    return jsonify({"status": "success", "code": 200, "total": data.get("total", len(results)), "results": results}), 200

# --- 5. SEARCH ALBUMS ---
@app.route("/search/albums", methods=["GET"])
def search_albums():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)
    data = fetch_jio({"__call": "search.getAlbumResults", "q": query, "p": page, "n": limit})
    results = data.get("results", [])
    for alb in results:
        alb["image"] = format_image(alb.get("image", ""))
    return jsonify({"status": "success", "code": 200, "total": data.get("total", 0), "results": results}), 200

# --- 6. SEARCH PLAYLISTS ---
@app.route("/search/playlists", methods=["GET"])
def search_playlists():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)
    data = fetch_jio({"__call": "search.getPlaylistResults", "q": query, "p": page, "n": limit})
    results = data.get("results", [])
    for ply in results:
        ply["image"] = format_image(ply.get("image", ""))
    return jsonify({"status": "success", "code": 200, "total": data.get("total", 0), "results": results}), 200

# --- 7. SONG DETAILS ---
@app.route("/song", methods=["GET"])
def song():
    song_id = request.args.get("id", "")
    song_data = resolve_song_data(song_id)
    if song_data:
        return jsonify({"status": "success", "code": 200, "data": format_song(song_data)}), 200
    return jsonify({"status": "error", "code": 404, "message": "Song not found"}), 404

# --- 8. ALBUM DETAILS ---
@app.route("/album", methods=["GET"])
def album():
    album_id = request.args.get("id", "")
    data = fetch_jio({"__call": "content.getAlbumDetails", "albumid": album_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Album not found"}), 404

# --- 9. PLAYLIST DETAILS ---
@app.route("/playlist", methods=["GET"])
def playlist():
    playlist_id = request.args.get("id", "")
    data = fetch_jio({"__call": "playlist.getDetails", "listid": playlist_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Playlist not found"}), 404

# --- 10. ARTIST DETAILS ---
@app.route("/artist", methods=["GET"])
def artist():
    artist_id = request.args.get("id", "")
    data = fetch_jio({"__call": "artist.getArtistPageDetails", "artistId": artist_id, "n": 20})
    if data:
        if "topSongs" in data:
            data["topSongs"] = [format_song(s) for s in data["topSongs"]]
        if "image" in data:
            data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Artist not found"}), 404

# --- 11. LYRICS ENDPOINT ---
@app.route("/lyrics", methods=["GET"])
def lyrics():
    song_id = request.args.get("id", "")
    lyrics_id = song_id
    song_info = resolve_song_data(song_id)
    if song_info:
        lyrics_id = song_info.get("more_info", {}).get("lyrics_id", song_info.get("id", song_id))

    data = fetch_jio({"__call": "lyrics.getLyrics", "lyrics_id": lyrics_id})
    if data and "lyrics" in data:
        clean_lyrics = data.get("lyrics", "").replace("<br>", "\n").replace("<br/>", "\n").replace("&amp;", "&")
        return jsonify({
            "status": "success",
            "code": 200,
            "has_lyrics": True,
            "lyrics": clean_lyrics,
            "snippet": data.get("snippet", ""),
            "copyright": data.get("lyrics_copyright", "")
        }), 200

    return jsonify({"status": "error", "code": 404, "has_lyrics": False, "message": "Lyrics unavailable for this track"}), 404

# --- 12. RECOMMENDATIONS ---
@app.route("/recommendations", methods=["GET"])
def recommendations():
    song_id = request.args.get("id", "")
    target_pid = song_id
    song_info = resolve_song_data(song_id)
    if song_info and "id" in song_info:
        target_pid = song_info["id"]

    data = fetch_jio({"__call": "reco.getreco", "pid": target_pid})
    songs = [format_song(s) for s in data] if isinstance(data, list) else []
    return jsonify({"status": "success", "code": 200, "results": songs}), 200

# CLOUD 24/7 DYNAMIC PORT RUNNER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
