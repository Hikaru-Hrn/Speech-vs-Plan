from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List
from pydantic import BaseModel
import json
import os

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

@app.post("/lectures/add")
async def lecture_to_json(stages: List[Stage]):
    """Function to save lecture"""
    if not os.path.isdir("lectures"):
        os.mkdir("lectures")
    stages_list = [stage.model_dump() for stage in stages]
    file_name = f"lectures/lecture_{len(os.listdir("lectures"))}.json"
    lecture_json = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_stages": len(stages_list),
        "stages": stages_list
    }   
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(lecture_json, file, ensure_ascii=False)
    
    return {"status": "success", "message": "Lecture saved"}