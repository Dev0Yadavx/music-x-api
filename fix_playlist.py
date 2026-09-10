with open("main.py", "r") as f:
    code = f.read()

old_playlist = """@app.route("/playlist/<playlist_id>")
def get_playlist(playlist_id):
    # RD / RDCLAK radio mix handler
    if playlist_id.startswith("RD") or playlist_id.startswith("RDCLAK"):
        try:
            return jsonify(yt.get_watch_playlist(playlistId=playlist_id, limit=int(request.args.get("limit", 50))))
        except Exception:
            pass

    # Standard playlist handler (PL / VL / User)
    try:
        return jsonify(yt.get_playlist(playlistId=playlist_id, limit=int(request.args.get("limit", 100))))
    except Exception:
        # Fallback to watch playlist if standard playlist fails
        try:
            return jsonify(yt.get_watch_playlist(playlistId=playlist_id))
        except Exception as e:
            return jsonify({"error": f"Playlist load failed: {str(e)}"}), 500"""

new_playlist = """@app.route("/playlist/<playlist_id>")
def get_playlist(playlist_id):
    limit = int(request.args.get("limit", 100))
    # 1. Direct get_playlist try
    try:
        return jsonify(yt.get_playlist(playlistId=playlist_id, limit=limit))
    except Exception:
        pass

    # 2. VL prefix attach try (for YouTube standard PL lists)
    if playlist_id.startswith("PL"):
        try:
            return jsonify(yt.get_playlist(playlistId="VL" + playlist_id, limit=limit))
        except Exception:
            pass

    # 3. Watch playlist / Radio queue fallback
    try:
        return jsonify(yt.get_watch_playlist(playlistId=playlist_id, limit=limit))
    except Exception:
        pass

    # 4. If VL prefix was added to watch
    try:
        return jsonify(yt.get_watch_playlist(playlistId="VL" + playlist_id, limit=limit))
    except Exception as e:
        return jsonify({"error": f"Playlist load failed: {str(e)}"}), 500"""

if old_playlist in code:
    code = code.replace(old_playlist, new_playlist)
    with open("main.py", "w") as f:
        f.write(code)
    print("[+] Playlist route successfully patched!")
else:
    print("[-] Route pattern mismatch, manually applying...")
