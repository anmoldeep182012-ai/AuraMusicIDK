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
from pytubefix import YouTube
from sclib import SoundcloudAPI, Track
from youtubesearchpython import VideosSearch
from concurrent.futures import ThreadPoolExecutor
from config import Config

executor = ThreadPoolExecutor(max_workers=10)
sc_api = SoundcloudAPI()

def is_stream_url_alive(url: str) -> bool:
    if not url: return False
    if os.path.exists(url): return True
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-1024"})
        with urllib.request.urlopen(req, context=ctx, timeout=2.0) as resp:
            return resp.getcode() in (200, 206)
    except: return False

def get_video_id(url):
    if not url: return None
    reg = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})'
    match = re.search(reg, url)
    return match.group(1) if match else (url if len(url) == 11 else None)

def is_playlist(url: str) -> bool:
    if "list=" in url or "playlist" in url:
        return True
    return False

def extract_with_pytubefix(video_id, is_video=False):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
        if is_video:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        else:
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        if stream:
            return {"url": stream.url, "title": yt.title, "duration_sec": yt.length, "thumbnail": yt.thumbnail_url}
    except: pass
    return None

def proxy_googlevideo_url(url: str) -> str:
    # Not actually a true proxy, just redirecting through a front-end instance for UI playback if needed. 
    # But since user wants no proxy, we return original url.
    return url

def extract_from_piped(video_id, is_video=False):
    instances = ["https://api.piped.private.coffee", "https://pipedapi.kavin.rocks", "https://pipedapi.leptons.xyz"]
    for base in instances:
        try:
            url = f"{base}/streams/{video_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                streams = data.get("audioStreams", []) if not is_video else data.get("videoStreams", [])
                if streams:
                    return {"url": streams[0]["url"], "title": data.get("title", "Piped"), "duration_sec": data.get("duration", 0), "thumbnail": data.get("thumbnailUrl")}
        except: pass
    return None

def extract_from_invidious(video_id, is_video=False):
    instances = ["https://inv.thepixora.com", "https://inv.nadeko.net", "https://invidious.nerdvpn.de"]
    for base in instances:
        try:
            url = f"{base}/api/v1/videos/{video_id}?local=true"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                adaptive = data.get("adaptiveFormats", [])
                streams = [a for a in adaptive if "audio" in a.get("type", "").lower()] if not is_video else data.get("formatStreams", [])
                if streams:
                    return {"url": streams[0]["url"], "title": data.get("title", "Invidious"), "duration_sec": data.get("lengthSeconds", 0), "thumbnail": data.get("videoThumbnails", [{}])[0].get("url")}
        except: pass
    return None

def extract_from_cobalt(video_id, is_video=False):
    instances = ["https://api.cobalt.tools", "https://dog.kittycat.boo", "https://rue-cobalt.xenon.zone"]
    for base in instances:
        try:
            payload = {"url": f"https://www.youtube.com/watch?v={video_id}", "videoQuality": "720", "downloadMode": "audio" if not is_video else "auto"}
            req = urllib.request.Request(base, data=json.dumps(payload).encode("utf-8"), headers={"Accept": "application/json", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("url"): return {"url": data["url"], "title": "Cobalt Stream", "duration_sec": 0, "thumbnail": None}
        except: pass
    return None

async def extract_from_soundcloud(url):
    try:
        loop = asyncio.get_event_loop()
        track = await loop.run_in_executor(executor, lambda: sc_api.resolve(url))
        if isinstance(track, Track):
            stream_url = await loop.run_in_executor(executor, lambda: track.get_stream_url())
            return {"url": stream_url, "title": track.title, "duration": f"{track.duration // 60000}:{(track.duration // 1000) % 60:02d}", "duration_sec": track.duration // 1000, "thumbnail": track.artwork_url, "is_video": False, "yt_url": url}
    except: pass
    return None

async def get_stream_info(query, is_video=False):
    if os.path.exists(query):
        return {"url": query, "title": os.path.basename(query), "duration": "00:00", "duration_sec": 0, "thumbnail": None, "is_video": is_video or query.lower().endswith((".mp4", ".mkv")), "yt_url": query}
    if "soundcloud.com" in query:
        info = await extract_from_soundcloud(query)
        if info: return info

    lower_query = query.lower()
    if query.startswith(("http://", "https://")) and any(ext in lower_query for ext in [".mp4", ".mkv", ".m3u8", ".mp3", ".m4a"]):
        return {"url": query, "title": "Direct Stream", "duration": "Live" if ".m3u8" in lower_query else "00:00", "duration_sec": 0, "thumbnail": None, "is_video": is_video or any(ext in lower_query for ext in [".mp4", ".mkv", ".m3u8"]), "yt_url": query}

    if not (query.startswith("http") or query.startswith("www")):
        try:
            search = VideosSearch(query, limit=1)
            res = search.result()
            if res and res.get("result"): query = res["result"][0]["link"]
        except: pass

    video_id = get_video_id(query)
    if not video_id: return None

    loop = asyncio.get_event_loop()
    pt_res = await loop.run_in_executor(executor, extract_with_pytubefix, video_id, is_video)
    if pt_res and is_stream_url_alive(pt_res["url"]):
        return {**pt_res, "duration": f"{pt_res['duration_sec'] // 60}:{pt_res['duration_sec'] % 60:02d}", "is_video": is_video, "yt_url": f"https://www.youtube.com/watch?v={video_id}"}

    async def fast_extract(func, *args):
        try:
            res = await loop.run_in_executor(executor, func, *args)
            if res and is_stream_url_alive(res["url"]): return res
        except: return None

    tasks = [fast_extract(extract_from_cobalt, video_id, is_video), fast_extract(extract_from_piped, video_id, is_video), fast_extract(extract_from_invidious, video_id, is_video)]
    done, pending = await asyncio.wait([asyncio.create_task(t) for t in tasks], return_when=asyncio.FIRST_COMPLETED, timeout=4.0)
    for task in done:
        res = task.result()
        if res:
            for p in pending: p.cancel()
            return {**res, "duration": f"{res.get('duration_sec', 0) // 60}:{res.get('duration_sec', 0) % 60:02d}", "is_video": is_video, "yt_url": f"https://www.youtube.com/watch?v={video_id}"}

    ydl_opts = {'format': "bestaudio/best" if not is_video else "best", 'quiet': True, 'no_warnings': True, 'noplaylist': True, 'cookiefile': "COOKIE/Youtube_Netscape.txt"}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(executor, lambda: ydl.extract_info(query, download=False))
            return {"url": info.get('url'), "title": info.get('title', 'Unknown'), "duration": f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}", "duration_sec": info.get('duration', 0), "thumbnail": info.get('thumbnail'), "is_video": is_video, "yt_url": info.get('webpage_url', query)}
    except: return None
