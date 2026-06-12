import os
import time
import asyncio
import random
import urllib.request
import urllib.parse
import re
import json
import ssl
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
from concurrent.futures import ThreadPoolExecutor
from config import Config

executor = ThreadPoolExecutor(max_workers=5)

# Proxy Circuit Breaker state
proxy_failures = 0
last_proxy_failure = 0
PROXY_COOLDOWN = 300  # 5 minutes

def mark_proxy_failure():
    global proxy_failures, last_proxy_failure
    proxy_failures += 1
    last_proxy_failure = time.time()
    print(f"Proxy failure marked. Consecutive failures: {proxy_failures}")

def mark_proxy_success():
    global proxy_failures
    if proxy_failures > 0:
        proxy_failures = 0
        print("Proxy success marked. Resetting failure counter.")

def get_active_proxy():
    global proxy_failures, last_proxy_failure
    if proxy_failures >= 3:
        elapsed = time.time() - last_proxy_failure
        if elapsed < PROXY_COOLDOWN:
            return None
        else:
            proxy_failures = 0
    return get_formatted_proxy()

def get_formatted_proxy():
    proxy = os.getenv("PROXY")
    if not proxy:
        proxy_file = "PROXY/Webshare 10 proxies.txt"
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, "r") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        import random
                        proxy = random.choice(lines)
            except Exception as e:
                print(f"Failed to read proxy file: {e}")
    if not proxy:
        return None
    proxy = proxy.strip()
    if not (proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks5://") or proxy.startswith("socks4://")):
        parts = proxy.split(":")
        if len(parts) == 4:
            return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return proxy

def urlopen_with_proxy(req, timeout=8, context=None):
    proxy_url = get_active_proxy()
    if proxy_url:
        try:
            handlers = [urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})]
            if context is not None:
                handlers.append(urllib.request.HTTPSHandler(context=context))
            opener = urllib.request.build_opener(*handlers)
            res = opener.open(req, timeout=timeout)
            mark_proxy_success()
            return res
        except Exception as proxy_err:
            mark_proxy_failure()
            print(f"Proxy connection failed ({proxy_err}), falling back to direct connection.")
            
    # Direct fallback: Reconstruct request to remove proxy mutations if req is a Request object
    if isinstance(req, urllib.request.Request):
        headers = dict(req.headers)
        # Remove any proxy headers
        for h in list(headers.keys()):
            if h.lower().startswith('proxy-'):
                del headers[h]
        
        method = getattr(req, 'method', None)
        if method is None and hasattr(req, 'get_method'):
            try:
                method = req.get_method()
            except Exception:
                pass

        fallback_req = urllib.request.Request(
            req.full_url,
            data=req.data,
            headers=headers,
            origin_req_host=req.origin_req_host,
            unverifiable=req.unverifiable,
            method=method
        )
        if hasattr(req, 'unredirected_hdrs'):
            fallback_req.unredirected_hdrs = {
                k: v for k, v in req.unredirected_hdrs.items()
                if not k.lower().startswith('proxy-')
            }
        req = fallback_req

    if context is not None:
        return urllib.request.urlopen(req, timeout=timeout, context=context)
    return urllib.request.urlopen(req, timeout=timeout)

def urlopen_direct(req, timeout=8, context=None):
    if context is not None:
        return urllib.request.urlopen(req, timeout=timeout, context=context)
    return urllib.request.urlopen(req, timeout=timeout)

def is_stream_url_alive(url: str) -> bool:
    if not url:
        return False
    if os.path.exists(url):
        return True
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Range": "bytes=0-1024"
            }
        )
        with urllib.request.urlopen(req, context=ctx, timeout=3.0) as resp:
            status = resp.getcode()
            if status not in (200, 206):
                return False
            cl = resp.getheader("Content-Length")
            if cl is not None:
                try:
                    if int(cl) == 0:
                        return False
                except ValueError:
                    pass
            first_chunk = resp.read(10)
            if len(first_chunk) == 0:
                return False
            return True
    except Exception as e:
        print(f"Stream URL health check failed for {url[:50]}: {e}")
        return False

def is_playlist(url: str) -> bool:
    if "list=" in url or "playlist" in url:
        return True
    return False

def get_video_id(url):
    if not url:
        return None
    reg = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})'
    match = re.search(reg, url)
    if match:
        return match.group(1)
    if len(url) == 11 and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in url):
        return url
    return None

def get_dynamic_piped_instances():
    try:
        url = "https://raw.githubusercontent.com/TeamPiped/documentation/main/content/docs/public-instances/index.md"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen_direct(req, timeout=5) as response:
            content = response.read().decode('utf-8')
            apis = re.findall(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9.-]+)*', content)
            seen = set()
            cleaned = []
            for x in apis:
                if any(bad in x for bad in ["/registered", "/badge", "github.com", "piped.video"]):
                    continue
                if ("pipedapi" in x or "piped-api" in x or "api.piped" in x) and x not in seen:
                    seen.add(x)
                    cleaned.append(x)
            # Prioritize known working instances
            priority = ["https://api.piped.private.coffee"]
            for p in priority:
                if p in cleaned:
                    cleaned.remove(p)
                cleaned.insert(0, p)
            return cleaned
    except Exception as e:
        print(f"Failed to fetch Piped instances: {e}")
    return []

_invidious_instances_cache = []
_invidious_instances_cache_time = 0

def get_dynamic_invidious_instances():
    global _invidious_instances_cache, _invidious_instances_cache_time
    now = time.time()
    if _invidious_instances_cache and (now - _invidious_instances_cache_time < 1800):
        return _invidious_instances_cache

    instances_list = []
    try:
        url = "https://api.invidious.io/instances.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl._create_unverified_context()
        with urlopen_direct(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            temp_list = []
            for item in data:
                domain = item[0]
                details = item[1]
                if details.get("type") != "https":
                    continue
                
                monitor = details.get("monitor")
                last_status = monitor.get("last_status") if monitor else None
                if last_status != 200:
                    continue
                
                stats = details.get("stats")
                playback = stats.get("playback", {}) if stats else {}
                ratio = playback.get("ratio", -1.0) if playback else -1.0
                
                uri = details.get("uri")
                if uri:
                    temp_list.append((uri, ratio))
            
            def sort_key(x):
                ratio = x[1]
                if ratio == -1.0:
                    return 0.1
                return ratio
            
            temp_list.sort(key=sort_key, reverse=True)
            instances_list = [x[0] for x in temp_list]
    except Exception as e:
        print(f"Failed to fetch invidious instances from API: {e}")
        
    if not instances_list:
        instances_list = [
            "https://inv.thepixora.com",
            "https://inv.nadeko.net",
            "https://invidious.nerdvpn.de",
            "https://invidious.tiekoetter.com",
            "https://invidious.f5.si",
            "https://yt.chocolatemoo53.com"
        ]
    else:
        for fallback in ["https://inv.thepixora.com"]:
            if fallback in instances_list:
                instances_list.remove(fallback)
            instances_list.insert(0, fallback)
            
    _invidious_instances_cache = instances_list
    _invidious_instances_cache_time = now
    return instances_list

def proxy_googlevideo_url(url: str) -> str:
    if not url or "googlevideo.com" not in url:
        return url
        
    instances = get_dynamic_invidious_instances()
    if not instances:
        return url
        
    base_instance = random.choice(instances[:min(3, len(instances))])
    
    match = re.search(r'/videoplayback\?.*', url)
    if match:
        return f"{base_instance}{match.group(0)}"
    return url

def search_alt_piped(query):
    piped_instances = get_dynamic_piped_instances()
    if not piped_instances:
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.leptons.xyz",
            "https://pipedapi.nosebs.ru",
            "https://piped-api.privacy.com.de",
            "https://pipedapi.adminforge.de",
            "https://api.piped.yt",
        ]
    encoded_query = urllib.parse.quote_plus(query)
    for base in piped_instances[:8]:
        try:
            url = f"{base}/search?q={encoded_query}&filter=videos"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen_with_proxy(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = data.get("items", [])
                for item in results:
                    if item.get("type") == "stream" and item.get("url"):
                        video_id = get_video_id(item["url"])
                        if video_id:
                            return video_id
        except Exception as e:
            print(f"Piped Search Error on {base}: {e}")
    return None

def search_alt_invidious(query):
    invidious_instances = get_dynamic_invidious_instances()
    if not invidious_instances:
        invidious_instances = [
            "https://inv.nadeko.net",
            "https://invidious.nerdvpn.de",
            "https://inv.thepixora.com",
            "https://yt.chocolatemoo53.com",
            "https://invidious.tiekoetter.com",
            "https://invidious.f5.si",
        ]
    encoded_query = urllib.parse.quote_plus(query)
    for base in invidious_instances[:8]:
        try:
            url = f"{base}/api/v1/search?q={encoded_query}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen_with_proxy(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                for item in data:
                    if item.get("type") == "video" and item.get("videoId"):
                        return item["videoId"]
        except Exception as e:
            print(f"Invidious Search Error on {base}: {e}")
    return None

def search_youtube_alt(query):
    # Try Piped search first
    video_id = search_alt_piped(query)
    if video_id:
        return video_id
    # Try Invidious search fallback
    return search_alt_invidious(query)

def extract_from_piped(video_id, is_video=False):
    piped_instances = get_dynamic_piped_instances()
    if not piped_instances:
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.leptons.xyz",
            "https://pipedapi.nosebs.ru",
            "https://piped-api.privacy.com.de",
            "https://pipedapi.adminforge.de",
            "https://api.piped.yt",
        ]
    for base in piped_instances[:12]:
        try:
            url = f"{base}/streams/{video_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen_with_proxy(req, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                selected_stream = None
                if is_video:
                    video_streams = [s for s in data.get("videoStreams", []) if not s.get("videoOnly", False)]
                    if video_streams:
                        selected_stream = video_streams[0]
                        for s in video_streams:
                            quality = s.get("quality", "")
                            if "720p" in quality or "480p" in quality or "360p" in quality:
                                selected_stream = s
                                break
                else:
                    audio_streams = data.get("audioStreams", [])
                    if audio_streams:
                        for s in audio_streams:
                            codec = s.get("codec", "").lower()
                            mime = s.get("mimeType", "").lower()
                            if "m4a" in codec or "m4a" in mime or "mp4" in mime:
                                selected_stream = s
                                break
                        if not selected_stream:
                            selected_stream = audio_streams[-1]
                    
                    if not selected_stream:
                        video_streams = [s for s in data.get("videoStreams", []) if not s.get("videoOnly", False)]
                        if video_streams:
                            selected_stream = video_streams[0]
                            
                if selected_stream:
                    return {
                        "url": selected_stream["url"],
                        "title": data.get("title", "Unknown"),
                        "duration_sec": data.get("duration", 0),
                        "thumbnail": data.get("thumbnailUrl")
                    }
        except Exception as e:
            print(f"Piped Extraction Error on {base}: {e}")
    return None

def extract_from_invidious(video_id, is_video=False):
    invidious_instances = get_dynamic_invidious_instances()
    if not invidious_instances:
        invidious_instances = [
            "https://inv.nadeko.net",
            "https://invidious.nerdvpn.de",
            "https://inv.thepixora.com",
            "https://yt.chocolatemoo53.com",
            "https://invidious.tiekoetter.com",
            "https://invidious.f5.si",
        ]
    for base in invidious_instances[:12]:
        try:
            url = f"{base}/api/v1/videos/{video_id}?local=true"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen_with_proxy(req, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                title = data.get("title", "Unknown")
                duration_sec = data.get("lengthSeconds", 0)
                thumbnails = data.get("videoThumbnails", [])
                thumbnail = thumbnails[0].get("url") if thumbnails else None
                
                selected_stream = None
                if is_video:
                    format_streams = data.get("formatStreams", [])
                    if format_streams:
                        selected_stream = format_streams[-1]
                else:
                    adaptive = data.get("adaptiveFormats", [])
                    audio_streams = [a for a in adaptive if "audio" in a.get("type", "").lower() or "audio" in a.get("mimeType", "").lower()]
                    if audio_streams:
                        for s in audio_streams:
                            mime = s.get("mimeType", "").lower()
                            if "m4a" in mime or "mp4" in mime or "aac" in mime:
                                selected_stream = s
                                break
                        if not selected_stream:
                            selected_stream = audio_streams[0]
                    
                    if not selected_stream:
                        format_streams = data.get("formatStreams", [])
                        if format_streams:
                            selected_stream = format_streams[-1]
                            
                if selected_stream:
                    stream_url = selected_stream["url"]
                    if not stream_url.startswith(("http://", "https://")):
                        if not stream_url.startswith("/"):
                            stream_url = "/" + stream_url
                        stream_url = f"{base}{stream_url}"
                    elif "googlevideo.com" in stream_url:
                        match = re.search(r'/videoplayback\?.*', stream_url)
                        if match:
                            stream_url = f"{base}{match.group(0)}"
                    elif stream_url.startswith("http://") and base.startswith("https://"):
                        stream_url = stream_url.replace("http://", "https://", 1)
                    
                    return {
                        "url": stream_url,
                        "title": title,
                        "duration_sec": duration_sec,
                        "thumbnail": thumbnail
                    }
        except Exception as e:
            print(f"Invidious Extraction Error on {base}: {e}")
    return None

def extract_from_cobalt(video_id, is_video=False):
    cobalt_api = os.getenv("COBALT_API")
    instances = []
    if cobalt_api:
        instances.append(cobalt_api.strip().rstrip("/"))
    
    # Fallback community instances
    instances.extend([
        "https://dog.kittycat.boo",
        "https://rue-cobalt.xenon.zone",
        "https://cobalt.adminforge.de",
        "https://cobalt-api.adminforge.de",
        "https://api.cobalt.tools"
    ])
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    for base in instances:
        try:
            url = base if base.endswith("/") else base + "/"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            payload = {
                "url": video_url,
                "videoQuality": "720",
                "downloadMode": "audio" if not is_video else "auto",
                "audioFormat": "mp3"
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            ctx = ssl._create_unverified_context()
            with urlopen_with_proxy(req, context=ctx, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
                stream_url = data.get("url")
                if stream_url:
                    return {
                        "url": stream_url,
                        "title": data.get("filename", "Cobalt Stream"),
                        "duration_sec": 0,
                        "thumbnail": None
                    }
        except Exception as e:
            print(f"Cobalt Extraction Error on {base}: {e}")
    return None

def get_jiosaavn_stream_info(query: str):
    """Fetch direct stream URL from JioSaavn public API."""
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://saavn.dev/api/search/songs?query={encoded_query}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        
        with urlopen_with_proxy(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success") and data.get("data") and data["data"].get("results"):
                song = data["data"]["results"][0]
                download_urls = song.get("downloadUrl", [])
                if download_urls:
                    direct_url = download_urls[-1].get("url")
                    duration_sec = int(song.get("duration", 0))
                    duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                    images = song.get("image", [])
                    thumbnail = images[-1].get("url") if images else None
                    
                    return {
                        "url": direct_url,
                        "audio_url": None,
                        "title": song.get("name", "JioSaavn Track"),
                        "duration": duration_min,
                        "duration_sec": duration_sec,
                        "thumbnail": thumbnail,
                        "is_video": False,
                        "yt_url": f"https://www.jiosaavn.com/song/{song.get('id')}"
                    }
    except Exception as e:
        print(f"JioSaavn Extraction Error: {e}")
    return None

def get_stream_info(query, is_video=False):
    # Local File Bypass
    if os.path.exists(query):
        title = os.path.basename(query)
        return {
            "url": query,
            "audio_url": None,
            "title": title,
            "duration": "00:00",
            "duration_sec": 0,
            "thumbnail": None,
            "is_video": is_video or query.lower().endswith((".mp4", ".mkv")),
            "yt_url": query
        }

    # Direct Stream Link Bypass (Bypass yt-dlp entirely for raw URLs)
    lower_query = query.lower()
    if query.startswith(("http://", "https://")) and (
        any(ext in lower_query for ext in [".mp4", ".mkv", ".m3u8", ".mp3", ".m4a", ".aac"]) or 
        any(param in lower_query for param in [".mp4?", ".m3u8?", ".mp3?"])
    ):
        filename = query.split("/")[-1].split("?")[0]
        title = filename if filename else "Direct Stream"
        return {
            "url": query,
            "audio_url": None,
            "title": title,
            "duration": "Live" if ".m3u8" in lower_query else "00:00",
            "duration_sec": 0,
            "thumbnail": None,
            "is_video": is_video or any(ext in lower_query for ext in [".mp4", ".mkv", ".m3u8"]),
            "yt_url": query
        }

    if query.startswith("saavn:"):
        saavn_query = query[6:].strip()
        info = get_jiosaavn_stream_info(saavn_query)
        if info:
            return info
        query = saavn_query

    # Determine which cookie file to use
    cookie_file = "COOKIE/Youtube_Netscape.txt"
    if "spotify.com" in query:
        cookie_file = "COOKIE/Spotify_Netscape.txt"
        
    # Spotify URL to YouTube Search Conversion
    if "spotify.com/track" in query or "spotify.com/playlist" in query or "spotify.com/album" in query:
        try:
            req = urllib.request.Request(query, headers={'User-Agent': 'Mozilla/5.0'})
            html_content = urlopen_direct(req).read().decode('utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html_content)
            if title_match:
                scrape_title = title_match.group(1).replace('| Spotify', '').replace('Song by', '').replace('Playlist by', '').strip()
                query = scrape_title
        except Exception as e:
            print(f"Spotify Scrape Error: {e}")
    
    # Fast Search Optimization
    if not (query.startswith("http") or query.startswith("www")):
        if query.startswith("sc:"):
            query = f"scsearch1:{query[3:].strip()}"
        else:
            resolved_link = None
            try:
                search = VideosSearch(query, limit=1)
                res = search.result()
                if res and res.get("result"):
                    resolved_link = res["result"][0]["link"]
            except Exception as e:
                print(f"VideosSearch failed: {e}")
            
            if resolved_link:
                query = resolved_link
            else:
                # Fallback to alternative search APIs (Piped / Invidious search) as MAIN search fallback
                resolved_id = search_youtube_alt(query)
                if resolved_id:
                    query = f"https://www.youtube.com/watch?v={resolved_id}"

    video_id = get_video_id(query)
    if video_id:
        try:
            cobalt_res = extract_from_cobalt(video_id, is_video=is_video)
            if cobalt_res and is_stream_url_alive(cobalt_res["url"]):
                duration_sec = cobalt_res.get("duration_sec", 0)
                duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                return {
                    "url": cobalt_res["url"],
                    "audio_url": None,
                    "title": cobalt_res["title"],
                    "duration": duration_min,
                    "duration_sec": duration_sec,
                    "thumbnail": cobalt_res.get("thumbnail"),
                    "is_video": is_video,
                    "yt_url": f"https://www.youtube.com/watch?v={video_id}"
                }
        except Exception as e:
            print(f"Cobalt Main Extraction failed: {e}")

        try:
            piped_res = extract_from_piped(video_id, is_video=is_video)
            if piped_res and is_stream_url_alive(piped_res["url"]):
                duration_sec = piped_res.get("duration_sec", 0)
                duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                return {
                    "url": piped_res["url"],
                    "audio_url": None,
                    "title": piped_res["title"],
                    "duration": duration_min,
                    "duration_sec": duration_sec,
                    "thumbnail": piped_res.get("thumbnail"),
                    "is_video": is_video,
                    "yt_url": f"https://www.youtube.com/watch?v={video_id}"
                }
        except Exception as e:
            print(f"Piped Main Extraction failed: {e}")

        try:
            invidious_res = extract_from_invidious(video_id, is_video=is_video)
            if invidious_res and is_stream_url_alive(invidious_res["url"]):
                duration_sec = invidious_res.get("duration_sec", 0)
                duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                return {
                    "url": invidious_res["url"],
                    "audio_url": None,
                    "title": invidious_res["title"],
                    "duration": duration_min,
                    "duration_sec": duration_sec,
                    "thumbnail": invidious_res.get("thumbnail"),
                    "is_video": is_video,
                    "yt_url": f"https://www.youtube.com/watch?v={video_id}"
                }
        except Exception as e:
            print(f"Invidious Main Extraction failed: {e}")

    # Final Fallback: yt-dlp Extraction
    ydl_opts = {
        'format': "bestvideo+bestaudio/best" if is_video else "bestaudio/best",
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
        'noplaylist': True,
        'default_search': 'auto',
        'cookiefile': cookie_file,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'protocols': ['dashy'],
                'player_client': ['android', 'web']
            }
        }
    }
    proxy = get_active_proxy()
    if proxy:
        ydl_opts['proxy'] = proxy
    
    def extract_with_opts(opts, q):
        with YoutubeDL(opts) as ydl:
            return ydl.extract_info(q, download=False)

    try:
        info = extract_with_opts(ydl_opts, query)
    except Exception:
        # Fallback: Try without cookies, proxy, and relaxation
        ydl_opts.pop('cookiefile', None)
        ydl_opts.pop('proxy', None)
        try:
            info = extract_with_opts(ydl_opts, query)
        except Exception as final_err:
            raise final_err

    duration_sec = info.get('duration', 0)
    duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
    
    stream_url = info.get('url')
    # If using bestvideo+bestaudio, yt-dlp might provide direct format URLs
    if not stream_url and 'formats' in info:
        formats = info['formats']
        if is_video:
            # Prefer 720p or lower for bandwidth
            v_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            if not v_formats:
                v_formats = formats
            stream_url = v_formats[-1]['url']
        else:
            a_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if not a_formats:
                a_formats = formats
            stream_url = a_formats[-1]['url']

    return {
        "url": stream_url,
        "audio_url": None,
        "title": info.get('title', 'Unknown'),
        "duration": duration_min,
        "duration_sec": duration_sec,
        "thumbnail": info.get('thumbnail'),
        "is_video": is_video,
        "yt_url": info.get('webpage_url', query)
    }
