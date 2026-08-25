from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.dialogue import find_dialogue
from services.pipeline import process_video
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files such as extracted frames.
app.mount(
    "/outputs",
    StaticFiles(directory="outputs"),
    name="outputs",
)


class DialogueRequest(BaseModel):
    video_url: str
    dialogue: str


@app.get("/")
def root():
    return {"message": "quest video dialogue finder"}


@app.post("/find-dialogue")
def find_dialogue_endpoint(request: DialogueRequest):
    # 1. Prepare the video and transcript.
    video = process_video(request.video_url)

    # 2. Find the requested dialogue and extract its exact frame.
    result = find_dialogue(
        video_id=video["video_id"],
        target_text=request.dialogue,
    )

    # 3. Dialogue was not found.
    if result is None:
        return {
            "success": False,
            "message": "Dialogue not found in the video transcript.",
        }

    # 4. Convert the server filesystem path into a browser URL.
    frame_path = Path(result["frame_path"])
    frame_url = "/" + frame_path.as_posix()

    return {
        "success": True,
        "video_id": result["video_id"],
        "video_url": f"/outputs/{result['video_id']}/video.mp4",
        "text": result["text"],
        "start_time": result["start_time"],
        "end_time": result["end_time"],
        "frame_number": result["frame_number"],
        "frame_timestamp": result["frame_timestamp"],
        "frame_url": frame_url,
    }
