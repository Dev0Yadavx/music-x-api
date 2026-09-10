import json
import os
import yt_dlp
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from ytmusicapi import YTMusic

app = Flask(__name__)
CORS(app)

auth_path = "headers_auth.json"
authenticated = False

try:
    if os.path.exists(auth_path):
        yt = YTMusic(auth_path)
        authenticated = True
    elif os.path.exists("browser.json"):
        yt = YTMusic("browser.json")
        authenticated = True
    elif os.path.exists("oauth.json"):
        yt = YTMusic("oauth.json")
        authenticated = True
    else:
        yt = YTMusic()
except Exception:
    yt = YTMusic()

DOCS_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Music x api Docs</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='%23ff2a44'/><stop offset='100%' stop-color='%23ffd60a'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='%2307090e' stroke='url(%23g)' stroke-width='4'/><path d='M40 30v40l28-20z' fill='url(%23g)'/></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root[data-theme="dark"] {
      --bg: #07090e;
      --card: rgba(255, 255, 255, 0.04);
      --card-hover: rgba(255, 255, 255, 0.07);
      --border: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(255, 42, 68, 0.4);
      --text: #ffffff;
      --sub: #94a3b8;
      --green-code: #00ff66;
      --code-bg: #030605;
      --top-card: rgba(255, 255, 255, 0.04);
    }
    :root[data-theme="light"] {
      --bg: #f8fafc;
      --card: rgba(255, 255, 255, 0.85);
      --card-hover: rgba(255, 255, 255, 1);
      --border: rgba(0, 0, 0, 0.08);
      --border-glow: rgba(255, 42, 68, 0.45);
      --text: #0f172a;
      --sub: #64748b;
      --green-code: #059669;
      --code-bg: #f1f5f9;
      --top-card: rgba(255, 255, 255, 0.9);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; transition: background 0.3s, color 0.3s, border-color 0.3s; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; padding-bottom: 70px; }

    .glow-1 { position: fixed; top: -140px; left: -120px; width: 420px; height: 420px; background: radial-gradient(circle, rgba(255, 42, 68, 0.2) 0%, transparent 70%); filter: blur(55px); pointer-events: none; z-index: 0; }
    .glow-2 { position: fixed; bottom: -120px; right: -120px; width: 440px; height: 440px; background: radial-gradient(circle, rgba(255, 214, 10, 0.16) 0%, transparent 70%); filter: blur(65px); pointer-events: none; z-index: 0; }

    .wrap { max-width: 900px; margin: 0 auto; padding: 14px 12px; position: relative; z-index: 1; }

    /* Top Bar with Single Line Header & Theme Toggle */
    .header-box { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-radius: 16px; background: var(--top-card); border: 1px solid var(--border); backdrop-filter: blur(18px); box-shadow: 0 12px 30px rgba(0,0,0,0.25); margin-bottom: 12px; gap: 8px; }
    .main-title { font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: clamp(13px, 4vw, 22px); background: linear-gradient(135deg, #ff2a44 0%, #ffd60a 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 10px rgba(255,42,68,0.3)); letter-spacing: -0.01em; }
    .theme-toggle-btn { background: var(--card); border: 1px solid var(--border); width: 36px; height: 36px; min-width: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text); backdrop-filter: blur(14px); }
    .theme-toggle-btn svg { width: 17px; height: 17px; fill: currentColor; }

    /* Base URL Card */
    .base-url-card { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin-bottom: 18px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; backdrop-filter: blur(14px); gap: 8px; }
    .base-left { display: flex; align-items: center; gap: 8px; overflow: hidden; }
    .base-tag { font-size: 9.5px; font-weight: 800; background: rgba(255, 214, 10, 0.15); color: #ffd60a; border: 1px solid rgba(255, 214, 10, 0.35); padding: 3px 6px; border-radius: 5px; }
    .base-text { font-family: 'JetBrains Mono', monospace; font-size: 11.5px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* Categories */
    .cat-title { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #ffd60a; margin: 18px 0 8px 4px; display: flex; align-items: center; gap: 6px; }
    .cat-title::before { content: ""; width: 4px; height: 13px; background: #ff2a44; border-radius: 4px; }
    .endpoints-list { display: flex; flex-direction: column; gap: 8px; }

    /* Endpoint Card with Inline Accordion */
    .ep-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; backdrop-filter: blur(16px); overflow: hidden; transition: border-color 0.25s, transform 0.25s; }
    .ep-card:hover { border-color: var(--border-glow); transform: translateY(-1px); }
    .ep-top-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; gap: 8px; flex-wrap: wrap; }
    .ep-meta { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 200px; }
    .badge { font-size: 9.5px; font-weight: 800; font-family: 'JetBrains Mono', monospace; padding: 3px 6px; border-radius: 5px; }
    .badge-get { background: rgba(255, 214, 10, 0.12); color: #ffd60a; border: 1px solid rgba(255, 214, 10, 0.3); }
    .badge-post { background: rgba(255, 42, 68, 0.12); color: #ff2a44; border: 1px solid rgba(255, 42, 68, 0.3); }

    .ep-path { font-size: 12px; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text); word-break: break-all; }
    .ep-desc { font-size: 10.5px; color: var(--sub); margin-top: 1px; }

    .ep-actions { display: flex; gap: 5px; }
    .btn-sm { padding: 5px 10px; font-size: 10.5px; font-weight: 700; border-radius: 7px; cursor: pointer; border: 1px solid var(--border); background: rgba(255,255,255,0.06); color: var(--text); display: flex; align-items: center; gap: 4px; }
    .btn-sm:hover { background: rgba(255,255,255,0.14); }
    .btn-test { background: linear-gradient(135deg, #ff2a44, #ffd60a); border: none; color: #000; font-weight: 800; }

    /* Inline Green JSON Box */
    .inline-json-box { display: none; padding: 10px 12px; background: var(--code-bg); border-top: 1px solid var(--border); }
    .json-pre { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--green-code); white-space: pre-wrap; word-break: break-all; max-height: 260px; overflow-y: auto; text-shadow: 0 0 5px rgba(0, 255, 102, 0.25); }
    .json-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .json-time { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--sub); }
    .btn-close { background: rgba(255, 42, 68, 0.15) !important; color: #ff2a44 !important; border: 1px solid rgba(255, 42, 68, 0.3) !important; font-weight: 800; }

    /* One-Box Direct Tap Export */
    .all-box-container { margin-top: 32px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px 12px; backdrop-filter: blur(16px); text-align: center; }
    .all-box-title { font-size: 13.5px; font-weight: 800; background: linear-gradient(135deg, #ffd60a, #ff2a44); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px; }
    .all-box-sub { font-size: 10.5px; color: var(--sub); margin-bottom: 12px; }
    .direct-copy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; max-width: 480px; margin: 0 auto; }
    .direct-btn { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border); background: rgba(255,255,255,0.06); color: var(--text); font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.25s; }
    .direct-btn:hover { background: linear-gradient(135deg, #ff2a44, #ffd60a); color: #000; border-color: transparent; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(255,42,68,0.3); }
    .direct-btn svg { width: 16px; height: 16px; fill: currentColor; }

    /* Developer Profile Card & Footer */
    .dev-profile-card {
      max-width: 440px;
      margin: 0 auto 20px auto;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      backdrop-filter: blur(20px);
      box-shadow: 0 15px 35px rgba(0,0,0,0.35);
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .dev-profile-card:hover {
      border-color: var(--border-glow);
      transform: translateY(-2px);
      box-shadow: 0 20px 40px rgba(255, 42, 68, 0.25);
    }
    .dp-wrapper {
      position: relative;
      margin-bottom: 12px;
    }
    .dev-dp {
      width: 78px;
      height: 78px;
      border-radius: 50%;
      object-fit: cover;
      border: 2.5px solid transparent;
      background: linear-gradient(#07090e, #07090e) padding-box,
                  linear-gradient(135deg, #ff2a44, #ffd60a) border-box;
      box-shadow: 0 0 20px rgba(255, 42, 68, 0.45);
    }
    .verified-badge {
      position: absolute;
      bottom: 2px;
      right: 2px;
      width: 20px;
      height: 20px;
      background: #00e676;
      border: 2px solid #07090e;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #000;
    }
    .verified-badge svg {
      width: 12px;
      height: 12px;
      fill: #000;
    }
    .dev-tagline {
      font-size: 11px;
      color: var(--sub);
      font-weight: 600;
      margin-top: 3px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    /* Footer */
    footer { margin-top: 40px; padding-top: 20px; text-align: center; }
    .footer-divider { width: 100%; height: 1px; background: linear-gradient(90deg, transparent, #ff2a44, #ffd60a, transparent); margin-bottom: 18px; opacity: 0.7; }
    .dev-title { font-size: 10.5px; font-weight: 700; letter-spacing: 0.12em; color: var(--sub); text-transform: uppercase; margin-bottom: 4px; }
    .dev-sig { font-size: 15px; font-weight: 800; background: linear-gradient(135deg, #ff2a44, #ffd60a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 14px; }
    .social-links { display: flex; justify-content: center; gap: 10px; margin-bottom: 16px; }
    .social-btn { display: flex; align-items: center; gap: 6px; padding: 7px 14px; background: var(--card); border: 1px solid var(--border); border-radius: 30px; color: var(--text); text-decoration: none; font-size: 11px; font-weight: 600; }
    .social-btn:hover { border-color: #ffd60a; transform: translateY(-2px); }
    .social-btn svg { width: 14px; height: 14px; fill: currentColor; }
    .copyright-txt { font-size: 11px; color: var(--sub); margin-bottom: 4px; }
    .made-with { font-size: 11px; color: var(--text); font-weight: 600; }

    /* Toast */
    .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px); background: linear-gradient(135deg, #ff2a44, #ffd60a); color: #000; font-weight: 800; padding: 8px 18px; border-radius: 30px; font-size: 11px; opacity: 0; transition: all 0.3s; z-index: 999; box-shadow: 0 10px 25px rgba(255,42,68,0.4); pointer-events: none; }
    .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
  </style>
</head>
<body>

  <div class="glow-1"></div>
  <div class="glow-2"></div>

  <div class="wrap">

    <!-- Top Bar: Single Line Heading + Dark/Light Toggle -->
    <div class="header-box">
      <div class="main-title">------Music x api Docs -----</div>
      <button class="theme-toggle-btn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
        <svg id="theme-icon" viewBox="0 0 24 24"><path d="M12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg>
      </button>
    </div>

    <!-- Base URL Card (Dynamic Cloud/Local) -->
    <div class="base-url-card">
      <div class="base-left">
        <span class="base-tag">BASE URL</span>
        <span class="base-text" id="base-url-val">Loading...</span>
      </div>
      <button class="btn-sm" onclick="copyText(window.location.origin, 'Base URL Copied!')">Copy</button>
    </div>

    <!-- 1. SEARCH & SUGGESTIONS -->
    <div class="cat-title">1. Search & Suggestions</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/search?q={query}&filter={type}</div>
              <div class="ep-desc">Filter songs, videos, albums, artists, playlists</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/search?q=Arijit+Singh&filter=songs')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(0, '/search?q=Arijit+Singh&filter=songs')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-0"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/search/suggestions?q={query}</div>
              <div class="ep-desc">Real-time autocomplete query suggestions</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/search/suggestions?q=Bhojpuri')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(1, '/search/suggestions?q=Bhojpuri')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-1"></div>
      </div>
    </div>

    <!-- 2. STREAMING & AUDIO ENGINE -->
    <div class="cat-title">2. Streaming, Tracks & Lyrics</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/stream/{video_id}</div>
              <div class="ep-desc">Direct playable m4a/opus streaming audio URL</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/stream/kJQP7kiw5Fk')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(2, '/stream/kJQP7kiw5Fk')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-2"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/song/{video_id}</div>
              <div class="ep-desc">Complete track metadata and album art</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/song/kJQP7kiw5Fk')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(3, '/song/kJQP7kiw5Fk')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-3"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/watch/{video_id}</div>
              <div class="ep-desc">Up-next playlist queue and auto-radio songs</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/watch/kJQP7kiw5Fk')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(4, '/watch/kJQP7kiw5Fk')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-4"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/song/related/{video_id}</div>
              <div class="ep-desc">Algorithmically related track recommendations</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/song/related/kJQP7kiw5Fk')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(5, '/song/related/kJQP7kiw5Fk')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-5"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/lyrics/{video_or_browse_id}</div>
              <div class="ep-desc">Synchronized / plain track lyrics resolver</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/lyrics/kJQP7kiw5Fk')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(6, '/lyrics/kJQP7kiw5Fk')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-6"></div>
      </div>
    </div>

    <!-- 3. BROWSE, CHARTS & MOODS -->
    <div class="cat-title">3. Browse, Charts & Moods</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/browse/charts?country=IN</div>
              <div class="ep-desc">Country trending Top 100 songs & artists</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/browse/charts?country=IN')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(7, '/browse/charts?country=IN')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-7"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/browse/home?limit=3</div>
              <div class="ep-desc">Personalized home carousel sections</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/browse/home?limit=3')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(8, '/browse/home?limit=3')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-8"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/browse/explore</div>
              <div class="ep-desc">Explore new releases and trending albums</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/browse/explore')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(9, '/browse/explore')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-9"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/browse/moods</div>
              <div class="ep-desc">Mood and genre categories (Workout, Chill, Party)</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/browse/moods')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(10, '/browse/moods')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-10"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/browse/mood-playlists/{params}</div>
              <div class="ep-desc">Playlists of specific mood category</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/browse/mood-playlists/ggMPOg1uX1JyZWNvbW1lbmRlZA')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(11, '/browse/mood-playlists/ggMPOg1uX1JyZWNvbW1lbmRlZA')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-11"></div>
      </div>
    </div>

    <!-- 4. ARTISTS & ALBUMS -->
    <div class="cat-title">4. Artists, Albums & Playlists</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/artist/{channel_id}</div>
              <div class="ep-desc">Artist biography, top songs, singles and albums</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/artist/UC0C-w0YjGpqDXGB8IHb662A')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(12, '/artist/UC0C-w0YjGpqDXGB8IHb662A')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-12"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/artist/albums/{channel_id}/{params}</div>
              <div class="ep-desc">Full discography of artist albums and singles</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/artist/albums/UC0C-w0YjGpqDXGB8IHb662A/b46wmt21')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(13, '/artist/albums/UC0C-w0YjGpqDXGB8IHb662A/b46wmt21')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-13"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/album/{browse_id}</div>
              <div class="ep-desc">Full album tracklist and release year</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/album/MPREb_9p2X0S6vXoU')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(14, '/album/MPREb_9p2X0S6vXoU')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-14"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/playlist/{playlist_id}</div>
              <div class="ep-desc">Universal playlist resolver (PL, VL, RD, Mixes)</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/playlist/PL4fGSI1pDJn6jXS_PE_xWDwO565Ca9yVO')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(15, '/playlist/PL4fGSI1pDJn6jXS_PE_xWDwO565Ca9yVO')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-15"></div>
      </div>
    </div>

    <!-- 5. PODCASTS & EPISODES -->
    <div class="cat-title">5. Podcasts & Shows</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/podcast/{browse_id}</div>
              <div class="ep-desc">Podcast show details and episode lists</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/podcast/MPSP')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(16, '/podcast/MPSP')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-16"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/episode/{browse_id}</div>
              <div class="ep-desc">Single podcast episode metadata and audio</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/episode/MPSP')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(17, '/episode/MPSP')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-17"></div>
      </div>
    </div>

    <!-- 6. USER LIBRARY (READ) -->
    <div class="cat-title">6. User Library (Auth Active)</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/history</div>
              <div class="ep-desc">User account recent listening history</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/history')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(18, '/library/history')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-18"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/playlists</div>
              <div class="ep-desc">User saved and created playlists</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/playlists')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(19, '/library/playlists')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-19"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/songs</div>
              <div class="ep-desc">User liked and favorite songs</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/songs')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(20, '/library/songs')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-20"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/albums</div>
              <div class="ep-desc">User saved library albums</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/albums')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(21, '/library/albums')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-21"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/artists</div>
              <div class="ep-desc">User subscribed artists</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/artists')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(22, '/library/artists')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-22"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-get">GET</span>
            <div>
              <div class="ep-path">/library/uploads</div>
              <div class="ep-desc">Personal cloud uploaded songs</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/uploads')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(23, '/library/uploads')">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-23"></div>
      </div>
    </div>

    <!-- 7. MUTATIONS & ACTIONS -->
    <div class="cat-title">7. Ratings & Playlist Mutations</div>
    <div class="endpoints-list">
      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/library/rate</div>
              <div class="ep-desc">Like / Dislike / Indifferent track rating</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/rate')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(24, '/library/rate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({video_id:'kJQP7kiw5Fk', rating:'LIKE'})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-24"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/library/playlists/create</div>
              <div class="ep-desc">Create a new private or public playlist</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/playlists/create')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(25, '/library/playlists/create', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:'New Music X Mix'})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-25"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/library/playlists/add</div>
              <div class="ep-desc">Add video IDs to existing playlist</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/playlists/add')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(26, '/library/playlists/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({playlist_id:'PL...', video_ids:['kJQP7kiw5Fk']})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-26"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/library/playlists/delete</div>
              <div class="ep-desc">Delete playlist by playlist ID</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/library/playlists/delete')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(27, '/library/playlists/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({playlist_id:'PL...'})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-27"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/artist/subscribe</div>
              <div class="ep-desc">Subscribe to artist channel</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/artist/subscribe')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(28, '/artist/subscribe', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({channel_ids:['UC0C-w0YjGpqDXGB8IHb662A']})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-28"></div>
      </div>

      <div class="ep-card">
        <div class="ep-top-row">
          <div class="ep-meta">
            <span class="badge badge-post">POST</span>
            <div>
              <div class="ep-path">/artist/unsubscribe</div>
              <div class="ep-desc">Unsubscribe from artist channel</div>
            </div>
          </div>
          <div class="ep-actions">
            <button class="btn-sm" onclick="copyEndpoint('/artist/unsubscribe')">Copy</button>
            <button class="btn-sm btn-test" onclick="toggleTest(29, '/artist/unsubscribe', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({channel_ids:['UC0C-w0YjGpqDXGB8IHb662A']})})">Test</button>
          </div>
        </div>
        <div class="inline-json-box" id="json-29"></div>
      </div>
    </div>

    <!-- ONE BOX DIRECT TAP EXPORT -->
    <div class="all-box-container">
      <div class="all-box-title">⚡ ALL 30+ ENDPOINTS INTEGRATION CODE</div>
      <div class="all-box-sub">Tap button to directly copy code (No raw text preview)</div>
      
      <div class="direct-copy-grid">
        <button class="direct-btn" onclick="copyAndroidCode()">
          <!-- Android SVG -->
          <svg viewBox="0 0 24 24"><path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993.0001.5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1521-.5676.416.416 0 00-.5676.1521l-2.0223 3.503C15.5896 8.4312 13.856 8 12 8s-3.5896.4312-5.1368.9497L4.8409 5.4467a.4161.4161 0 00-.5677-.1521.4157.4157 0 00-.1521.5676l1.9973 3.4592C2.6889 11.1867 0 15.1128 0 19.646h24c0-4.5332-2.6889-8.4593-6.1185-10.3246"/></svg>
          Copy Android Kotlin SDK
        </button>

        <button class="direct-btn" onclick="copyWebCode()">
          <!-- Web SVG -->
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
          Copy Web JavaScript SDK
        </button>
      </div>
    </div>

    <!-- FOOTER -->
    <footer>
      <div class="footer-divider"></div>
      <div class="dev-title">DEVELOPER SECTION</div>

      <!-- Developer DP Glass Card -->
      <div class="dev-profile-card">
        <div class="dp-wrapper">
          <img src="https://avatars.githubusercontent.com/u/257059002?v=4" alt="Developer DP" class="dev-dp" loading="lazy" />
          <div class="verified-badge" title="Verified Creator">
            <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
          </div>
        </div>
        <div class="dev-sig" style="margin-bottom:2px;">DEV BY- —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
        <div class="dev-tagline">
          <span>Full Stack • API Architect</span>
        </div>
      </div>
      
      <div class="social-links">
        <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-btn">
          <!-- Telegram SVG -->
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
          Telegram
        </a>
        <a href="https://github.com/Dev0Yadavx?tab=repositories" target="_blank" class="social-btn">
          <!-- GitHub SVG -->
          <svg viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
          GitHub
        </a>
      </div>

      <div class="copyright-txt">All copyrights © reserved —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
      <div class="made-with">Made with ❤️ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
    </footer>

  </div>

  <div class="toast" id="toast">Copied to Clipboard!</div>

  <script>
    // Theme Toggle
    function toggleTheme() {
      const root = document.documentElement;
      const isDark = root.getAttribute('data-theme') === 'dark';
      root.setAttribute('data-theme', isDark ? 'light' : 'dark');
      const icon = document.getElementById('theme-icon');
      icon.innerHTML = isDark 
        ? '<path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1z"/>'
        : '<path d="M12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/>';
    }

    // Toast
    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2000);
    }

    // Universal Robust Copy Helper
    function copyText(str, msg) {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(str).then(() => showToast(msg || "Copied!")).catch(() => fallbackCopy(str, msg));
      } else {
        fallbackCopy(str, msg);
      }
    }

    function fallbackCopy(str, msg) {
      const textArea = document.createElement("textarea");
      textArea.value = str;
      textArea.style.position = "fixed";
      textArea.style.opacity = "0";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        showToast(msg || "Copied!");
      } catch (err) {
        showToast("Copy failed!");
      }
      document.body.removeChild(textArea);
    }

    // Dynamically set Base URL on page load (Local/Cloud auto-detect)
    window.addEventListener('DOMContentLoaded', () => {
      const activeOrigin = window.location.origin;
      const baseValElem = document.getElementById('base-url-val');
      if (baseValElem) {
        baseValElem.innerText = activeOrigin;
      }
    });

    function copyEndpoint(path) {
      const currentHost = window.location.origin;
      copyText(currentHost + path, "Endpoint URL Copied!");
    }

    // Inline Green JSON Test Trigger
    async function toggleTest(idx, url, opts = {}) {
      const box = document.getElementById('json-' + idx);
      if (box.style.display === 'block') {
        box.style.display = 'none';
        return;
      }
      box.style.display = 'block';
      box.innerHTML = `
        <div class="json-actions">
          <span class="json-time">Executing ${(opts.method || "GET")} ${url}...</span>
          <button class="btn-sm btn-close" onclick="document.getElementById('json-${idx}').style.display='none'">Close ✕</button>
        </div>
        <pre class="json-pre">// Requesting YouTube Music live data...</pre>
      `;
      const start = Date.now();
      try {
        const res = await fetch(url, opts);
        const data = await res.json();
        const duration = Date.now() - start;
        box.innerHTML = `
          <div class="json-actions">
            <span class="json-time">HTTP ${res.status} OK • ${duration}ms</span>
            <div style="display:flex; gap:6px;">
              <button class="btn-sm" onclick="copyText(document.getElementById('pre-${idx}').innerText, 'JSON Copied!')">Copy JSON</button>
              <button class="btn-sm btn-close" onclick="document.getElementById('json-${idx}').style.display='none'">Close ✕</button>
            </div>
          </div>
          <pre class="json-pre" id="pre-${idx}">${JSON.stringify(data, null, 2)}</pre>
        `;
      } catch(err) {
        box.innerHTML = `
          <div class="json-actions">
            <span class="json-time" style="color:#ef4444;">Request Failed</span>
            <button class="btn-sm btn-close" onclick="document.getElementById('json-${idx}').style.display='none'">Close ✕</button>
          </div>
          <pre class="json-pre" style="color:#ef4444;">// Error: ${err.message}</pre>
        `;
      }
    }

    // Direct Copy Android Code (ALL 30+ ENDPOINTS)
    function copyAndroidCode() {
      const code = `// Music X API - Android Retrofit Interface (All 30+ Endpoints)
package com.musicx.api

import retrofit2.http.*

interface MusicXApiService {
    @GET("/api/status")
    suspend fun getSystemStatus(): Any

    @GET("/search")
    suspend fun search(@Query("q") q: String, @Query("filter") filter: String? = null, @Query("scope") scope: String? = null): Any

    @GET("/search/suggestions")
    suspend fun getSearchSuggestions(@Query("q") q: String): List<String>

    @GET("/browse/charts")
    suspend fun getCharts(@Query("country") country: String = "IN"): Any

    @GET("/browse/home")
    suspend fun getHomeFeed(@Query("limit") limit: Int = 3): Any

    @GET("/browse/explore")
    suspend fun getExploreFeed(): Any

    @GET("/browse/moods")
    suspend fun getMoodCategories(): Any

    @GET("/browse/mood-playlists/{params}")
    suspend fun getMoodPlaylists(@Path("params") params: String): Any

    @GET("/stream/{videoId}")
    suspend fun getAudioStream(@Path("videoId") videoId: String): Any

    @GET("/song/{videoId}")
    suspend fun getSongDetails(@Path("videoId") videoId: String): Any

    @GET("/song/related/{videoId}")
    suspend fun getRelatedSongs(@Path("videoId") videoId: String): Any

    @GET("/watch/{videoId}")
    suspend fun getWatchQueue(@Path("videoId") videoId: String, @Query("playlistId") playlistId: String? = null, @Query("radio") radio: Boolean = false): Any

    @GET("/lyrics/{id}")
    suspend fun getLyrics(@Path("id") id: String): Any

    @GET("/artist/{channelId}")
    suspend fun getArtistDetails(@Path("channelId") channelId: String): Any

    @GET("/artist/albums/{channelId}/{params}")
    suspend fun getArtistAlbums(@Path("channelId") channelId: String, @Path("params") params: String): Any

    @GET("/album/{browseId}")
    suspend fun getAlbumDetails(@Path("browseId") browseId: String): Any

    @GET("/playlist/{playlistId}")
    suspend fun getPlaylistTracks(@Path("playlistId") playlistId: String, @Query("limit") limit: Int = 100): Any

    @GET("/podcast/{browseId}")
    suspend fun getPodcast(@Path("browseId") browseId: String): Any

    @GET("/episode/{browseId}")
    suspend fun getEpisode(@Path("browseId") browseId: String): Any

    @GET("/library/history")
    suspend fun getHistory(): Any

    @GET("/library/playlists")
    suspend fun getSavedPlaylists(@Query("limit") limit: Int = 25): Any

    @GET("/library/songs")
    suspend fun getLikedSongs(@Query("limit") limit: Int = 25): Any

    @GET("/library/albums")
    suspend fun getSavedAlbums(@Query("limit") limit: Int = 25): Any

    @GET("/library/artists")
    suspend fun getSubscribedArtists(@Query("limit") limit: Int = 25): Any

    @GET("/library/uploads")
    suspend fun getUploadSongs(): Any

    @POST("/library/rate")
    suspend fun rateSong(@Body body: Map<String, String>): Any

    @POST("/library/playlists/create")
    suspend fun createPlaylist(@Body body: Map<String, String>): Any

    @POST("/library/playlists/add")
    suspend fun addToPlaylist(@Body body: Map<String, Any>): Any

    @POST("/library/playlists/delete")
    suspend fun deletePlaylist(@Body body: Map<String, String>): Any

    @POST("/artist/subscribe")
    suspend fun subscribeArtist(@Body body: Map<String, List<String>>): Any

    @POST("/artist/unsubscribe")
    suspend fun unsubscribeArtist(@Body body: Map<String, List<String>>): Any
}`;
      copyText(code, "Android Kotlin SDK Copied!");
    }

    // Direct Copy Web JavaScript Code (ALL 30+ ENDPOINTS)
    function copyWebCode() {
      const code = `// Music X API - Web JavaScript Client (All 30+ Endpoints)
const BASE_URL = window.location.origin;

export const MusicX = {
  getStatus: () => fetch(\`\${BASE_URL}/api/status\`).then(r => r.json()),
  search: (q, filter = "songs", scope = null) => fetch(\`\${BASE_URL}/search?q=\${encodeURIComponent(q)}\${filter ? '&filter=' + filter : ''}\${scope ? '&scope=' + scope : ''}\`).then(r => r.json()),
  getSuggestions: (q) => fetch(\`\${BASE_URL}/search/suggestions?q=\${encodeURIComponent(q)}\`).then(r => r.json()),
  getCharts: (country = "IN") => fetch(\`\${BASE_URL}/browse/charts?country=\${country}\`).then(r => r.json()),
  getHome: (limit = 3) => fetch(\`\${BASE_URL}/browse/home?limit=\${limit}\`).then(r => r.json()),
  getExplore: () => fetch(\`\${BASE_URL}/browse/explore\`).then(r => r.json()),
  getMoods: () => fetch(\`\${BASE_URL}/browse/moods\`).then(r => r.json()),
  getMoodPlaylists: (params) => fetch(\`\${BASE_URL}/browse/mood-playlists/\${params}\`).then(r => r.json()),
  getStreamUrl: (videoId) => fetch(\`\${BASE_URL}/stream/\${videoId}\`).then(r => r.json()),
  getSong: (videoId) => fetch(\`\${BASE_URL}/song/\${videoId}\`).then(r => r.json()),
  getRelated: (videoId) => fetch(\`\${BASE_URL}/song/related/\${videoId}\`).then(r => r.json()),
  getWatchRadio: (videoId, playlistId = null) => fetch(\`\${BASE_URL}/watch/\${videoId}\${playlistId ? '?playlist_id=' + playlistId : ''}\`).then(r => r.json()),
  getLyrics: (id) => fetch(\`\${BASE_URL}/lyrics/\${id}\`).then(r => r.json()),
  getArtist: (channelId) => fetch(\`\${BASE_URL}/artist/\${channelId}\`).then(r => r.json()),
  getArtistAlbums: (channelId, params) => fetch(\`\${BASE_URL}/artist/albums/\${channelId}/\${params}\`).then(r => r.json()),
  getAlbum: (browseId) => fetch(\`\${BASE_URL}/album/\${browseId}\`).then(r => r.json()),
  getPlaylist: (playlistId, limit = 100) => fetch(\`\${BASE_URL}/playlist/\${playlistId}?limit=\${limit}\`).then(r => r.json()),
  getPodcast: (browseId) => fetch(\`\${BASE_URL}/podcast/\${browseId}\`).then(r => r.json()),
  getEpisode: (browseId) => fetch(\`\${BASE_URL}/episode/\${browseId}\`).then(r => r.json()),
  getHistory: () => fetch(\`\${BASE_URL}/library/history\`).then(r => r.json()),
  getLibraryPlaylists: (limit = 25) => fetch(\`\${BASE_URL}/library/playlists?limit=\${limit}\`).then(r => r.json()),
  getLikedSongs: (limit = 25) => fetch(\`\${BASE_URL}/library/songs?limit=\${limit}\`).then(r => r.json()),
  getSavedAlbums: (limit = 25) => fetch(\`\${BASE_URL}/library/albums?limit=\${limit}\`).then(r => r.json()),
  getSubscriptions: (limit = 25) => fetch(\`\${BASE_URL}/library/artists?limit=\${limit}\`).then(r => r.json()),
  getUploads: () => fetch(\`\${BASE_URL}/library/uploads\`).then(r => r.json()),
  rateSong: (videoId, rating = "LIKE") => fetch(\`\${BASE_URL}/library/rate\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ video_id: videoId, rating }) }).then(r => r.json()),
  createPlaylist: (title, description = "") => fetch(\`\${BASE_URL}/library/playlists/create\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, description }) }).then(r => r.json()),
  addToPlaylist: (playlistId, videoIds) => fetch(\`\${BASE_URL}/library/playlists/add\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ playlist_id: playlistId, video_ids: videoIds }) }).then(r => r.json()),
  deletePlaylist: (playlistId) => fetch(\`\${BASE_URL}/library/playlists/delete\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ playlist_id: playlistId }) }).then(r => r.json()),
  subscribeArtist: (channelIds) => fetch(\`\${BASE_URL}/artist/subscribe\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ channel_ids: channelIds }) }).then(r => r.json()),
  unsubscribeArtist: (channelIds) => fetch(\`\${BASE_URL}/artist/unsubscribe\`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ channel_ids: channelIds }) }).then(r => r.json())
};`;
      copyText(code, "Web JavaScript SDK Copied!");
    }
  </script>
</body>
</html>
"""

# ================= FLASK SERVER ROUTES =================

@app.route("/favicon.ico")
def favicon():
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ff2a44"/>
          <stop offset="100%" stop-color="#ffd60a"/>
        </linearGradient>
      </defs>
      <circle cx="50" cy="50" r="48" fill="#07090e" stroke="url(#g)" stroke-width="4"/>
      <path d="M40 30v40l28-20z" fill="url(#g)"/>
    </svg>"""
    from flask import Response
    return Response(svg_icon, mimetype='image/svg+xml')

@app.route("/")
def index():
    return render_template_string(DOCS_HTML)

@app.route("/api/status")
def status():
    return jsonify({"status": "online", "authenticated": authenticated, "auth_source": auth_path if authenticated else "Guest", "total_endpoints": "30+"})

@app.route("/search")
def search():
    q = request.args.get("q")
    if not q: return jsonify({"error": "Param 'q' required"}), 400
    return jsonify(yt.search(query=q, filter=request.args.get("filter"), scope=request.args.get("scope")))

@app.route("/search/suggestions")
def search_suggestions():
    q = request.args.get("q")
    if not q: return jsonify({"error": "Param 'q' required"}), 400
    return jsonify(yt.get_search_suggestions(query=q))

@app.route("/browse/home")
def get_home():
    return jsonify(yt.get_home(limit=int(request.args.get("limit", 3))))

@app.route("/browse/charts")
def get_charts():
    return jsonify(yt.get_charts(country=request.args.get("country", "IN")))

@app.route("/browse/explore")
def get_explore():
    return jsonify(yt.get_explore())

@app.route("/browse/moods")
def get_mood_categories():
    return jsonify(yt.get_mood_categories())

@app.route("/browse/mood-playlists/<params>")
def get_mood_playlists(params):
    return jsonify(yt.get_mood_playlists(params=params))

@app.route("/song/<video_id>")
def get_song(video_id):
    return jsonify(yt.get_song(videoId=video_id))

@app.route("/song/related/<video_id>")
def get_song_related(video_id):
    try:
        watch = yt.get_watch_playlist(videoId=video_id)
        rel = watch.get("related")
        if rel: return jsonify(yt.get_song_related(browseId=rel))
        return jsonify(watch.get("tracks", []))
    except Exception as e:
        return jsonify({"tracks": [], "message": str(e)})

@app.route("/watch/<video_id>")
def get_watch(video_id):
    return jsonify(yt.get_watch_playlist(videoId=video_id, playlistId=request.args.get("playlist_id"), limit=int(request.args.get("limit", 25))))

@app.route("/lyrics/<video_or_browse_id>")
def get_lyrics(video_or_browse_id):
    if len(video_or_browse_id) != 11:
        try: return jsonify(yt.get_lyrics(browseId=video_or_browse_id))
        except Exception: pass
    try:
        w = yt.get_watch_playlist(videoId=video_or_browse_id)
        if w.get("lyrics"): return jsonify(yt.get_lyrics(browseId=w.get("lyrics")))
    except Exception: pass
    return jsonify({"lyrics": None, "source": "YouTube Music", "message": "Lyrics not available"})

@app.route("/stream/<video_id>")
def get_stream(video_id):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return jsonify({
                "id": video_id,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "stream_url": info.get("url"),
                "ext": info.get("ext")
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/artist/<channel_id>")
def get_artist(channel_id):
    try: return jsonify(yt.get_artist(channelId=channel_id))
    except Exception: pass
    search_default = yt.search("Arijit Singh", filter="artists")
    return jsonify(yt.get_artist(channelId=search_default[0]["browseId"]))

@app.route("/artist/albums/<channel_id>/<params>")
def get_artist_albums(channel_id, params):
    return jsonify(yt.get_artist_albums(channelId=channel_id, params=params))

@app.route("/album/<browse_id>")
def get_album(browse_id):
    return jsonify(yt.get_album(browseId=browse_id))

@app.route("/playlist/<playlist_id>")
def get_playlist(playlist_id):
    limit = int(request.args.get("limit", 100))
    try: return jsonify(yt.get_playlist(playlistId=playlist_id, limit=limit))
    except Exception: pass
    if playlist_id.startswith("PL"):
        try: return jsonify(yt.get_playlist(playlistId="VL" + playlist_id, limit=limit))
        except Exception: pass
    return jsonify(yt.get_watch_playlist(playlistId=playlist_id, limit=limit))

@app.route("/podcast/<browse_id>")
def get_podcast(browse_id):
    try: return jsonify(yt.get_podcast(browseId=browse_id))
    except Exception as e: return jsonify({"error": str(e)}), 404

@app.route("/episode/<browse_id>")
def get_episode(browse_id):
    try: return jsonify(yt.get_episode(browseId=browse_id))
    except Exception as e: return jsonify({"error": str(e)}), 404

@app.route("/library/history")
def get_history():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_history())

@app.route("/library/playlists")
def get_library_playlists():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_library_playlists(limit=int(request.args.get("limit", 25))))

@app.route("/library/songs")
def get_library_songs():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_library_songs(limit=int(request.args.get("limit", 25))))

@app.route("/library/albums")
def get_library_albums():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_library_albums(limit=int(request.args.get("limit", 25))))

@app.route("/library/artists")
def get_library_artists():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_library_subscriptions(limit=int(request.args.get("limit", 25))))

@app.route("/library/uploads")
def get_library_uploads():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify(yt.get_library_upload_songs(limit=int(request.args.get("limit", 25))))

@app.route("/library/rate", methods=["POST"])
def rate_song():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    d = request.get_json() or {}
    return jsonify({"status": yt.rate_song(d.get("video_id"), d.get("rating", "LIKE"))})

@app.route("/library/playlists/create", methods=["POST"])
def create_playlist():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    d = request.get_json() or {}
    return jsonify({"status": yt.create_playlist(d.get("title"), d.get("description", ""), d.get("privacy_status", "PRIVATE"))})

@app.route("/library/playlists/add", methods=["POST"])
def add_to_playlist():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    d = request.get_json() or {}
    return jsonify({"status": yt.add_playlist_items(d.get("playlist_id"), d.get("video_ids", []))})

@app.route("/library/playlists/delete", methods=["POST"])
def delete_playlist():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify({"status": yt.delete_playlist(request.get_json().get("playlist_id"))})

@app.route("/artist/subscribe", methods=["POST"])
def subscribe():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify({"status": yt.subscribe_artists(request.get_json().get("channel_ids", []))})

@app.route("/artist/unsubscribe", methods=["POST"])
def unsubscribe():
    if not authenticated: return jsonify({"error": "Auth required"}), 401
    return jsonify({"status": yt.unsubscribe_artists(request.get_json().get("channel_ids", []))})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
