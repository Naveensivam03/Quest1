from services.downloader import download_video

# url = "https://ok.ru/video/248244667877"
url = "https://youtu.be/dPTKl5H5ftg?si=w8tnZ4JeEJAGOJyw"

video_id, video_path = download_video(url)

print(f"\nDownloaded successfully:")
print(video_path)
print(video_id)
