import os
import json
import html
import base64
import requests
from typing import Optional
from Crypto.Cipher import DES
from fastapi import FastAPI, Query, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Music X API",
    description="Music x Api Best Music Api all end",
    version="5.0.0",
    docs_url="/swagger",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://www.jiosaavn.com/api.php"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.jiosaavn.com/',
    'Accept': '*/*',
    'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
    'X-Forwarded-For': '103.241.226.1',
    'CF-IPCountry': 'IN'
}

def clean_text(text):
    if not text:
        return ""
    return html.unescape(str(text)).replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').strip()

def safe_parse_json(val):
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return None
    return None

def extract_artists(data):
    if not isinstance(data, dict):
        return "Various Artists"
    more = data.get('more_info', {}) if isinstance(data.get('more_info'), dict) else {}
    
    artist_map = more.get('artist_map', {})
    if isinstance(artist_map, str):
        artist_map = safe_parse_json(artist_map) or {}
    if isinstance(artist_map, dict):
        primaries = artist_map.get('primary_artists', [])
        if primaries and isinstance(primaries, list):
            names = [a.get('name') for a in primaries if isinstance(a, dict) and a.get('name')]
            if names:
                return ", ".join(names)

    for key in ['primary_artists', 'singers', 'music', 'artist']:
        val = more.get(key) or data.get(key)
        if val and isinstance(val, str) and val.strip():
            return clean_text(val)

    subtitle = data.get('subtitle') or more.get('subtitle')
    if subtitle and isinstance(subtitle, str) and subtitle.strip():
        return clean_text(subtitle)
        
    return "Various Artists"

def decrypt_raw_url(cipher_text):
    if not cipher_text:
        return None
    try:
        key = b'3834363538333735'
        cipher = DES.new(key, DES.MODE_ECB)
        dec = cipher.decrypt(base64.b64decode(cipher_text))
        pad = dec[-1]
        return dec[:-pad].decode('utf-8')
    except Exception:
        return None

def get_authorized_stream_url(encrypted_url, bitrate='320'):
    if not encrypted_url:
        return None
    try:
        params = {
            '__call': 'song.generateAuthToken',
            'url': encrypted_url,
            'bitrate': str(bitrate),
            'api_version': '4',
            '_format': 'json',
            'ctx': 'web6dot0',
            '_marker': '0'
        }
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=4).json()
        if 'auth_url' in res and res['auth_url']:
            return res['auth_url']
    except Exception:
        pass
    
    raw = decrypt_raw_url(encrypted_url)
    if raw:
        clean = raw.replace('_96.mp4', '').replace('_160.mp4', '').replace('_320.mp4', '')
        return f"{clean}_{bitrate}.mp4"
    return None

def fetch_all_stream_urls(encrypted_url):
    if not encrypted_url:
        return {}
    urls = {}
    for br in ['320', '160', '96']:
        link = get_authorized_stream_url(encrypted_url, br)
        if link:
            if link.startswith("http://"):
                link = link.replace("http://", "https://")
            urls[f"{br}kbps"] = link
    return urls

def format_song(song):
    if not isinstance(song, dict):
        return {}
    more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
    enc_url = more.get('encrypted_media_url') or song.get('encrypted_media_url')
    img = song.get('image') or more.get('image', '')
    
    return {
        "id": song.get('id'),
        "title": clean_text(song.get('title') or song.get('song')),
        "album": clean_text(more.get('album') or song.get('album')),
        "artists": extract_artists(song),
        "year": more.get('year') or song.get('year') or "",
        "duration": int(more.get('duration') or song.get('duration') or 0),
        "language": song.get('language') or more.get('language') or "hindi",
        "has_lyrics": more.get('has_lyrics') == 'true' or song.get('has_lyrics') == 'true',
        "image": {
            "low": img.replace('150x150', '50x50') if img else None,
            "medium": img.replace('150x150', '150x150') if img else None,
            "high": img.replace('150x150', '500x500') if img else None
        },
        "stream_urls": fetch_all_stream_urls(enc_url)
    }

# ----------------- MODERN LIQUID GLASS DOCS UI ----------------- #

DOCS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
  <title>Music X API - Documentation & Live Sandbox</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #050711;
      --glass-bg: rgba(255, 255, 255, 0.04);
      --glass-border: rgba(255, 255, 255, 0.1);
      --glass-shine: rgba(255, 255, 255, 0.2);
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.45);
      --accent-grad: linear-gradient(135deg, #6366f1 0%, #ec4899 50%, #8b5cf6 100%);
      --text: #f8fafc;
      --text-dim: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; padding-bottom: 30px; position: relative; }
    
    .ambient-orb { position: fixed; border-radius: 50%; filter: blur(95px); pointer-events: none; z-index: 0; }
    .orb-1 { width: 380px; height: 380px; background: rgba(99, 102, 241, 0.25); top: -80px; left: -80px; }
    .orb-2 { width: 350px; height: 350px; background: rgba(236, 72, 153, 0.18); bottom: 40px; right: -40px; }

    .liquid-glass {
      background: var(--glass-bg);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border: 1px solid var(--glass-border);
      box-shadow: 0 16px 40px 0 rgba(0, 0, 0, 0.45), inset 0 0 0 1px var(--glass-shine);
      border-radius: 20px;
    }

    .container { width: 100%; max-width: 980px; margin: 0 auto; padding: 24px 16px 20px; position: relative; z-index: 1; }
    header { text-align: center; margin-bottom: 28px; }
    .badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 100px; font-size: 0.75rem; font-weight: 700; color: #a5b4fc; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); margin-bottom: 12px; }
    .title { font-size: clamp(2rem, 6vw, 2.9rem); font-weight: 800; background: linear-gradient(135deg, #fff 40%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { color: #38bdf8; margin-top: 8px; font-size: clamp(0.95rem, 3vw, 1.15rem); font-weight: 600; }

    .base-card { padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 26px; }
    .base-title { font-size: 0.72rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; }
    .base-url { font-family: monospace; font-size: 0.95rem; color: #34d399; font-weight: 600; word-break: break-all; }
    
    .btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 9px 15px; border-radius: 10px; font-size: 0.84rem; font-weight: 600; border: none; cursor: pointer; transition: 0.2s ease; text-decoration: none; }
    .btn-grad { background: var(--accent-grad); color: #fff; box-shadow: 0 4px 18px var(--accent-glow); }
    .btn-ghost { background: rgba(255, 255, 255, 0.06); border: 1px solid var(--glass-border); color: #fff; }
    .btn-test { background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; }

    .endpoints-grid { display: flex; flex-direction: column; gap: 16px; }
    .endpoint-card { padding: 20px; transition: border-color 0.25s; }
    .endpoint-card:hover { border-color: rgba(255, 255, 255, 0.25); }
    .ep-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
    .method-get { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.74rem; }
    .ep-path { font-size: clamp(1rem, 3.5vw, 1.15rem); font-weight: 700; font-family: monospace; color: #fff; }
    .ep-desc { color: var(--text-dim); font-size: 0.88rem; margin-bottom: 12px; }

    .input-control-box { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; background: rgba(0,0,0,0.25); padding: 6px 10px; border-radius: 12px; border: 1px solid var(--glass-border); }
    .input-label { font-size: 0.78rem; font-weight: 700; color: #38bdf8; font-family: monospace; white-space: nowrap; }
    .custom-input { flex: 1; min-width: 0; background: transparent; border: none; color: #fff; outline: none; font-size: 0.88rem; font-weight: 500; }
    
    .url-preview { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); padding: 10px 12px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; gap: 10px; font-family: monospace; font-size: 0.82rem; color: #e2e8f0; flex-wrap: wrap; }
    .url-text { word-break: break-all; flex: 1; min-width: 180px; }
    .action-group { display: flex; gap: 6px; }

    .json-viewer-container { display: none; margin-top: 14px; background: rgba(2, 4, 10, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px; }
    .json-output { max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 0.82rem; line-height: 1.6; color: #a5b4fc; white-space: pre-wrap; word-break: break-all; }

    footer { margin-top: 40px; padding: 24px 16px; text-align: center; border-radius: 20px; }
    .dev-title { font-size: clamp(0.95rem, 3.5vw, 1.15rem); font-weight: 700; margin-bottom: 14px; background: linear-gradient(135deg, #f43f5e, #fb923c, #eab308, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .social-links { display: flex; justify-content: center; gap: 10px; margin-bottom: 16px; }
    .social-badge { display: inline-flex; align-items: center; gap: 6px; background: #000; border: 1px solid rgba(255, 255, 255, 0.15); padding: 8px 14px; border-radius: 10px; color: #fff; text-decoration: none; font-size: 0.82rem; font-weight: 600; }
    .copyright { font-size: 0.8rem; font-weight: 600; background: linear-gradient(135deg, #ec4899, #8b5cf6, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  </style>
</head>
<body>
  <div class="ambient-orb orb-1"></div>
  <div class="ambient-orb orb-2"></div>

  <div class="container">
    <header>
      <div class="badge">✦ HIGH-SPEED ENGINE • 24/7 ONLINE</div>
      <h1 class="title">Music X API</h1>
      <p class="subtitle">Music x Api Best Music Api all end</p>
    </header>

    <div class="base-card liquid-glass">
      <div>
        <div class="base-title">Active Base Host URL</div>
        <div class="base-url" id="baseUrlText">https://...</div>
      </div>
      <button class="btn btn-grad" onclick="navigator.clipboard.writeText(window.location.origin); alert('Base URL Copied!');">Copy Base URL</button>
    </div>

    <div class="endpoints-grid">

      <!-- 1. Daily New Releases (Auto Bhojpuri & Hindi) -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/releases</span>
          </div>
          <span style="font-size:0.75rem; color:#f43f5e; font-weight:700;">★ DAILY AUTO NEW RELEASES</span>
        </div>
        <div class="ep-desc">Auto fetches fresh daily releases. Filter dynamically by language: 'hindi', 'bhojpuri', or 'all'.</div>
        <div class="input-control-box">
          <span class="input-label">?language=</span>
          <input type="text" id="param-releases" class="custom-input" value="bhojpuri" oninput="updateUrl('releases')" placeholder="bhojpuri, hindi, or all" />
        </div>
        <div class="url-preview">
          <span class="url-text" id="url-releases">...</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="executeTest('releases')">Run In UI</button>
            <button class="btn btn-ghost" onclick="copyDynamicUrl('releases')">Copy</button>
          </div>
        </div>
        <div class="json-viewer-container" id="box-releases"><div class="json-output" id="out-releases"></div></div>
      </div>

      <!-- 2. Auto Queue / Similar Songs Engine -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/recommend</span>
          </div>
          <span style="font-size:0.75rem; color:#38bdf8; font-weight:700;">★ AUTO QUEUE & SIMILAR ARTISTS</span>
        </div>
        <div class="ep-desc">Auto recommendation engine for seamless autoplay queue based on current song's artist & genre.</div>
        <div class="input-control-box">
          <span class="input-label">?id=</span>
          <input type="text" id="param-recommend" class="custom-input" value="s_oVd9yZ" oninput="updateUrl('recommend')" placeholder="Track ID..." />
        </div>
        <div class="url-preview">
          <span class="url-text" id="url-recommend">...</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="executeTest('recommend')">Run In UI</button>
            <button class="btn btn-ghost" onclick="copyDynamicUrl('recommend')">Copy</button>
          </div>
        </div>
        <div class="json-viewer-container" id="box-recommend"><div class="json-output" id="out-recommend"></div></div>
      </div>

      <!-- 3. Global Search -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/search</span>
          </div>
          <span style="font-size:0.75rem; color:var(--text-dim);">Search Engine</span>
        </div>
        <div class="ep-desc">Search songs, movie soundtracks, and singers in real time.</div>
        <div class="input-control-box">
          <span class="input-label">?q=</span>
          <input type="text" id="param-search" class="custom-input" value="Pawan Singh" oninput="updateUrl('search')" />
        </div>
        <div class="url-preview">
          <span class="url-text" id="url-search">...</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="executeTest('search')">Run In UI</button>
            <button class="btn btn-ghost" onclick="copyDynamicUrl('search')">Copy</button>
          </div>
        </div>
        <div class="json-viewer-container" id="box-search"><div class="json-output" id="out-search"></div></div>
      </div>

      <!-- 4. Download / Fast Stream -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/download</span>
          </div>
          <span style="font-size:0.75rem; color:var(--text-dim);">320kbps MP3</span>
        </div>
        <div class="ep-desc">Streams & triggers high-speed MP3 download proxy.</div>
        <div class="input-control-box">
          <span class="input-label">?id=</span>
          <input type="text" id="param-download" class="custom-input" value="s_oVd9yZ" oninput="updateUrl('download')" />
        </div>
        <div class="url-preview">
          <span class="url-text" id="url-download">...</span>
          <div class="action-group">
            <a href="#" target="_blank" class="btn btn-test" id="btn-download">Direct Download ↗</a>
            <button class="btn btn-ghost" onclick="copyDynamicUrl('download')">Copy</button>
          </div>
        </div>
      </div>

      <!-- 5. Playlists -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/playlist</span>
          </div>
          <span style="font-size:0.75rem; color:var(--text-dim);">Playlists</span>
        </div>
        <div class="ep-desc">Unpack complete playlist tracks by title query (e.g. Bhojpuri Hits, Hindi Romance).</div>
        <div class="input-control-box">
          <span class="input-label">?q=</span>
          <input type="text" id="param-playlist" class="custom-input" value="Bhojpuri Top 50" oninput="updateUrl('playlist')" />
        </div>
        <div class="url-preview">
          <span class="url-text" id="url-playlist">...</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="executeTest('playlist')">Run In UI</button>
            <button class="btn btn-ghost" onclick="copyDynamicUrl('playlist')">Copy</button>
          </div>
        </div>
        <div class="json-viewer-container" id="box-playlist"><div class="json-output" id="out-playlist"></div></div>
      </div>

    </div>

    <footer class="liquid-glass">
      <div class="dev-title">Dev:BY-—͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
      <div class="social-links">
        <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-badge">Telegram</a>
        <a href="https://github.com/Dev0Yadavx/music-x-api" target="_blank" class="social-badge">GitHub</a>
      </div>
      <div class="copyright">All Copyrights © Music x reserved</div>
    </footer>
  </div>

  <script>
    const origin = window.location.origin;
    document.getElementById('baseUrlText').innerText = origin;

    const routes = {
      'releases': (val) => `/api/releases?language=${encodeURIComponent(val)}&limit=15`,
      'recommend': (val) => `/api/recommend?id=${encodeURIComponent(val)}&limit=10`,
      'search': (val) => `/api/search?q=${encodeURIComponent(val)}&limit=5`,
      'download': (val) => `/api/download?id=${encodeURIComponent(val)}`,
      'playlist': (val) => `/api/playlist?q=${encodeURIComponent(val)}`
    };

    function updateUrl(key) {
      const input = document.getElementById('param-' + key);
      const val = input ? input.value.trim() : '';
      const path = routes[key](val);
      const fullUrl = origin + path;
      
      const preview = document.getElementById('url-' + key);
      if(preview) preview.innerText = fullUrl;

      if(key === 'download') {
        const dlBtn = document.getElementById('btn-download');
        if(dlBtn) dlBtn.href = fullUrl;
      }
    }

    Object.keys(routes).forEach(key => updateUrl(key));

    function copyDynamicUrl(key) {
      const text = document.getElementById('url-' + key).innerText;
      navigator.clipboard.writeText(text);
      alert('Copied URL!');
    }

    async function executeTest(key) {
      const box = document.getElementById('box-' + key);
      const out = document.getElementById('out-' + key);
      const input = document.getElementById('param-' + key);
      const val = input ? input.value.trim() : '';
      const path = routes[key](val);

      box.style.display = 'block';
      out.innerText = '// Engine fetching data...';

      try {
        const res = await fetch(path);
        const data = await res.json();
        out.innerText = JSON.stringify(data, null, 2);
      } catch(err) {
        out.innerText = '// Error: ' + err.message;
      }
    }
  </script>
</body>
</html>
"""

# ----------------- ROUTES ----------------- #

@app.get("/", response_class=HTMLResponse, tags=["Documentation"])
@app.get("/docs", response_class=HTMLResponse, tags=["Documentation"])
def modern_docs():
    return DOCS_HTML

# 1. DAILY NEW RELEASES (AUTO FETCH & FILTER BHOJPURI / HINDI)
@app.get("/api/releases", tags=["Discovery"])
def get_daily_new_releases(language: str = Query("all", description="Language filter: 'hindi', 'bhojpuri', or 'all'"), limit: int = 20):
    lang_clean = language.lower().strip()
    collected_songs = []

    # Method A: Launch Data se latest fresh releases lena
    try:
        res = requests.get(BASE_URL, params={'__call': 'webapi.getLaunchData', '_format': 'json', '_marker': '0', 'api_version': '4', 'ctx': 'web6dot0'}, headers=HEADERS, timeout=7).json()
        new_albums = res.get('new_albums', [])
        
        # Har naye album ke tracks auto unpack karein
        for alb in new_albums[:6]:
            alb_id = alb.get('id')
            if alb_id:
                try:
                    alb_det = requests.get(BASE_URL, params={'__call': 'content.getAlbumDetails', '_format': 'json', '_marker': '0', 'albumid': str(alb_id)}, headers=HEADERS, timeout=4).json()
                    songs = alb_det.get('songs', [])
                    if isinstance(songs, list):
                        for s in songs:
                            s_lang = (s.get('language') or '').lower()
                            if lang_clean == 'all' or lang_clean in s_lang:
                                collected_songs.append(format_song(s))
                except Exception:
                    continue
    except Exception:
        pass

    # Method B: Search fallback for fresh releases
    if len(collected_songs) < 10:
        query_map = {
            'bhojpuri': 'Latest Bhojpuri New Releases 2026',
            'hindi': 'Latest Hindi New Releases 2026',
            'all': 'Latest Indian New Releases 2026'
        }
        target_q = query_map.get(lang_clean, f'Latest {language} New Releases 2026')
        try:
            s_res = requests.get(BASE_URL, params={'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'p': '1', 'n': str(limit), 'q': target_q}, headers=HEADERS, timeout=6).json()
            results = s_res.get('results', [])
            for s in results:
                formatted = format_song(s)
                if not any(x['id'] == formatted['id'] for x in collected_songs):
                    collected_songs.append(formatted)
        except Exception:
            pass

    return {
        "app": "Music X API",
        "status": "success",
        "category": f"Daily New Releases ({language.upper()})",
        "total": len(collected_songs[:limit]),
        "data": collected_songs[:limit]
    }

# 2. AUTO QUEUE & SIMILAR ARTIST RECOMMENDATION ENGINE
@app.get("/api/recommend", tags=["Discovery"])
def get_song_recommendations(id: str = Query(..., description="Currently playing Song ID"), limit: int = 15):
    # Step 1: Current playing song ki details fetch karein
    params = {'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
        current_song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
        if not current_song:
            raise HTTPException(status_code=404, detail="Original song ID not found")
        
        more = current_song.get('more_info', {}) if isinstance(current_song.get('more_info'), dict) else {}
        primary_artist = extract_artists(current_song).split(',')[0].strip()
        song_lang = current_song.get('language') or more.get('language') or 'hindi'
        song_title = clean_text(current_song.get('title') or current_song.get('song'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve current track: {str(e)}")

    recommended_songs = []

    # Step 2: Same Singer / Similar Artist se tracks fetch karein
    if primary_artist and primary_artist != "Various Artists":
        try:
            # Artist ke top charts
            art_res = requests.get(BASE_URL, params={'__call': 'search.getArtistResults', '_format': 'json', '_marker': '0', 'p': '1', 'n': '1', 'q': primary_artist}, headers=HEADERS, timeout=5).json()
            art_list = art_res.get('results', [])
            if art_list:
                art_id = art_list[0].get('artistid') or art_list[0].get('id')
                page_res = requests.get(BASE_URL, params={'__call': 'artist.getArtistPageDetails', '_format': 'json', '_marker': '0', 'artistId': art_id}, headers=HEADERS, timeout=5).json()
                top_songs = page_res.get('topSongs', [])
                if isinstance(top_songs, dict):
                    top_songs = top_songs.get('songs', [])
                for s in top_songs:
                    if s.get('id') != id:
                        recommended_songs.append(format_song(s))
        except Exception:
            pass

    # Step 3: Genre & Language auto-queue fallback
    if len(recommended_songs) < limit:
        try:
            s_res = requests.get(BASE_URL, params={'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'p': '1', 'n': str(limit), 'q': f"Best of {primary_artist} {song_lang}"}, headers=HEADERS, timeout=5).json()
            for s in s_res.get('results', []):
                if s.get('id') != id and not any(x['id'] == s.get('id') for x in recommended_songs):
                    recommended_songs.append(format_song(s))
        except Exception:
            pass

    return {
        "app": "Music X API",
        "status": "success",
        "based_on": {
            "title": song_title,
            "artist": primary_artist,
            "language": song_lang
        },
        "total": len(recommended_songs[:limit]),
        "queue": recommended_songs[:limit]
    }

# 3. FAST STREAMING & DOWNLOAD PROXY
@app.get("/api/download", tags=["Download"])
def stream_or_download_song(id: str = Query(..., description="Track ID"), request: Request = None):
    params = {'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
        song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
        if not song:
            raise HTTPException(status_code=404, detail="Song ID not found")
        
        more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
        enc_url = more.get('encrypted_media_url') or song.get('encrypted_media_url')
        
        stream_url = get_authorized_stream_url(enc_url, '320') or get_authorized_stream_url(enc_url, '160')
        if not stream_url:
            raise HTTPException(status_code=500, detail="Audio stream unavailable")
            
        fwd_headers = {
            'User-Agent': HEADERS['User-Agent'],
            'Referer': 'https://www.jiosaavn.com/'
        }
        range_header = request.headers.get('Range') if request else None
        if range_header:
            fwd_headers['Range'] = range_header

        cdn_resp = requests.get(stream_url, headers=fwd_headers, stream=True, timeout=10)
        
        title = clean_text(song.get('title') or song.get('song') or 'Track')
        artist = extract_artists(song)
        safe_filename = "".join(c for c in f"{title} - {artist}" if c.isalnum() or c in (' ', '_', '-')).strip() or 'track'

        resp_headers = {
            "Content-Disposition": f'inline; filename="{safe_filename}.mp3"',
            "Accept-Ranges": "bytes"
        }
        if 'Content-Range' in cdn_resp.headers:
            resp_headers['Content-Range'] = cdn_resp.headers['Content-Range']
        if 'Content-Length' in cdn_resp.headers:
            resp_headers['Content-Length'] = cdn_resp.headers['Content-Length']

        def iterfile():
            try:
                for chunk in cdn_resp.iter_content(chunk_size=65536):
                    if chunk:
                        yield chunk
            except Exception:
                pass

        return StreamingResponse(
            iterfile(),
            status_code=cdn_resp.status_code,
            media_type="audio/mpeg",
            headers=resp_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. SEARCH
@app.get("/api/search", tags=["Search"])
def search_songs(q: str = Query(..., description="Song name"), page: int = 1, limit: int = 20):
    raw_results = []
    params = {'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'ctx': 'web6dot0', 'p': str(page), 'n': str(limit), 'q': q}
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
        raw_results = r.get('results', [])
    except Exception:
        raw_results = []

    return {
        "app": "Music X API",
        "status": "success",
        "total": len(raw_results),
        "data": [format_song(s) for s in raw_results if isinstance(s, dict)]
    }

# 5. PLAYLISTS
@app.get("/api/playlist", tags=["Playlists"])
def get_playlist(q: Optional[str] = None, id: Optional[str] = None):
    if not q and not id:
        raise HTTPException(status_code=400, detail="Provide either 'q' or 'id'")
    
    list_id = id
    list_token = None

    if q and not list_id:
        try:
            s_res = requests.get(BASE_URL, params={'__call': 'search.getPlaylistResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'p': '1', 'n': '5', 'q': q}, headers=HEADERS, timeout=8).json()
            results = s_res.get('results', []) or s_res.get('data', {}).get('results', [])
            if not results:
                raise HTTPException(status_code=404, detail=f"No playlist found for '{q}'")
            matched = results[0]
            list_id = matched.get('id') or matched.get('listid')
            perma = matched.get('perma_url', '')
            if perma and '/' in perma:
                list_token = perma.rstrip('/').split('/')[-1]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    details_res = None
    if list_id:
        try:
            r = requests.get(BASE_URL, params={'__call': 'playlist.getDetails', '_format': 'json', '_marker': '0', 'api_version': '4', 'listid': str(list_id)}, headers=HEADERS, timeout=8).json()
            if isinstance(r, dict) and (r.get('songs') or r.get('list')):
                details_res = r
        except Exception:
            pass

    if (not details_res or not details_res.get('songs')) and (list_token or list_id):
        token_to_use = list_token or str(list_id)
        try:
            r = requests.get(BASE_URL, params={'__call': 'webapi.get', 'token': token_to_use, 'type': 'playlist', '_format': 'json', '_marker': '0', 'api_version': '4'}, headers=HEADERS, timeout=8).json()
            if isinstance(r, dict) and (r.get('songs') or r.get('list')):
                details_res = r
        except Exception:
            pass

    if not details_res:
        raise HTTPException(status_code=404, detail="Playlist tracks could not be unpacked")

    raw_songs = details_res.get('songs', []) or details_res.get('list', [])
    if isinstance(raw_songs, dict):
        raw_songs = list(raw_songs.values())

    return {
        "app": "Music X API",
        "status": "success",
        "playlist": {
            "id": details_res.get('id') or list_id,
            "title": clean_text(details_res.get('title') or details_res.get('name')),
            "total_tracks": int(details_res.get('list_count') or len(raw_songs)),
            "image": (details_res.get('image') or '').replace('150x150', '500x500')
        },
        "songs": [format_song(s) for s in raw_songs if isinstance(s, dict)]
    }

# 6. SONG DETAILS
@app.get("/api/song", tags=["Streams"])
def get_song(id: str = Query(..., description="Track ID")):
    params = {'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
        song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        return {"app": "Music X API", "status": "success", "data": format_song(song)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. LYRICS
@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Song ID")):
    try:
        res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
        if isinstance(res, dict) and res.get('lyrics'):
            return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    except Exception:
        pass
    return {"app": "Music X API", "status": "success", "has_lyrics": False, "lyrics": "Lyrics unavailable for this track."}
