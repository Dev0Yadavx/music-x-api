import time
import requests

BASE_URL = "http://127.0.0.1:8000"

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[0m"
B = "\033[1m"

print(f"\n{B}{C}======================================================================{W}")
print(f"{B}{C}     YT MUSIC COMPLETE 25+ ENDPOINTS AUTOMATED COMPREHENSIVE TEST     {W}")
print(f"{B}{C}======================================================================{W}\n")

endpoints = [
    # 1. System
    ("SYSTEM", "/api/status"),
    # 2. Search
    ("SEARCH", "/search?q=Arijit+Singh&filter=songs"),
    ("SEARCH", "/search/suggestions?q=Bhojpuri"),
    # 3. Browse & Discovery
    ("BROWSE", "/browse/charts?country=IN"),
    ("BROWSE", "/browse/home?limit=2"),
    ("BROWSE", "/browse/explore"),
    ("BROWSE", "/browse/moods"),
    # 4. Tracks & Media
    ("TRACK", "/song/kJQP7kiw5Fk"),
    ("TRACK", "/watch/kJQP7kiw5Fk"),
    ("TRACK", "/song/related/kJQP7kiw5Fk"),
    ("TRACK", "/lyrics/kJQP7kiw5Fk"),
    ("STREAM", "/stream/kJQP7kiw5Fk"),
    # 5. Artists & Entities
    ("ENTITY", "/artist/UC0C-w0YjGpqDXGB8IHb662A"),
    ("ENTITY", "/playlist/PL4fGSI1pDJn6jXS_PE_xWDwO565Ca9yVO"),
    ("ENTITY", "/playlist/RDCLAK5uy_kfdxRPFiMS06TvTT9xLqvHG7ZyvW64t80"),
    # 6. Library (Private Auth)
    ("LIBRARY", "/library/history"),
    ("LIBRARY", "/library/playlists"),
    ("LIBRARY", "/library/songs"),
    ("LIBRARY", "/library/albums"),
    ("LIBRARY", "/library/artists"),
    ("LIBRARY", "/library/channels"),
    ("LIBRARY", "/library/podcasts"),
    ("LIBRARY", "/library/uploads"),
    ("LIBRARY", "/library/upload-artists"),
    ("LIBRARY", "/library/upload-albums"),
]

passed = 0
failed = 0

for category, path in endpoints:
    url = f"{BASE_URL}{path}"
    start = time.time()
    try:
        res = requests.get(url, timeout=16)
        elapsed = int((time.time() - start) * 1000)
        
        if res.status_code == 200:
            passed += 1
            status_text = f"{G}[PASS 200]{W}"
        elif res.status_code == 401:
            failed += 1
            status_text = f"{Y}[AUTH 401]{W}"
        else:
            failed += 1
            status_text = f"{R}[FAIL {res.status_code}]{W}"

        print(f"{B}[{category:<9}]{W} {path:<53} {status_text} ({elapsed}ms)")
    except Exception as e:
        failed += 1
        elapsed = int((time.time() - start) * 1000)
        print(f"{B}[{category:<9}]{W} {path:<53} {R}[ERROR]{W} ({elapsed}ms)")

print(f"\n{B}{C}======================================================================{W}")
print(f"  TOTAL ENDPOINTS TESTED : {passed + failed}")
print(f"  {G}WORKING (PASS)         {W} : {passed}")
print(f"  {R}FAILED / REQUIRES AUTH {W} : {failed}")
print(f"{B}{C}======================================================================{W}\n")
