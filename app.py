import base64
import os
import re
import requests
from flask import Flask, request, jsonify, render_template_string
from Crypto.Cipher import DES

app = Flask(__name__)

BASE_URL = "https://www.jiosaavn.com/api.php"
DES_KEY = b"38346591"

# Indian Geo-Spoofing & Regional Cookies for Cloud Hosting
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Referer": "https://www.jiosaavn.com/",
    "Origin": "https://www.jiosaavn.com",
    "X-Forwarded-For": "49.37.0.1",
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
    params.update({"_format": "json", "_marker": "0", "api_version": "4", "ctx": "web6dot0"})
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

# --- ROOT API DOCS & TEST CONSOLE ---
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
                -webkit-backdrop-filter: blur(24px) saturate(180%);
                border-radius: 20px;
                padding: 22px;
                margin-bottom: 22px;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.12);
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
                backdrop-filter: blur(18px) saturate(160%);
                -webkit-backdrop-filter: blur(18px) saturate(160%);
                border-radius: 16px;
                padding: 16px 18px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08);
                transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            }
            .card:hover {
                border-color: rgba(255, 208, 0, 0.4);
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.5), 0 0 16px var(--pink-glow);
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
                padding: 5px 8px;
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
                background: rgba(255, 255, 255, 0.08);
                color: var(--text-main);
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
            }
            .btn:hover { background: rgba(255, 255, 255, 0.16); }
            .btn:active { transform: scale(0.95); }
            .btn-test {
                background: var(--gradient-py);
                color: #0b0710;
                border: none;
                font-weight: 800;
                box-shadow: 0 4px 14px var(--pink-glow);
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
                display: inline-flex;
                align-items: center;
                gap: 6px;
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
            .btn-close-test:hover { background: rgba(239, 68, 68, 0.3); color: #fca5a5; }

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

            /* --- ALL ENDPOINTS SINGLE COPY DOCK --- */
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }
            .bulk-text { display: flex; flex-direction: column; gap: 3px; }
            .bulk-title { font-size: 15px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }
            .bulk-subtitle { font-size: 12px; color: var(--text-muted); }
            
            .bulk-buttons-group {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }
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
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .btn-bulk:active { transform: scale(0.96); }
            .btn-bulk-android {
                background: rgba(57, 255, 20, 0.1);
                color: var(--green-neon);
                border-color: rgba(57, 255, 20, 0.35);
            }
            .btn-bulk-android:hover {
                background: rgba(57, 255, 20, 0.2);
                box-shadow: 0 0 16px rgba(57, 255, 20, 0.3);
            }
            .btn-bulk-web {
                background: rgba(255, 46, 147, 0.12);
                color: #ff55a3;
                border-color: rgba(255, 46, 147, 0.35);
            }
            .btn-bulk-web:hover {
                background: rgba(255, 46, 147, 0.22);
                box-shadow: 0 0 16px var(--pink-glow);
            }

            /* --- FOOTER & DEVELOPER SECTION --- */
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }

            .dev-profile { display: flex; align-items: center; gap: 12px; }
            .dev-avatar-wrapper { position: relative; width: 44px; height: 44px; }
            .dev-avatar {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                border: 2px solid var(--yellow);
                object-fit: cover;
                box-shadow: 0 0 14px var(--pink-glow);
            }
            .fire-badge { position: absolute; bottom: -2px; right: -2px; font-size: 13px; filter: drop-shadow(0 0 4px #ff5722); }
            .dev-text { display: flex; flex-direction: column; gap: 2px; }
            .dev-label { font-size: 11px; font-weight: 700; color: var(--pink); text-transform: uppercase; letter-spacing: 0.8px; }
            .dev-name { font-size: 13.5px; font-weight: 800; color: #fff; letter-spacing: 0.2px; }
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
                transition: transform 0.2s, border-color 0.2s;
            }
            .social-btn:hover { transform: translateY(-2px); border-color: var(--yellow); }
            .social-btn svg { width: 15px; height: 15px; fill: #fff; }

            .footer-copyright {
                text-align: center;
                padding: 22px 10px 14px;
                font-size: 12px;
                color: var(--text-muted);
                display: flex;
                flex-direction: column;
                gap: 6px;
                align-items: center;
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
                box-shadow: 0 10px 24px var(--pink-glow);
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

                <!-- 1. HOME REGIONAL -->
                <div class="card" id="card-home">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Home Feed (Hindi, Bhojpuri, Haryanvi)</span>
                        </div>
                        <span class="card-tag">Regional Collections</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-home" value="/home?languages=hindi,bhojpuri,haryanvi" readonly>
                        <button class="btn btn-test" onclick="runInlineTest('home', 'url-home')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-home">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-home">FETCHING...</span>
                                <span class="response-time" id="time-home">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('home')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-home"></pre>
                    </div>
                </div>

                <!-- 2. TRENDING -->
                <div class="card" id="card-trending">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Trending & Charts Exclusive</span>
                        </div>
                        <span class="card-tag">Viral Modules</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-trending" value="/trending?languages=hindi,bhojpuri,haryanvi" readonly>
                        <button class="btn btn-test" onclick="runInlineTest('trending', 'url-trending')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-trending">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-trending">FETCHING...</span>
                                <span class="response-time" id="time-trending">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('trending')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-trending"></pre>
                    </div>
                </div>

                <!-- 3. SEARCH AUTOCOMPLETE -->
                <div class="card" id="card-auto">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Search Autocomplete (Instant)</span>
                        </div>
                        <span class="card-tag">Predictive Search</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-auto" value="/search/all?query=pawan singh">
                        <button class="btn btn-test" onclick="runInlineTest('auto', 'url-auto')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-auto">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-auto">FETCHING...</span>
                                <span class="response-time" id="time-auto">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('auto')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-auto"></pre>
                    </div>
                </div>

                <!-- 4. SEARCH SONGS -->
                <div class="card" id="card-search">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Search Songs (320kbps Streams)</span>
                        </div>
                        <span class="card-tag">Tracks Search</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-search" value="/search?query=kesariya&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('search', 'url-search')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-search">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-search">FETCHING...</span>
                                <span class="response-time" id="time-search">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('search')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-search"></pre>
                    </div>
                </div>

                <!-- 5. SEARCH ALBUMS -->
                <div class="card" id="card-salbum">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Search Albums</span>
                        </div>
                        <span class="card-tag">Album Query</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-salbum" value="/search/albums?query=ashiqui 2&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('salbum', 'url-salbum')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-salbum">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-salbum">FETCHING...</span>
                                <span class="response-time" id="time-salbum">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('salbum')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-salbum"></pre>
                    </div>
                </div>

                <!-- 6. SEARCH PLAYLISTS -->
                <div class="card" id="card-splaylist">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Search Playlists</span>
                        </div>
                        <span class="card-tag">Playlist Query</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-splaylist" value="/search/playlists?query=bhojpuri dance&page=1&limit=5">
                        <button class="btn btn-test" onclick="runInlineTest('splaylist', 'url-splaylist')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-splaylist">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-splaylist">FETCHING...</span>
                                <span class="response-time" id="time-splaylist">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('splaylist')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-splaylist"></pre>
                    </div>
                </div>

                <!-- 7. SONG DETAILS -->
                <div class="card" id="card-song">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Song Details & Audio Decrypt</span>
                        </div>
                        <span class="card-tag">Direct Media</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-song" value="/song?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('song', 'url-song')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-song">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-song">FETCHING...</span>
                                <span class="response-time" id="time-song">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('song')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-song"></pre>
                    </div>
                </div>

                <!-- 8. ALBUM DETAILS -->
                <div class="card" id="card-album">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Album Full Details & Tracks</span>
                        </div>
                        <span class="card-tag">Album Hub</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-album" value="/album?id=51664531">
                        <button class="btn btn-test" onclick="runInlineTest('album', 'url-album')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-album">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-album">FETCHING...</span>
                                <span class="response-time" id="time-album">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('album')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-album"></pre>
                    </div>
                </div>

                <!-- 9. PLAYLIST DETAILS -->
                <div class="card" id="card-playlist">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Playlist Details & Tracks</span>
                        </div>
                        <span class="card-tag">Playlists</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-playlist" value="/playlist?id=1130638706">
                        <button class="btn btn-test" onclick="runInlineTest('playlist', 'url-playlist')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-playlist">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-playlist">FETCHING...</span>
                                <span class="response-time" id="time-playlist">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('playlist')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-playlist"></pre>
                    </div>
                </div>

                <!-- 10. ARTIST DETAILS -->
                <div class="card" id="card-artist">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Artist Profile & Top Hits</span>
                        </div>
                        <span class="card-tag">Artist Hub</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-artist" value="/artist?id=459320">
                        <button class="btn btn-test" onclick="runInlineTest('artist', 'url-artist')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-artist">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-artist">FETCHING...</span>
                                <span class="response-time" id="time-artist">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('artist')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-artist"></pre>
                    </div>
                </div>

                <!-- 11. LYRICS -->
                <div class="card" id="card-lyrics">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Lyrics Fetcher</span>
                        </div>
                        <span class="card-tag">Synced/Text Lyrics</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-lyrics" value="/lyrics?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('lyrics', 'url-lyrics')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-lyrics">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-lyrics">FETCHING...</span>
                                <span class="response-time" id="time-lyrics">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('lyrics')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-lyrics"></pre>
                    </div>
                </div>

                <!-- 12. RECOMMENDATIONS -->
                <div class="card" id="card-reco">
                    <div class="card-meta">
                        <div class="card-title-box">
                            <span class="method-badge">GET</span>
                            <span class="card-title">Radio / Recommendations Queue</span>
                        </div>
                        <span class="card-tag">Autoplay Radio</span>
                    </div>
                    <div class="input-wrapper">
                        <input type="text" class="ep-field" id="url-reco" value="/recommendations?id=c9_7sW8q">
                        <button class="btn btn-test" onclick="runInlineTest('reco', 'url-reco')">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Test
                        </button>
                    </div>
                    <div class="inline-tester" id="tester-reco">
                        <div class="tester-status-bar">
                            <div class="status-tag-group">
                                <span class="status-tag" id="status-reco">FETCHING...</span>
                                <span class="response-time" id="time-reco">0ms</span>
                            </div>
                            <button class="btn-close-test" onclick="closeTest('reco')">✕ Close</button>
                        </div>
                        <pre class="json-viewer" id="json-reco"></pre>
                    </div>
                </div>

            </div>

            <!-- ALL ENDPOINTS SINGLE COPY DOCK -->
            <div class="bulk-copy-card">
                <div class="bulk-text">
                    <div class="bulk-title">
                        <svg viewBox="0 0 24 24" style="fill: var(--yellow);"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                        All Endpoints Single Copy Hub
                    </div>
                    <span class="bulk-subtitle">One-click copy for Android App dev & Web Integration</span>
                </div>
                <div class="bulk-buttons-group">
                    <button class="btn-bulk btn-bulk-android" onclick="copyAllEndpoints('android')">
                        <svg viewBox="0 0 24 24"><path d="M6 18c0 .55.45 1 1 1h1v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h2v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h1c.55 0 1-.45 1-1V8H6v10zM3.5 8C2.67 8 2 8.67 2 9.5v7c0 .83.67 1.5 1.5 1.5S5 17.33 5 16.5v-7C5 8.67 4.33 8 3.5 8zm17 0c-.83 0-1.5.67-1.5 1.5v7c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5v-7c0-.83-.67-1.5-1.5-1.5zm-4.97-4.84l1.3-1.3c.2-.2.2-.51 0-.71-.2-.2-.51-.2-.71 0l-1.48 1.48C13.85 2.23 12.95 2 12 2c-.96 0-1.86.23-2.66.63L7.85.99c-.2-.2-.51-.2-.71 0-.2.2-.2.51 0 .71l1.31 1.31C6.97 4.26 6 6.01 6 8h12c0-1.99-.97-3.75-2.47-4.84zM10 5H9V4h1v1zm5 0h-1V4h1v1z"/></svg>
                        Copy All (Android)
                    </button>
                    <button class="btn-bulk btn-bulk-web" onclick="copyAllEndpoints('web')">
                        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        Copy All (Web)
                    </button>
                </div>
            </div>

            <!-- TOP DIVIDER -->
            <hr class="styled-divider">

            <!-- DEVELOPER SECTION -->
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
                    <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-btn">
                        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
                        Telegram
                    </a>

                    <a href="https://github.com/Dev0Yadavx" target="_blank" class="social-btn">
                        <svg viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
                        GitHub
                    </a>
                </div>
            </div>

            <!-- BOTTOM DIVIDER -->
            <hr class="styled-divider">

            <!-- COPYRIGHT FOOTER -->
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
                        jsonBox.innerText = 'Network error or bad response: ' + err;
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

# --- 4. SEARCH SONGS (WITH CLOUD FALLBACK) ---
@app.route("/search", methods=["GET"])
def search_songs():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)
    data = fetch_jio({"__call": "search.getResults", "q": query, "p": page, "n": limit})
    results = [format_song(s) for s in data.get("results", [])]
    
    # Cloud foreign IP fallback
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
                "album_id": "",
                "primary_artists": [],
                "year": s.get("more_info", {}).get("year", ""),
                "duration": "0",
                "language": "",
                "has_lyrics": "false",
                "lyrics_id": s.get("id"),
                "image": format_image(s.get("image", "")),
                "download_url": decrypt_url(s.get("more_info", {}).get("encrypted_media_url", "")) if s.get("more_info", {}).get("encrypted_media_url") else {}
            })

    return jsonify({"status": "success", "code": 200, "total": len(results), "results": results}), 200

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
