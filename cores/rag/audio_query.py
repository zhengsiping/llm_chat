import dashscope
import openai
from dashscope.audio.tts_v2 import SpeechSynthesizer
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from dashscope import MultiModalConversation

from cores.rag.query_engin import index_doc, query_with_datastore
from utils.constants import Region
from utils.utils import get_project_root


router = APIRouter()

UPLOAD_DIR = f"{get_project_root()}/uploads"  # Directory to temporarily store uploaded files
OUTPUT_DIR = f"{get_project_root()}/outputs"  # Directory to store generated files
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/api/upload-wav")
async def upload_wav(file: UploadFile = File(...)):
    """
    Uploads a WAV file and returns it as a response.
    """
    if not file.filename.endswith(".wav"):
        return {"error": "Only WAV files are allowed."}

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.environ["Region"] == "US":
        translated = convert_audio_to_text_openai(file_path)
    else:
        translated = convert_audio_to_text_dashscope(file_path)

    ds = index_doc(["雁荡山瞎扯信息.txt"], region=os.environ["Region"])
    response_txt = query_with_datastore(ds, translated, region=os.environ["Region"])

    output_path = os.path.join(OUTPUT_DIR, 'output.mp3')
    if os.environ["Region"] == Region.CHINA:
        convert_text_to_audio_dashscope(response_txt, output_path)
    else:
        convert_text_to_audio_openai(response_txt, output_path)

    return FileResponse(output_path, media_type="audio/mpeg", filename='output.mp3')


def convert_audio_to_text_openai(file_path: str):
    openai.api_key = os.environ["OPENAI_API_KEY"]
    with open(file_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            temperature=0.6,
            prompt="提问的问题可能关于雁荡山，旅游，中国历史，餐饮等"
        )
    translated = transcript.text  # Updated to access text correctly
    return translated


def convert_audio_to_text_dashscope(file_path: str):

    print("File uploaded to:", file_path)

    messages = [
        {
            "role": "user",
            "content": [{"audio": file_path}],
        },
    ]

    response = MultiModalConversation.call(model="qwen-audio-asr", messages=messages,
                                           api_key=os.environ["DASHSCOPE_API_KEY"])
    translated = response["output"]["choices"][0].message['content'][0]['text']
    return translated


def convert_text_to_audio_openai(text: str, output_path: str):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
        input=text
    )
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def convert_text_to_audio_dashscope(text: str, output_path: str):
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
    synthesizer = SpeechSynthesizer(model="cosyvoice-v1", voice="longxiaochun")
    audio = synthesizer.call(text)

    with open(output_path, 'wb') as f:
        f.write(audio)
