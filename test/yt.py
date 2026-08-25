import yt_dlp

url="https://youtu.be/abckzfkg4zI?si=uTTqH478e0gNP0KX"
options = {
    "outtmpl": "video.%(ext)s",
}

with yt_dlp.YoutubeDL(options) as ydl:
    ydl.download([url])

print("Download completed.")
