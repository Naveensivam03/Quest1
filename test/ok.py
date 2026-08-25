import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

url = "https://ok.ru/video/248244667877"
options = {
    "outtmpl": "ok_test.%(ext)s",
    "impersonate": ImpersonateTarget.from_str("chrome"),
    "retries": 5,
    "socket_timeout": 30,
}
with yt_dlp.YoutubeDL(options) as ydl:
    ydl.download([url])
print("OK.ru download completed.")
