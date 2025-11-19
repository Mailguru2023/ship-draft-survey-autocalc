import os
import json
import csv
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
DEMO_DIR = os.path.join(DATA_DIR, "demo")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_profiles():
    profiles = []
    for fname in os.listdir(DEMO_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(DEMO_DIR, fname), encoding="utf-8") as f:
                profile = json.load(f)
                profiles.append(profile)
    return profiles

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    profiles = get_profiles()
    return templates.TemplateResponse("index.html", {"request": request, "profiles": profiles})

@app.get("/survey/{profile_id}", response_class=HTMLResponse)
async def survey_step1(request: Request, profile_id: str):
    # Step 1: Input drafts
    with open(os.path.join(DEMO_DIR, profile_id + ".json"), encoding="utf-8") as f:
        profile = json.load(f)
    return templates.TemplateResponse("survey_step1.html", {"request": request, "profile": profile})

@app.post("/survey/{profile_id}/step2", response_class=HTMLResponse)
async def survey_step2(
    request: Request,
    profile_id: str,
    draft_fp_l: float = Form(...), draft_fp_r: float = Form(...), 
    draft_mid_l: float = Form(...), draft_mid_r: float = Form(...),
    draft_ap_l: float = Form(...), draft_ap_r: float = Form(...),
    water_density: float = Form(1.025)
):
    # Step 2: Input tanks
    with open(os.path.join(DEMO_DIR, profile_id + ".json"), encoding="utf-8") as f:
        profile = json.load(f)
    # Save user drafts for the session (in prod use, add session token/project context)
    user_input = {
        "draft_fp_l": draft_fp_l, "draft_fp_r": draft_fp_r,
        "draft_mid_l": draft_mid_l, "draft_mid_r": draft_mid_r,
        "draft_ap_l": draft_ap_l, "draft_ap_r": draft_ap_r,
        "water_density": water_density
    }
    # read tanks: open tank_tables[0] (demo — только ballast)
    tank_table = []
    with open(os.path.join(DEMO_DIR, profile["tank_tables"][0]), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tank_table.append(row)
    return templates.TemplateResponse("survey_step2.html", {
        "request": request,
        "profile": profile,
        "user_input": user_input,
        "tanks": tank_table
    })

@app.post("/survey/{profile_id}/results", response_class=HTMLResponse)
async def survey_results(
    request: Request,
    profile_id: str,
    draft_fp_l: float = Form(...), draft_fp_r: float = Form(...),
    draft_mid_l: float = Form(...), draft_mid_r: float = Form(...),
    draft_ap_l: float = Form(...), draft_ap_r: float = Form(...),
    water_density: float = Form(...),
    **kwargs # tank soundings as: sound_{tank_name}
):
    with open(os.path.join(DEMO_DIR, profile_id + ".json"), encoding="utf-8") as f:
        profile = json.load(f)
    # Parse tank soundings
    tank_table = []
    with open(os.path.join(DEMO_DIR, profile["tank_tables"][0]), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = dict(row)
            volume = 0
            sound_val = kwargs.get(f"sound_{row['Tank']}", "")
            try: volume = float(row['Volume']) if not sound_val else float(sound_val)
            except: volume = 0
            row["Sounding"] = sound_val
            row["ActualVolume"] = volume
            tank_table.append(row)
    # Calculate draft survey automatically! (demo-formula; in work use hydrostatics interpolation)
    mean_fp = (float(draft_fp_l) + float(draft_fp_r)) / 2
    mean_mid = (float(draft_mid_l) + float(draft_mid_r)) / 2
    mean_ap = (float(draft_ap_l) + float(draft_ap_r)) / 2
    mean_draft = (mean_fp + mean_mid + mean_ap) / 3
    displacement = 4000 + (mean_draft - 2.0) * 600   # demo: linear from fake CSV
    survey_result = {
        "mean_fp": mean_fp, "mean_mid": mean_mid, "mean_ap": mean_ap,
        "mean_draft": mean_draft,
        "displacement": displacement,
        "density": water_density,
        "tanks": tank_table,
        "profile": profile
    }
    return templates.TemplateResponse("survey_result.html", {
        "request": request, "result": survey_result
    })


@app.post("/upload_profile", response_class=HTMLResponse)
async def upload_profile(request: Request, file: UploadFile = File(...)):
    # Demo: accept .json profile only
    if file.filename.endswith('.json'):
        with open(os.path.join(DEMO_DIR, file.filename), "wb") as out:
            out.write(await file.read())
    return RedirectResponse("/", status_code=303)

@app.post("/upload_table/{profile_id}", response_class=HTMLResponse)
async def upload_table(profile_id: str, table_file: UploadFile = File(...)):
    # Accepts .csv for hydrostatics or tanks, saves as is
    if table_file.filename.endswith('.csv'):
        with open(os.path.join(DEMO_DIR, table_file.filename), "wb") as out:
            out.write(await table_file.read())
    return RedirectResponse("/", status_code=303)