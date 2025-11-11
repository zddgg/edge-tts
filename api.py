import argparse
import io
from typing import Optional

from starlette.responses import JSONResponse

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.edge_tts import Communicate, list_voices
from src.edge_tts.edge_tts_client import EdgeTTSClient

app = FastAPI()


class TTSRequest(BaseModel):
    text: Optional[str] = Field(default=None)
    voice: Optional[str] = Field(default=None)
    ssml: Optional[str] = Field(default=None)


@app.post("/tts")
async def generate_audio(request: TTSRequest):
    if (not request.text and not request.voice) or (not not request.ssml):
        return JSONResponse(status_code=400, content={"message": "参数错误"})

    text = request.text
    voice = request.voice
    ssml = request.ssml

    try:
        if request.ssml:
            communicate = EdgeTTSClient(ssml)
        else:
            communicate = Communicate(text, voice)

        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

        audio_stream.seek(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(audio_stream, media_type="audio/mp3")


@app.get("/voices")
async def get_voices():
    voices = await list_voices()
    return voices


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI application")
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run the API on')
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=args.port, timeout_keep_alive=120)
