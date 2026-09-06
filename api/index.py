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
    version="3.5.0",
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

CDN_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.jiosaavn.com/'
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
            # Force HTTPS
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
    .endpoint-card { padding: 18px; }
    .ep-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
    .method-get { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.74rem; }
    .ep-path { font-size: 1.1rem; font-weight: 700; font-family: monospace; color: #fff; }
    .ep-desc { color: var(--text-dim); font-size: 0.88rem; margin-bottom: 12px; }

    .search-input-box { display: flex; gap: 8px; margin-bottom: 12px; }
    .search-input-box input { flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); border-radius: 10px; padding: 8px 12px; color: #fff; outline: none; }
    
    .url-preview { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); padding: 10px 12px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; gap: 10px; font-family: monospace; font-size: 0.82rem; color: #e2e8f0; flex-wrap: wrap; }
    .url-text { word-break: break-all; flex: 1; }
    .action-group { display: flex; gap: 6px; }

    .json-viewer-container { display: none; margin-top: 14px; background: rgba(2, 4, 10, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px; }
    .json-output { max-height: 240px; overflow-y: auto; font-family: monospace; font-size: 0.82rem; color: #a5b4fc; white-space: pre-wrap; word-break: break-all; }

    footer { margin-top: 40px; padding: 24px 16px; text-align: center; border-radius: 20px; }
    .dev-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 14px; background: linear-gradient(135deg, #f43f5e, #fb923c, #eab308, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
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
      <button class="btn btn-grad" onclick="navigator.clipboard.writeText(window.location.origin); alert('Copied!');">Copy Base URL</button>
    </div>

    <div class="endpoints-grid">

      <!-- 1. Search -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <span class="method-get">GET</span>
          <span class="ep-path">/api/search</span>
        </div>
        <div class="ep-desc">Real-time catalog search for songs, albums, and artists.</div>
        <div class="url-preview">
          <span class="url-text" id="url-search">/api/search?q=Kesariya&limit=5</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="runInUI('search', '/api/search?q=Kesariya&limit=5')">Run In UI</button>
          </div>
        </div>
        <div class="json-viewer-container" id="json-box-search"><div class="json-output" id="json-out-search"></div></div>
      </div>

      <!-- 2. Download / Stream -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <span class="method-get">GET</span>
          <span class="ep-path">/api/download</span>
        </div>
        <div class="ep-desc">High-speed audio streaming proxy & direct 320kbps MP3 downloader (Android & Browser verified).</div>
        <div class="url-preview">
          <span class="url-text" id="url-download">/api/download?id=s_oVd9yZ</span>
          <div class="action-group">
            <a href="#" target="_blank" class="btn btn-test" id="test-download">Direct Download ↗</a>
          </div>
        </div>
      </div>

      <!-- 3. Lyrics -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <span class="method-get">GET</span>
          <span class="ep-path">/api/lyrics</span>
        </div>
        <div class="ep-desc">Extract official track lyrics with synced line breaks & paragraph formatting.</div>
        <div class="url-preview">
          <span class="url-text" id="url-lyrics">/api/lyrics?id=s_oVd9yZ</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="runInUI('lyrics', '/api/lyrics?id=s_oVd9yZ')">Run In UI</button>
          </div>
        </div>
        <div class="json-viewer-container" id="json-box-lyrics"><div class="json-output" id="json-out-lyrics"></div></div>
      </div>

      <!-- 4. Playlists -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <span class="method-get">GET</span>
          <span class="ep-path">/api/playlist</span>
        </div>
        <div class="ep-desc">Unpack complete playlist tracks, covers, and details by title or playlist ID.</div>
        <div class="url-preview">
          <span class="url-text" id="url-playlist">/api/playlist?q=Hindi+Romance</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="runInUI('playlist', '/api/playlist?q=Hindi+Romance')">Run In UI</button>
          </div>
        </div>
        <div class="json-viewer-container" id="json-box-playlist"><div class="json-output" id="json-out-playlist"></div></div>
      </div>

      <!-- 5. Song Details -->
      <div class="endpoint-card liquid-glass">
        <div class="ep-top">
          <span class="method-get">GET</span>
          <span class="ep-path">/api/song</span>
        </div>
        <div class="ep-desc">Complete track details and signed high-bitrate CDN streaming keys.</div>
        <div class="url-preview">
          <span class="url-text" id="url-song">/api/song?id=s_oVd9yZ</span>
          <div class="action-group">
            <button class="btn btn-test" onclick="runInUI('song', '/api/song?id=s_oVd9yZ')">Run In UI</button>
          </div>
        </div>
        <div class="json-viewer-container" id="json-box-song"><div class="json-output" id="json-out-song"></div></div>
      </div>

    </div>

    <!-- Liquid Glass Custom Footer -->
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
    document.getElementById('test-download').href = origin + '/api/download?id=s_oVd9yZ';

    async function runInUI(key, path) {
      const box = document.getElementById('json-box-' + key);
      const out = document.getElementById('json-out-' + key);
      box.style.display = 'block';
      out.innerText = '// Fetching data from Music X Engine...';
      try {
        const res = await fetch(path);
        const data = await res.json();
        out.innerText = JSON.stringify(data, null, 2);
      } catch(err) {
        out.innerText = '// Request failed: ' + err.message;
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

# 1. BULLETPROOF DOWNLOAD & STREAMING (FOR BROWSER & ANDROID APP)
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
        
        # Range handling for Android ExoPlayer & background download
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

# 2. SEARCH
@app.get("/api/search", tags=["Search"])
def search_songs(q: str = Query(..., description="Song name"), page: int = 1, limit: int = 20):
    raw_results = []
    params = {'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'ctx': 'web6dot0', 'p': str(page), 'n': str(limit), 'q': q}
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
        raw_results = r.get('results', [])
    except Exception:
        raw_results = []

    if not raw_results:
        try:
            params_more = {'__call': 'search.getMoreResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'ctx': 'web6dot0', 'query': q, 'params': json.dumps({'type': 'song'}), 'p': str(page), 'n': str(limit)}
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

# 4. TRENDING
@app.get("/api/trending", tags=["Trending"])
def get_trending():
    params = {'__call': 'webapi.getLaunchData', '_format': 'json', '_marker': '0', 'api_version': '4', 'ctx': 'web6dot0'}
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

# 5. PLAYLISTS (FIXED TRACK UNPACKING)
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

    # Fetch complete playlist tracklist
    params = {
        '__call': 'playlist.getDetails',
        '_format': 'json',
        '_marker': '0',
        'api_version': '4',
        'ctx': 'web6dot0',
        'listid': list_id
    }
    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
    
    songs_data = res.get('songs', [])
    if isinstance(songs_data, dict):
        songs_data = list(songs_data.values())

    return {
        "app": "Music X API",
        "status": "success",
        "playlist": {
            "id": list_id,
            "title": clean_text(res.get('title')),
            "total_tracks": int(res.get('list_count') or len(songs_data)),
            "image": res.get('image', '').replace('150x150', '500x500')
        },
        "songs": [format_song(s) for s in songs_data if isinstance(s, dict)]
    }

# 6. ENHANCED LYRICS ENGINE (FIXED RESOLUTION)
@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Song ID")):
    # 1. Direct lyrics check
    try:
        res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
        if isinstance(res, dict) and res.get('lyrics'):
            return {
                "app": "Music X API",
                "status": "success",
                "has_lyrics": True,
                "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')
            }
    except Exception:
        pass

    # 2. Metadata details resolution check
    try:
        d_res = requests.get(BASE_URL, params={'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}, headers=HEADERS, timeout=5).json()
        song = d_res.get(id) or (d_res.get('songs', [])[0] if d_res.get('songs') else None)
        if song:
            more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
            has_lyrics = more.get('has_lyrics') == 'true' or song.get('has_lyrics') == 'true'
            actual_lyrics_id = more.get('lyrics_id') or id
            if has_lyrics:
                lyr_res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': actual_lyrics_id}, headers=HEADERS, timeout=5).json()
                if isinstance(lyr_res, dict) and lyr_res.get('lyrics'):
                    return {
                        "app": "Music X API",
                        "status": "success",
                        "has_lyrics": True,
                        "lyrics": lyr_res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')
                    }
    except Exception:
        pass

    return {
        "app": "Music X API",
        "status": "success",
        "has_lyrics": False,
        "lyrics": "Lyrics unavailable for this track.",
        "message": "Lyrics not available"
    }
