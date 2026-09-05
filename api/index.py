import os
import io
import json
import html
import base64
import requests
from typing import Optional
from Crypto.Cipher import DES
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, APIC, ID3NoHeaderError

app = FastAPI(
    title="Music X API",
    description="Music x Api Best Music Api all end",
    version="2.6.0",
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
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=5).json()
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

# ----------------- EMBED COVER ART & TAGS ----------------- #

def embed_metadata_and_cover(raw_audio_bytes, title, artist, album, year, image_url):
    audio_buffer = io.BytesIO(raw_audio_bytes)
    
    # Check or init ID3 tag container
    try:
        tags = ID3(audio_buffer)
    except ID3NoHeaderError:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=title))
    tags.add(TPE1(encoding=3, text=artist))
    tags.add(TALB(encoding=3, text=album))
    if year:
        tags.add(TYER(encoding=3, text=str(year)))

    # Fetch and embed HD Cover Artwork
    if image_url:
        try:
            hd_art_url = image_url.replace('150x150', '500x500')
            img_res = requests.get(hd_art_url, timeout=5)
            if img_res.status_code == 200:
                tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Front Cover
                    desc='Cover',
                    data=img_res.content
                ))
        except Exception:
            pass

    try:
        tags.save(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.getvalue()
    except Exception:
        return raw_audio_bytes

# ----------------- ROUTES ----------------- #

@app.get("/")
@app.get("/docs")
def root_docs():
    return RedirectResponse(url="/swagger")

# 1. DOWNLOAD WITH COVER ART & TAGS EMBEDDED
@app.get("/api/download", tags=["Download"])
def download_song(id: str = Query(..., description="Track ID")):
    params = {'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=6).json()
        song = res.get(id) or (res.get('songs', [])[0] if res.get('songs') else None)
        if not song:
            raise HTTPException(status_code=404, detail="Song ID not found")
        
        more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
        enc_url = more.get('encrypted_media_url') or song.get('encrypted_media_url')
        
        # Resolve 320kbps authenticated CDN stream
        stream_url = get_authorized_stream_url(enc_url, '320') or get_authorized_stream_url(enc_url, '160')
        if not stream_url:
            raise HTTPException(status_code=500, detail="Stream link resolution failed")
            
        cdn_req = requests.get(stream_url, headers=CDN_HEADERS, timeout=12)
        if cdn_req.status_code not in [200, 206]:
            return RedirectResponse(url=stream_url)

        title = clean_text(song.get('title') or song.get('song') or 'Track')
        artist = extract_artists(song)
        album = clean_text(more.get('album') or song.get('album') or 'Music X')
        year = more.get('year') or song.get('year') or ""
        image_url = song.get('image') or more.get('image', '')

        # Tag embedding process
        tagged_audio = embed_metadata_and_cover(
            cdn_req.content,
            title=title,
            artist=artist,
            album=album,
            year=year,
            image_url=image_url
        )

        safe_filename = "".join(c for c in f"{title} - {artist}" if c.isalnum() or c in (' ', '_', '-')).strip() or 'track'

        return Response(
            content=tagged_audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}.mp3"',
                "Accept-Ranges": "bytes"
            }
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

# 5. LYRICS
@app.get("/api/lyrics", tags=["Lyrics"])
def get_lyrics(id: str = Query(..., description="Song ID")):
    try:
        res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': id}, headers=HEADERS, timeout=5).json()
        if isinstance(res, dict) and 'lyrics' in res and res['lyrics']:
            return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    except Exception:
        pass

    try:
        d_res = requests.get(BASE_URL, params={'__call': 'song.getDetails', '_format': 'json', '_marker': '0', 'pids': id}, headers=HEADERS, timeout=5).json()
        song = d_res.get(id) or (d_res.get('songs', [])[0] if d_res.get('songs') else None)
        if song:
            more = song.get('more_info', {}) if isinstance(song.get('more_info'), dict) else {}
            has_lyrics = more.get('has_lyrics') == 'true' or song.get('has_lyrics') == 'true'
            actual_lyrics_id = more.get('lyrics_id') or id
            if has_lyrics:
                lyr_res = requests.get(BASE_URL, params={'__call': 'lyrics.getLyrics', '_format': 'json', '_marker': '0', 'lyrics_id': actual_lyrics_id}, headers=HEADERS, timeout=5).json()
                if isinstance(lyr_res, dict) and 'lyrics' in lyr_res and lyr_res['lyrics']:
                    return {"app": "Music X API", "status": "success", "has_lyrics": True, "lyrics": lyr_res['lyrics'].replace('<br>', '\n').replace('<br/>', '\n')}
    except Exception:
        pass

    return {"app": "Music X API", "status": "success", "has_lyrics": False, "lyrics": "Lyrics not available", "message": "Lyrics not available"}
