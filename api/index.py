import base64
import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from Crypto.Cipher import DES

app = Flask(__name__)
CORS(app)

BASE_URL = "https://www.jiosaavn.com/api.php"
DES_KEY = b"38346591"

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
    res = requests.get(BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=10)
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
    return jsonify({
        "status": "online",
        "service": "Music X API",
        "code": 200,
        "endpoints": [
            "/home?languages=hindi,bhojpuri,haryanvi",
            "/trending?languages=hindi,bhojpuri,haryanvi",
            "/search/all?query=pawan singh",
            "/search?query=kesariya&page=1&limit=5",
            "/search/albums?query=ashiqui 2&page=1&limit=5",
            "/search/playlists?query=bhojpuri dance&page=1&limit=5",
            "/song?id=c9_7sW8q",
            "/album?id=51664531",
            "/playlist?id=1130638706",
            "/artist?id=459320",
            "/lyrics?id=c9_7sW8q",
            "/recommendations?id=c9_7sW8q"
        ]
    }), 200

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

@app.route("/search/all", methods=["GET"])
def search_all():
    query = request.args.get("query", "")
    data = fetch_jio({"__call": "autocomplete.get", "query": query})
    return jsonify({"status": "success", "code": 200, "data": data}), 200

@app.route("/search", methods=["GET"])
def search_songs():
    query = request.args.get("query", "")
    page = request.args.get("page", 1)
    limit = request.args.get("limit", 20)
    data = fetch_jio({"__call": "search.getResults", "q": query, "p": page, "n": limit})
    results = [format_song(s) for s in data.get("results", [])]
    return jsonify({"status": "success", "code": 200, "total": len(results), "results": results}), 200

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

@app.route("/song", methods=["GET"])
def song():
    song_id = request.args.get("id", "")
    song_data = resolve_song_data(song_id)
    if song_data:
        return jsonify({"status": "success", "code": 200, "data": format_song(song_data)}), 200
    return jsonify({"status": "error", "code": 404, "message": "Song not found"}), 404

@app.route("/album", methods=["GET"])
def album():
    album_id = request.args.get("id", "")
    data = fetch_jio({"__call": "content.getAlbumDetails", "albumid": album_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Album not found"}), 404

@app.route("/playlist", methods=["GET"])
def playlist():
    playlist_id = request.args.get("id", "")
    data = fetch_jio({"__call": "playlist.getDetails", "listid": playlist_id})
    if data and "list" in data:
        data["list"] = [format_song(s) for s in data.get("list", [])]
        data["image"] = format_image(data.get("image", ""))
        return jsonify({"status": "success", "code": 200, "data": data}), 200
    return jsonify({"status": "error", "code": 404, "message": "Playlist not found"}), 404

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
        return jsonify({"status": "success", "code": 200, "has_lyrics": True, "lyrics": clean_lyrics}), 200
    return jsonify({"status": "error", "code": 404, "message": "Lyrics unavailable"}), 404

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

app = app
