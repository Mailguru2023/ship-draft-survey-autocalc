from fastapi import FastAPI, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import csv
import os

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '../data')
PROFILE_DIR = os.path.join(DATA_DIR, 'demo')

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    ship_profiles = [f[:-5] for f in os.listdir(PROFILE_DIR) if f.endswith('.json')]
    return templates.TemplateResponse("index.html", {"request": request, "profiles": ship_profiles})

@app.get("/survey/{ship_name}", response_class=HTMLResponse)
async def survey_main(request: Request, ship_name: str):
    with open(os.path.join(PROFILE_DIR, f"{ship_name}.json")) as f:
        ship_info = f.read()  # Парсинг json можно добавить позже
    return templates.TemplateResponse("survey.html", {"request": request, "ship": ship_name, "info": ship_info})

# Для тестовых гидростатических таблиц и балластных танков (демонстрация):
@app.post("/upload_table/{ship_name}")
async def upload_table(ship_name: str, table_file: UploadFile = File(...)):
    # todo: сохранить файл, распарсить, привязать к профилю
    return RedirectResponse(url="/", status_code=303)
