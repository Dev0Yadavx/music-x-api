import os
import json
import html
import base64
import requests
from typing import Optional
from Crypto.Cipher import DES
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Music X API",
    description="High-Speed JioSaavn Music Engine with Exact Terminal Match",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://www.jiosaavn.com/api.php"

# Indian Client Emulation Headers (Bypasses Vercel US Datacenter Filter)
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

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# 1. EXACT TERMINAL APP SEARCH LOGIC (search.getResults + search.getMoreResults)
@app.get("/api/search", tags=["Search"])
def search_songs(q: str = Query(..., description="Song name"), page: int = 1, limit: int = 20):
    raw_results = []
    
    # Primary Call: Terminal app wala standard search
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

    # Secondary Call: Agar 0 results aate hain toh getMoreResults call karega
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

# 2. SONG DETAILS & DIRECT 320kbps
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

# 3. TOP TRENDING CHARTS
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

# 4. ARTIST PROFILE & TOP SONGS
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

# 5. PLAYLIST TRACKS
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

# 6. LYRICS
@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Song ID")):
    res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
    if 'lyrics' in res and res['lyrics']:
        return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    return {"app": "Music X API", "status": "success", "has_lyrics": False, "lyrics": None, "message": "Lyrics not available"}
