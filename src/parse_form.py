from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import List
from pydantic import BaseModel
import json
import os

templates = Jinja2Templates(directory="templates")
app = FastAPI()

class Stage(BaseModel):
    stage_number: int
    name: str
    time: str
    description: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Function to show main page"""
    return templates.TemplateResponse(request=request, name="start_window.html")

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