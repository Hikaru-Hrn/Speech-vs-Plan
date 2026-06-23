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