with open("main.py", "r") as f:
    code = f.read()

# 1. Head tag me SVG favicon inject karna
old_head = '<title>Music x api Docs</title>'
new_head = '''<title>Music x api Docs</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='%23ff2a44'/><stop offset='100%' stop-color='%23ffd60a'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='%2307090e' stroke='url(%23g)' stroke-width='4'/><path d='M40 30v40l28-20z' fill='url(%23g)'/></svg>">'''

if old_head in code:
    code = code.replace(old_head, new_head)

# 2. Browser ke direct /favicon.ico request ke liye route add karna
old_route = '@app.route("/")\ndef index():'
new_route = '''@app.route("/favicon.ico")
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
def index():'''

if old_route in code and "/favicon.ico" not in code:
    code = code.replace(old_route, new_route)

with open("main.py", "w") as f:
    f.write(code)

print("[+] Favicon injected successfully into main.py!")
