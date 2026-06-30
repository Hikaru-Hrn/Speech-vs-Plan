from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List
from pydantic import BaseModel
import json
import os
import shutil
from pathlib import Path
from md_docx_to_json import plan_to_json
from transcribe import transcribe_audio_file
from analyze import ask_with_file_content
from dotenv import load_dotenv

LECTURES_JSONS_DIR = "lectures"
TRANSCRIPTS_DIR = "lectures_transcripts"
UPLOADED_AUDIOFILES_DIR = "lectures_audiofiles"
UPLOADED_PLANS_DIR = "uploaded_plans"
COMPARISON_JSONS_DIR = "lectures_comparisons"

FILES_TO_PROCESS = {
    "lecture_plan": None,
    "lecture_audiofile": None,
    "lecture_transcript": None,
    "lecture_comparison": None
}

load_dotenv()
templates = Jinja2Templates(directory="templates/html")
app = FastAPI()

app.mount("/css", StaticFiles(directory="templates/css"), name="css")
app.mount("/js", StaticFiles(directory="templates/js"), name="js")
app.mount("/fonts", StaticFiles(directory="templates/fonts"), name="fonts")


class Stage(BaseModel):
    description: str

def save_file(destination_dir: str, file_type: str, 
                     file: UploadFile) -> str:
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)
    file_id = len(os.listdir(destination_dir))
    file_extension = Path(file.filename).suffix.lower()
    if not file_extension:
        file_extension = ".bin"
    file_path = f"{destination_dir}/lecture_{file_id}_{file_type}{file_extension}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Function to show main page"""
    return templates.TemplateResponse(request=request, name="start_window.html")


@app.get("/step1")
async def step_one_page(request: Request):
    """Function to show choice of way to upload file page"""
    return templates.TemplateResponse(request=request, name="step_one.html")


@app.get("/step2")
async def step_two_page(request: Request):
    """Function to show uploading audiofile page"""
    return templates.TemplateResponse(request=request, name="step_two.html")


@app.get("/step3")
async def step_three_page(request: Request):
    """Function to show page with comparing lecture and its plan"""
    return templates.TemplateResponse(request=request, name="step_three.html")


@app.get("/upload-plan")
async def upload_plan(request: Request):
    """Function to show page where user can upload lecture plan file"""
    return templates.TemplateResponse(request=request, name="upload_plan.html")


@app.get("/lectures", response_class=HTMLResponse)
async def show_form(request: Request):
    """Function to show form"""
    return templates.TemplateResponse(request=request, name="form.html")

@app.get("/upload-transcript")
async def show_upload_transcript_page(request: Request):
    """Function to show page to upload prepared transcript"""
    return templates.TemplateResponse(request=request, name="upload_audio.html")

@app.post("/save-plan")
async def save_uploaded_plan(file: UploadFile = File(...)):
    """Function to save uploaded plan file"""

    save_file(destination_dir=UPLOADED_PLANS_DIR, file_type='',
                   file=file)

    return RedirectResponse(url="/plan-to-json")


@app.post("/plan-to-json")
async def uploaded_file_to_json(request: Request):
    """Function to convert plans files to JSON"""

    filename = os.listdir(UPLOADED_PLANS_DIR)[0]
    if not os.path.isdir(LECTURES_JSONS_DIR):
        os.mkdir(LECTURES_JSONS_DIR)
    file_id = len(os.listdir(LECTURES_JSONS_DIR))
    json_filename = f"lecture_{file_id}.json"
    plan_to_json(f"{UPLOADED_PLANS_DIR}/{filename}", f"{LECTURES_JSONS_DIR}/{json_filename}")
    file_id += 1
    FILES_TO_PROCESS["lecture_plan"] = f"{LECTURES_JSONS_DIR}/{json_filename}"
    for item in os.listdir(UPLOADED_PLANS_DIR):
        file_path = os.path.join(UPLOADED_PLANS_DIR, item)
        if os.path.isfile(file_path):
            os.remove(file_path) 
    return {
                "status": "success", 
                "redirect_url": "/step2"
            }

@app.post("/lectures/add")
async def lecture_to_json(stages: List[Stage]):
    """Function to save lecture"""
    if not os.path.isdir(LECTURES_JSONS_DIR):
        os.mkdir(LECTURES_JSONS_DIR)
    stages_list = [stage.model_dump() for stage in stages]
    file_name = f"{LECTURES_JSONS_DIR}/lecture_{len(os.listdir(LECTURES_JSONS_DIR))}.json"
    lecture_json = {
        "paragraphs": stages_list
    }
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(lecture_json, file, ensure_ascii=False)
    
    return {"status": "success", "message": "Лекция сохранена", "redirect_url": "/step2"}

@app.post("/save-audiofile")
async def save_uploaded_audiofile(file: UploadFile = File(...)):
    """Function to save uploaded audiofile"""

    file_path = save_file(destination_dir=UPLOADED_AUDIOFILES_DIR, file_type="audiofile",
               file=file)
    FILES_TO_PROCESS["lecture_audiofile"] = file_path
    
    return {"status": "success", "message": "audiofile uploaded"}

@app.post("/speech-transcribe-request")
async def transcribe_api_request(requst: Request):
    if not os.path.isdir(TRANSCRIPTS_DIR):
        os.mkdir(TRANSCRIPTS_DIR)
    file_id = len(os.listdir(TRANSCRIPTS_DIR))
    lecture_transcribe_path = f"{TRANSCRIPTS_DIR}/lecture_{file_id}_transcript.txt"
    is_processed = transcribe_audio_file(input_audio_path=FILES_TO_PROCESS["lecture_audiofile"],
                                         output_text_path=lecture_transcribe_path)
    FILES_TO_PROCESS["lecture_transcript"] = lecture_transcribe_path
    print(is_processed)
    if is_processed:
        return {"message": "success", "redirect_url": "/step3"}
    else:
        return {"message": "fail", "redirect_url": None}

@app.post("/gigachat-api-request")
async def gigachat_api_request():
    response = ask_with_file_content(FILES_TO_PROCESS["lecture_plan"], 
                                     FILES_TO_PROCESS["lecture_transcript"])
    if not os.path.isdir(COMPARISON_JSONS_DIR):
        os.mkdir(COMPARISON_JSONS_DIR)
    base_name = Path(FILES_TO_PROCESS['lecture_plan']).stem
    file_name = f"{COMPARISON_JSONS_DIR}/{base_name}_comparison.json"
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
    FILES_TO_PROCESS['lecture_comparison'] = file_name
    return {"message": "success", "gigachat_response_saved_to": file_name}

@app.post("/save-transcript")
async def upload_transcript(file: UploadFile = File(...)):
    try:
        file_name = save_file(destination_dir=TRANSCRIPTS_DIR, 
                            file_type='transcript',
                            file=file)
        FILES_TO_PROCESS["lecture_transcript"] = file_name
        return {
            "status": "success", 
            "message": "file uploaded", 
            "redirect_url": "/step3",
            "error_msg": None
            }
    except Exception as e:
        return {
            "status": "fail",
            "message": "an error occured while uploading file",
            "redirect_url": None,
            "error_msg": e
        }
    
@app.post("/show-in-browser")
async def show_analysis_in_browser():
    try:
        with open(
            FILES_TO_PROCESS["lecture_comparison"], 
            'r', encoding='utf-8') as comparison_json:
            json_content = json.load(comparison_json)
        choices = json_content['choices']
        message = choices['message']
        return {
            "status": "success", 
            "gigachat-answer": message['content'],
            "error_msg": None
            }
    except Exception as e:
        return {
            "status": "fail",
            "gigachat-answer": None,
            "error_msg": e
        }

@app.get("/download")
def download_analysis_file():
    try:
        if FILES_TO_PROCESS["lecture_comparison"] is not None:
            file_path = FILES_TO_PROCESS["lecture_comparison"]
            return FileResponse(path=file_path, filename="lecture_analysis.md")
    except Exception as e:
        print(f"An error occured: {e}")