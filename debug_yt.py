import yt_dlp
import os

video_id = 'VMQICBJO47O'
cookie = 'COOKIE/Youtube_Netscape.txt'

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
}

if os.path.exists(cookie):
    ydl_opts['cookiefile'] = cookie
    print(f"Using cookie file: {cookie}")

print(f"Checking formats for: {video_id}")

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # First check with NO format restriction
        info = ydl.extract_info(video_id, download=False)
        formats = info.get('formats', [])
        print(f"Found {len(formats)} formats total.")
        
        # Check if it fails with specific format strings
        for f_str in ["bestaudio/best", "bestvideo+bestaudio/best"]:
            try:
                ydl_opts['format'] = f_str
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_inner:
                    res = ydl_inner.extract_info(video_id, download=False)
                    print(f"Success with format '{f_str}': {res.get('url')[:50] if res.get('url') else 'No direct URL'}")
            except Exception as e:
                print(f"Failed with format '{f_str}': {e}")

except Exception as e:
    print(f"Critical Extraction Error: {e}")
