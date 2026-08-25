from services.pipeline import process_video


# url = "https://ok.ru/video/248244667877"
url = "https://youtu.be/abckzfkg4zI?si=vHwAWbKlfq_2eLWE"
result = process_video(url)

print("\nResult:")
print(f"Video ID:  {result['video_id']}")
print(f"Status:    {result['status']}")
print(f"File:      {result['file_path']}")
print(f"Cached:    {result['audio_path']}")
