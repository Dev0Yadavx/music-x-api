# 🎵 Music X API

High-speed 24/7 REST API for Music x song search, 320kbps audio decryption, playlist extraction, and lyrics.

## 🚀 Endpoints
- `GET /docs` - Interactive Swagger UI Documentation
- `GET /api/search?q={query}` - Global track search
- `GET /api/song?id={song_id}` - Direct 320kbps CDN playable audio URLs
- `GET /api/trending` - Trending tracks from JioSaavn charts
- `GET /api/artist?name={artist}` - Artist profile & top tracks
- `GET /api/playlist?q={name}` - Curated playlists scraper
- `GET /api/lyrics?id={song_id}` - Raw & synced lyrics

## 📦 Deployment
Ready for 1-click deployment on Railway.app, Render, or Docker.Ver
