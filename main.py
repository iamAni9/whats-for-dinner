import os
import httpx
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import tinker
from tinker_cookbook.renderers import get_renderer
from starlette.exceptions import HTTPException as StarletteHTTPException
import asyncio

app = FastAPI(title="What's for Dinner API")

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")
BACKBOARD_URL = os.getenv("BACKBOARD_URL", "https://api.backboard.io/v1")
TINKER_SAMPLER_PATH = os.getenv("TINKER_SAMPLER_PATH", "default/sampler")

class SuggestionRequest(BaseModel):
    pantry_items: str

class SuggestionResponse(BaseModel):
    dishes: List[str]

class SelectionRequest(BaseModel):
    dish: str

@app.post("/api/select")
async def save_selection(req: SelectionRequest):
    if BACKBOARD_API_KEY:
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{BACKBOARD_URL}/memory/meals/history",
                    headers={"Authorization": f"Bearer {BACKBOARD_API_KEY}"},
                    json={"dish": req.dish}
                )
            except Exception as e:
                print(f"Backboard API warning: {e}")
    return {"status": "success"}

@app.post("/api/suggest", response_model=SuggestionResponse)
async def suggest_meals(req: SuggestionRequest):
    history = ""
    if BACKBOARD_API_KEY:
        async with httpx.AsyncClient() as client:
            try:
                resp_history = await client.get(
                    f"{BACKBOARD_URL}/memory/meals/history",
                    headers={"Authorization": f"Bearer {BACKBOARD_API_KEY}"},
                    params={"days": 2}
                )
                if resp_history.status_code == 200:
                    history = resp_history.json().get("data", "")
            except Exception as e:
                print(f"Backboard API warning: {e}")

    prompt = (
        f"Available pantry items: {req.pantry_items}\n"
        f"Recent meal history (do not repeat): {history}\n"
    )

    try:
        def get_suggestions():
            sampler = tinker.ServiceClient().create_sampling_client(model_path=TINKER_SAMPLER_PATH)
            tokenizer = sampler.get_tokenizer()
            renderer = get_renderer("role_colon", tokenizer)
            
            messages = [{"role": "user", "content": prompt}]
            prompt_input, _ = renderer.build_supervised_example(messages)
            
            params = tinker.types.SamplingParams(max_tokens=150)
            
            future = sampler.sample(
                prompt=prompt_input,
                num_samples=1,
                sampling_params=params
            )
            return future.result(), tokenizer

        result, tokenizer = await asyncio.to_thread(get_suggestions)

        
        text_output = tokenizer.decode(result.sequences[0].tokens, skip_special_tokens=True)
        dishes = [dish.strip("- \t\r\n") for dish in text_output.strip().split("\n") if dish.strip()]
        
        # Keep 3-4 max as requested
        dishes = [d for d in dishes if d][:4]

        return SuggestionResponse(dishes=dishes)
    except Exception as e:
        print(f"Tinker API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions via Tinker")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    
    frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Frontend not built yet."}, status_code=404)

frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
os.makedirs(frontend_dist, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
