from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List
from pydantic import BaseModel
import json
import os
import shutil
from pathlib import Path

LECTURES_JSONS_DIR = "lectures"
TRANSCRIPTS_DIR = "lectures_transcripts"
AUDIOFILES_DIR = "lectures_audiofiles"
UPLOADED_PLANS_DIR = "uploaded_plans"

templates = Jinja2Templates(directory="templates/html")
app = FastAPI()

app.mount("/css", StaticFiles(directory="templates/css"), name="css")
app.mount("/js", StaticFiles(directory="templates/js"), name="js")


class Stage(BaseModel):
    stage_number: int
    name: str
    time: str
    description: str


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


@app.post("/upload-plan/save")
async def save_uploaded_plans(files: List[UploadFile] = File(...)):
    """Function to save uploaded lecture plans files"""

    if not os.path.isdir(UPLOADED_PLANS_DIR):
        os.mkdir(UPLOADED_PLANS_DIR)
    for file in files:
        file_id = len(os.listdir(UPLOADED_PLANS_DIR))
        file_extension = Path(file.filename).suffix.lower()
        if not file_extension:
            file_extension = ".bin"
        file_path = f"{UPLOADED_PLANS_DIR}/lecture_{file_id}_plan{file_extension}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return {"message": "Файлы успешно загружены!"}


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