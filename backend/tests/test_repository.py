from db.database import SessionLocal
from db.repository import create_video, get_video_by_url


url = "https://ok.ru/video/248244667877"


with SessionLocal() as session:

    video = get_video_by_url(session, url)

    if video:
        print("Video already exists:")
        print(f"ID:     {video.id}")
        print(f"URL:    {video.url}")
        print(f"Status: {video.status}")

    else:
        video = create_video(session, url)

        print("Video created:")
        print(f"ID:     {video.id}")
        print(f"URL:    {video.url}")
        print(f"Status: {video.status}")
