import os
import json
import html
import base64
import requests
from typing import Optional
from Crypto.Cipher import DES
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Music X API",
    description="High-Speed JioSaavn Music Engine with Liquid Glass Docs",
    version="2.0.0",
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

def decrypt_url(cipher_text):
    if not cipher_text:
        return None
    try:
        key = b'3834363538333735'
        cipher = DES.new(key, DES.MODE_ECB)
        dec = cipher.decrypt(base64.b64decode(cipher_text))
        pad = dec[-1]
        raw_url = dec[:-pad].decode('utf-8')
        clean = raw_url.replace('_96.mp4', '').replace('_160.mp4', '').replace('_320.mp4', '')
        return {
            "96kbps": f"{clean}_96.mp4",
            "160kbps": f"{clean}_160.mp4",
            "320kbps": f"{clean}_320.mp4"
        }
    except Exception:
        return None

def fetch_stream_urls(encrypted_url):
    if not encrypted_url:
        return {}
    local = decrypt_url(encrypted_url)
    if local:
        return local

    links = {}
    for br in ['320', '160', '96']:
        try:
            params = {
                '__call': 'song.generateAuthToken',
                'url': encrypted_url,
                'bitrate': br,
                'api_version': '4',
                '_format': 'json',
                'ctx': 'web6dot0',
                '_marker': '0'
            }
            res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=4).json()
            if 'auth_url' in res:
                links[f"{br}kbps"] = res['auth_url']
        except Exception:
            pass
    return links

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
        "stream_urls": fetch_stream_urls(enc_url)
    }

# ----------------- MODERN LIQUID GLASS DOCS UI ----------------- #

DOCS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Music X API - Documentation</title>
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
      --accent-glow: rgba(99, 102, 241, 0.4);
      --accent-grad: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
      --text: #f8fafc;
      --text-dim: #94a3b8;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; padding-bottom: 60px; position: relative; }
    
    .ambient-orb { position: fixed; border-radius: 50%; filter: blur(100px); pointer-events: none; z-index: 0; }
    .orb-1 { width: 450px; height: 450px; background: rgba(99, 102, 241, 0.25); top: -100px; left: -100px; animation: float 16s infinite alternate ease-in-out; }
    .orb-2 { width: 400px; height: 400px; background: rgba(236, 72, 153, 0.18); bottom: 50px; right: -50px; animation: float 20s infinite alternate ease-in-out; }
    .orb-3 { width: 300px; height: 300px; background: rgba(14, 165, 233, 0.2); top: 40%; left: 35%; animation: float 12s infinite alternate ease-in-out; }
    @keyframes float { 0% { transform: translateY(0) scale(1); } 100% { transform: translateY(50px) scale(1.08); } }

    .liquid-glass {
      background: var(--glass-bg);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border: 1px solid var(--glass-border);
      box-shadow: 0 16px 40px 0 rgba(0, 0, 0, 0.45), inset 0 0 0 1px var(--glass-shine);
      border-radius: 24px;
    }

    .container { max-width: 1000px; margin: 0 auto; padding: 40px 20px; position: relative; z-index: 1; }

    header { text-align: center; margin-bottom: 40px; }
    .badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 100px; font-size: 0.8rem; font-weight: 600; color: #a5b4fc; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); margin-bottom: 16px; }
    .title { font-size: 2.7rem; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(135deg, #fff 40%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { color: var(--text-dim); margin-top: 10px; font-size: 1.05rem; }

    /* Base URL Display Box */
    .base-card { padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; margin-bottom: 36px; }
    .base-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-dim); font-weight: 700; margin-bottom: 4px; }
    .base-url { font-family: monospace; font-size: 1.05rem; color: #38bdf8; font-weight: 600; word-break: break-all; }
    
    .btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 12px; font-size: 0.88rem; font-weight: 600; border: none; cursor: pointer; transition: 0.2s ease; }
    .btn-grad { background: var(--accent-grad); color: #fff; box-shadow: 0 4px 18px var(--accent-glow); }
    .btn-grad:hover { transform: translateY(-2px); box-shadow: 0 6px 24px var(--accent-glow); }
    .btn-ghost { background: rgba(255, 255, 255, 0.06); border: 1px solid var(--glass-border); color: #fff; }
    .btn-ghost:hover { background: rgba(255, 255, 255, 0.12); }

    /* Endpoints Grid */
    .endpoints-grid { display: flex; flex-direction: column; gap: 18px; }
    .endpoint-card { padding: 22px; transition: transform 0.25s, border-color 0.25s; }
    .endpoint-card:hover { transform: translateY(-2px); border-color: rgba(255, 255, 255, 0.22); }
    .ep-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
    .method-get { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.04em; }
    .ep-path { font-size: 1.15rem; font-weight: 700; font-family: monospace; color: #fff; }
    .ep-desc { color: var(--text-dim); font-size: 0.92rem; margin-bottom: 14px; line-height: 1.5; }
    
    .url-preview { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); padding: 12px 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; gap: 12px; font-family: monospace; font-size: 0.88rem; color: #e2e8f0; }
    .url-text { word-break: break-all; }

    .toast { position: fixed; bottom: 24px; right: 24px; background: #10b981; color: #fff; padding: 12px 22px; border-radius: 14px; font-weight: 600; font-size: 0.9rem; transform: translateY(100px); opacity: 0; transition: 0.3s; z-index: 999; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4); }
    .toast.show { transform: translateY(0); opacity: 1; }
  </style>
</head>
<body>
  <div class="ambient-orb orb-1"></div>
  <div class="ambient-orb orb-2"></div>
  <div class="ambient-orb orb-3"></div>

  <div class="container">
    <header>
      <div class="badge">✦ HIGH-SPEED ENGINE • 24/7 ONLINE</div>
      <h1 class="title">Music X API Documentation</h1>
      <p class="subtitle">Complete JioSaavn Gateway with 320kbps Direct Streams, Metadata & Downloads</p>
    </header>

    <!-- Dynamic Base URL Box -->
    <div class="base-card liquid-glass">
      <div>
        <div class="base-title">Active Host Base URL</div>
        <div class="base-url" id="baseUrlText">https://...</div>
      </div>
      <button class="btn btn-grad" onclick="copyBaseUrl()">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        Copy Base URL
      </button>
    </div>

    <!-- API Endpoints Section -->
    <div class="endpoints-grid">

      <!-- 1. Download -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/download</span>
          </div>
          <span style="font-size:0.8rem; color:#f43f5e; font-weight:700;">★ NEW MP3 EXPORT</span>
        </div>
        <div class="ep-desc">Directly triggers high-speed 320kbps MP3 audio download in browser or mobile client with ID3 metadata tags.</div>
        <div class="url-preview">
          <span class="url-text" id="url-download">/api/download?id=s_oVd9yZ</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-download')">Copy</button>
        </div>
      </div>

      <!-- 2. Search -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/search</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">Global Catalog</span>
        </div>
        <div class="ep-desc">Search songs, movie albums, or singers with query matching (exact JioSaavn catalog parity).</div>
        <div class="url-preview">
          <span class="url-text" id="url-search">/api/search?q=Kesariya&limit=10</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-search')">Copy</button>
        </div>
      </div>

      <!-- 3. Stream & Song Details -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/song</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">320kbps CDN</span>
        </div>
        <div class="ep-desc">Retrieve song details and decrypted high-bitrate streaming URLs (96kbps, 160kbps, 320kbps).</div>
        <div class="url-preview">
          <span class="url-text" id="url-song">/api/song?id=s_oVd9yZ</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-song')">Copy</button>
        </div>
      </div>

      <!-- 4. Trending Charts -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/trending</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">Top Charts</span>
        </div>
        <div class="ep-desc">Extract official Top Trending tracks currently featured on the JioSaavn homepage charts.</div>
        <div class="url-preview">
          <span class="url-text" id="url-trending">/api/trending</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-trending')">Copy</button>
        </div>
      </div>

      <!-- 5. Artist Profile -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/artist</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">Artist Info</span>
        </div>
        <div class="ep-desc">Get artist biography, 500x500 profile picture, and all top popular tracks.</div>
        <div class="url-preview">
          <span class="url-text" id="url-artist">/api/artist?name=Arijit+Singh</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-artist')">Copy</button>
        </div>
      </div>

      <!-- 6. Playlists -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/playlist</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">Playlists</span>
        </div>
        <div class="ep-desc">Search public playlists and unpack full song tracks with metadata.</div>
        <div class="url-preview">
          <span class="url-text" id="url-playlist">/api/playlist?q=Hindi+Romance</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-playlist')">Copy</button>
        </div>
      </div>

      <!-- 7. Lyrics -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="method-get">GET</span>
            <span class="ep-path">/api/lyrics</span>
          </div>
          <span style="font-size:0.8rem; color:var(--text-dim);">Lyrics</span>
        </div>
        <div class="ep-desc">Extract official track lyrics with proper linebreaks and paragraph formatting.</div>
        <div class="url-preview">
          <span class="url-text" id="url-lyrics">/api/lyrics?id=s_oVd9yZ</span>
          <button class="btn btn-ghost" onclick="copySnippet('url-lyrics')">Copy</button>
        </div>
      </div>

    </div>
  </div>

  <div id="toast" class="toast">URL Copied to Clipboard!</div>

  <script>
    const origin = window.location.origin;
    document.getElementById('baseUrlText').innerText = origin;

    // Prepend full domain to all snippet preview texts
    const snippetIds = ['url-download', 'url-search', 'url-song', 'url-trending', 'url-artist', 'url-playlist', 'url-lyrics'];
    snippetIds.forEach(id => {
      const el = document.getElementById(id);
      if(el) {
        el.innerText = origin + el.innerText;
      }
    });

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2200);
    }

    function copyBaseUrl() {
      navigator.clipboard.writeText(origin);
      showToast('Base URL Copied!');
    }

    function copySnippet(elementId) {
      const text = document.getElementById(elementId).innerText;
      navigator.clipboard.writeText(text);
      showToast('API URL Copied!');
    }
  </script>
</body>
</html>
"""

# ----------------- ROUTES ----------------- #

@app.get("/", response_class=HTMLResponse, tags=["Documentation"])
@app.get("/docs", response_class=HTMLResponse, tags=["Documentation"])
def modern_docs():
    """Returns Liquid Glass Styled Modern Documentation UI"""
    return DOCS_HTML

# 1. NEW DOWNLOAD ENDPOINT
@app.get("/api/download", tags=["Download"])
def download_song(id: str = Query(..., description="Track ID")):
    """
    Direct MP3 audio download endpoint.
    Resolves 320kbps CDN stream and redirects as direct downloadable stream.
    """
    params = {
        '__call': 'song.getDetails',
        '_format': 'json',
        '_marker': '0',
        'pids': id
    }
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
        song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
        if not song:
            raise HTTPException(status_code=404, detail="Song ID not found")
        
        more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
        enc_url = more.get('encrypted_media_url') or song.get('encrypted_media_url')
        
        stream_urls = fetch_stream_urls(enc_url)
        download_url = stream_urls.get('320kbps') or stream_urls.get('160kbps') or stream_urls.get('96kbps')
        
        if not download_url:
            raise HTTPException(status_code=500, detail="Audio stream unavailable for download")
        
        # Redirect to the direct CDN stream URL which browsers download immediately
        return RedirectResponse(url=download_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. SEARCH ENGINE
@app.get("/api/search", tags=["Search"])
def search_songs(q: str = Query(..., description="Song name"), page: int = 1, limit: int = 20):
    raw_results = []
    params = {
        '__call': 'search.getResults',
        '_format': 'json',
        '_marker': '0',
        'api_version': '4',
        'ctx': 'web6dot0',
        'p': str(page),
        'n': str(limit),
        'q': q
    }
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
        raw_results = r.get('results', [])
    except Exception:
        raw_results = []

    if not raw_results:
        try:
            params_more = {
                '__call': 'search.getMoreResults',
                '_format': 'json',
                '_marker': '0',
                'api_version': '4',
                'ctx': 'web6dot0',
                'query': q,
                'params': json.dumps({'type': 'song'}),
                'p': str(page),
                'n': str(limit)
            }
            r_more = requests.get(BASE_URL, params=params_more, headers=HEADERS, timeout=8).json()
            raw_results = r_more.get('results', [])
        except Exception:
            pass

    return {
        "app": "Music X API",
        "status": "success",
        "total": len(raw_results),
        "data": [format_song(s) for s in raw_results if isinstance(s, dict)]
    }

# 3. SONG DETAILS
@app.get("/api/song", tags=["Streams"])
def get_song(id: str = Query(..., description="Track ID")):
    params = {
        '__call': 'song.getDetails',
        '_format': 'json',
        '_marker': '0',
        'pids': id
    }
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

# 4. TRENDING CHARTS
@app.get("/api/trending", tags=["Trending"])
def get_trending():
    params = {
        '__call': 'webapi.getLaunchData',
        '_format': 'json',
        '_marker': '0',
        'api_version': '4',
        'ctx': 'web6dot0'
    }
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
        trending = res.get('new_trending', [])
        songs = [t for t in trending if isinstance(t, dict) and t.get('type') == 'song']
        if not songs:
            r = requests.get(BASE_URL, params={'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'p': '1', 'n': '15', 'q': 'Top Trending Hindi'}, headers=HEADERS).json()
            songs = r.get('results', [])
        return {"app": "Music X API", "status": "success", "data": [format_song(s) for s in songs[:15]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. ARTIST PROFILE
@app.get("/api/artist", tags=["Artist"])
def get_artist(name: Optional[str] = None, id: Optional[str] = None):
    if not name and not id:
        raise HTTPException(status_code=400, detail="Provide either 'name' or 'id'")
    artist_id = id
    if name and not artist_id:
        s_res = requests.get(BASE_URL, params={'__call': 'search.getArtistResults', '_format': 'json', '_marker': '0', 'p': '1', 'n': '1', 'q': name}, headers=HEADERS).json()
        results = s_res.get('results', [])
        if not results:
            raise HTTPException(status_code=404, detail="Artist not found")
        artist_id = results[0].get('artistid') or results[0].get('id')

    res = requests.get(BASE_URL, params={'__call': 'artist.getArtistPageDetails', '_format': 'json', '_marker': '0', 'artistId': artist_id}, headers=HEADERS).json()
    top_songs = res.get('topSongs', [])
    if isinstance(top_songs, dict):
        top_songs = top_songs.get('songs', [])
    return {
        "app": "Music X API",
        "status": "success",
        "artist": {
            "id": artist_id,
            "name": clean_text(res.get('name')),
            "role": clean_text(res.get('role')),
            "image": res.get('image', '').replace('150x150', '500x500')
        },
        "top_songs": [format_song(s) for s in top_songs if isinstance(s, dict)]
    }

# 6. PLAYLISTS
@app.get("/api/playlist", tags=["Playlists"])
def get_playlist(q: Optional[str] = None, id: Optional[str] = None):
    if not q and not id:
        raise HTTPException(status_code=400, detail="Provide either 'q' or 'id'")
    list_id = id
    if q and not list_id:
        s_res = requests.get(BASE_URL, params={'__call': 'search.getPlaylistResults', '_format': 'json', '_marker': '0', 'p': '1', 'n': '1', 'q': q}, headers=HEADERS).json()
        playlists = s_res.get('results', [])
        if not playlists:
            raise HTTPException(status_code=404, detail="Playlist not found")
        list_id = playlists[0].get('id')

    res = requests.get(BASE_URL, params={'__call': 'playlist.getDetails', '_format': 'json', '_marker': '0', 'listid': list_id}, headers=HEADERS).json()
    return {
        "app": "Music X API",
        "status": "success",
        "playlist": {
            "id": list_id,
            "title": clean_text(res.get('title')),
            "total_tracks": res.get('list_count'),
            "image": res.get('image', '').replace('150x150', '500x500')
        },
        "songs": [format_song(s) for s in res.get('songs', []) if isinstance(s, dict)]
    }

# 7. LYRICS
@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Song ID")):
    res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
    if 'lyrics' in res and res['lyrics']:
        return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    return {"app": "Music X API", "status": "success", "has_lyrics": False, "lyrics": None, "message": "Lyrics not available"}
