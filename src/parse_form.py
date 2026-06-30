from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
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

FILES_TO_PROCESS = {
    "lecture_plan": None,
    "lecture_audiofile": None,
    "lecture_transcript": None
}

load_dotenv()
templates = Jinja2Templates(directory="templates/html")
app = FastAPI()

app.mount("/css", StaticFiles(directory="templates/css"), name="css")
app.mount("/js", StaticFiles(directory="templates/js"), name="js")
app.mount("/fonts", StaticFiles(directory="templates/fonts"), name="fonts")


class Stage(BaseModel):
    stage_number: int
    name: str
    time: str
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
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_stages": len(stages_list),
        "stages": stages_list
    }
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(lecture_json, file, ensure_ascii=False)
    
    return {"status": "success", "message": "Lecture saved"}

@app.post("/save-audiofile")
async def save_uploaded_audiofile(file: UploadFile = File(...)):
    """Function to save uploaded audiofile"""

    file_path = save_file(destination_dir=UPLOADED_AUDIOFILES_DIR, file_type="audiofile",
               file=file)
    FILES_TO_PROCESS["lecture_audiofile"] = file_path
    
    return {"status": "success", "message": "audiofile uploaded"}

@app.post("/gigachat-api-request")
async def gigachat_api_request():
    response = ask_with_file_content(FILES_TO_PROCESS["lecture_plan"], 
                                     FILES_TO_PROCESS["lecture_transcript"])
    return {"message": "success", "gigachat_response": response.json()}