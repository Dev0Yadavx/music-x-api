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
    description="Production-ready JioSaavn API with Official App Search Matching",
    version="1.1.0",
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

# Official App headers + Multi-language cookies taaki regional tracks drop na hon
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.jiosaavn.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Cookie': 'L=hindi%2Cenglish%2Cpunjabi%2Cbhojpuri%2Ctamil%2Ctelugu%2Charyanvi%2Cmarathi%2Cgujarati%2Cbengali;'
}

def clean_text(text):
    if not text:
        return ""
    return html.unescape(str(text)).replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').strip()

def extract_artists(data):
    if not isinstance(data, dict):
        return "Various Artists"
    more = data.get('more_info', {}) if isinstance(data.get('more_info'), dict) else {}
    artist_map = more.get('artist_map', {})
    if isinstance(artist_map, str):
        try:
            artist_map = json.loads(artist_map)
        except Exception:
            artist_map = {}
            
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

def get_songs_by_ids(id_list):
    """Fetch complete metadata and stream keys using comma-separated IDs"""
    if not id_list:
        return []
    try:
        params = {
            '__call': 'song.getDetails',
            '_format': 'json',
            '_marker': '0',
            'pids': ",".join(id_list[:20])
        }
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=7).json()
        songs = []
        if isinstance(res, dict):
            if 'songs' in res and isinstance(res['songs'], list):
                songs = res['songs']
            else:
                for k, v in res.items():
                    if isinstance(v, dict) and 'id' in v:
                        songs.append(v)
        return [format_song(s) for s in songs]
    except Exception:
        return []

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/api/search", tags=["Search"])
def search_songs(q: str = Query(..., description="Query term"), page: int = 1, limit: int = 15):
    """
    Dual Engine Search:
    1. App AutoComplete Engine (catches misspelled and newest app-exclusive releases)
    2. Fallback to Full Catalog Search
    """
    final_songs = []
    seen_ids = set()

    # Tier 1: Official App Typeahead Autocomplete Search
    try:
        ac_params = {
            '__call': 'autocomplete.get',
            '_format': 'json',
            '_marker': '0',
            'query': q
        }
        ac_res = requests.get(BASE_URL, params=ac_params, headers=HEADERS, timeout=5).json()
        song_candidates = ac_res.get('songs', {}).get('data', [])
        ac_ids = [s.get('id') for s in song_candidates if s.get('id')]

        if ac_ids:
            detailed_songs = get_songs_by_ids(ac_ids)
            for s in detailed_songs:
                if s.get('id') and s['id'] not in seen_ids:
                    seen_ids.add(s['id'])
                    final_songs.append(s)
    except Exception:
        pass

    # Tier 2: Deep Catalog Search (adds extra results and handles pagination)
    try:
        params = {
            '__call': 'search.getResults',
            '_format': 'json',
            '_marker': '0',
            'api_version': '4',
            'p': str(page),
            'n': str(limit),
            'q': q
        }
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=7).json()
        raw = res.get('results', [])
        for r in raw:
            formatted = format_song(r)
            if formatted.get('id') and formatted['id'] not in seen_ids:
                seen_ids.add(formatted['id'])
                final_songs.append(formatted)
    except Exception:
        pass

    return {
        "app": "Music X API",
        "status": "success",
        "total": len(final_songs),
        "data": final_songs[:limit]
    }

@app.get("/api/song", tags=["Streams & Details"])
def get_song(id: str = Query(..., description="Song ID")):
    params = {'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}
    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
    song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return {"app": "Music X API", "status": "success", "data": format_song(song)}

@app.get("/api/trending", tags=["Trending"])
def get_trending():
    params = {'__call': 'webapi.getLaunchData', '_format': 'json', '_marker': '0', 'api_version': '4'}
    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8).json()
    trending = res.get('new_trending', [])
    songs = [t for t in trending if isinstance(t, dict) and t.get('type') == 'song']
    if not songs:
        res = requests.get(BASE_URL, params={'__call': 'search.getResults', '_format': 'json', '_marker': '0', 'api_version': '4', 'p': '1', 'n': '15', 'q': 'Top Hindi Hits'}, headers=HEADERS).json()
        songs = res.get('results', [])
    return {"app": "Music X API", "status": "success", "data": [format_song(s) for s in songs[:15]]}

@app.get("/api/artist", tags=["Artist"])
def get_artist(name: Optional[str] = None, id: Optional[str] = None):
    if not name and not id:
        raise HTTPException(status_code=400, detail="Provide either name or id")
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
        "artist": {"id": artist_id, "name": clean_text(res.get('name')), "role": clean_text(res.get('role')), "image": res.get('image', '').replace('150x150', '500x500')},
        "top_songs": [format_song(s) for s in top_songs if isinstance(s, dict)]
    }

@app.get("/api/playlist", tags=["Playlists"])
def get_playlist(q: Optional[str] = None, id: Optional[str] = None):
    if not q and not id:
        raise HTTPException(status_code=400, detail="Provide either q or id")
    list_id = id
    if q and not list_id:
        s_res = requests.get(BASE_URL, params={'__call': 'search.getPlaylistResults', '_format': 'json', '_marker': '0', 'p': '1', 'n': '1', 'q': q}, headers=HEADERS).json()
        results = s_res.get('results', [])
        if not results:
            raise HTTPException(status_code=404, detail="Playlist not found")
        list_id = results[0].get('id')

    res = requests.get(BASE_URL, params={'__call': 'playlist.getDetails', '_format': 'json', '_marker': '0', 'listid': list_id}, headers=HEADERS).json()
    return {
        "app": "Music X API",
        "status": "success",
        "playlist": {"id": list_id, "title": clean_text(res.get('title')), "total_tracks": res.get('list_count'), "image": res.get('image', '').replace('150x150', '500x500')},
        "songs": [format_song(s) for s in res.get('songs', []) if isinstance(s, dict)]
    }

@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Track ID")):
    res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
    if 'lyrics' in res and res['lyrics']:
        return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    return {"app": "Music X API", "status": "success", "has_lyrics": False, "lyrics": None, "message": "Lyrics not available"}
