from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import datetime
import logging
import os
from . import engine, integrations, pdf_generator

app = FastAPI(title="Analog Algorithm Engine", version="1.0.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Absolute paths for reliability
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
TEMPLATE_PATH = os.path.join(ROOT_DIR, "templates", "dashboard.html")

# ====================== DATA MODELS ======================

class LetterRequest(BaseModel):
    first_name: str
    birth_date: str # YYYY-MM-DD
    target_month: str # YYYY-MM

# ====================== ENDPOINTS ======================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serves the Writer's Dashboard."""
    logger.info(f"Checking for template at: {TEMPLATE_PATH}")
    
    if not os.path.exists(TEMPLATE_PATH):
        # Fallback to local 'templates' if ROOT_DIR logic fails on certain OS
        alt_path = os.path.join(os.getcwd(), "templates", "dashboard.html")
        if os.path.exists(alt_path):
            with open(alt_path, "r") as f:
                return HTMLResponse(content=f.read())
        
        logger.error(f"Template NOT FOUND at {TEMPLATE_PATH}")
        return HTMLResponse(content=f"<h1>Dashboard Template Not Found</h1><p>Tried: {TEMPLATE_PATH}</p>", status_code=404)
        
    with open(TEMPLATE_PATH, "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/admin/generate-test")
async def generate_test_letter(req: LetterRequest):
    """
    Manually triggers a letter generation and mails it via Lob.
    """
    try:
        b_year, b_month, b_day = map(int, req.birth_date.split("-"))
        target_date = f"{req.target_month}-15"
        
        data = engine.calculate_letter_data(
            req.first_name, b_year, b_month, b_day, target_date
        )
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        content = f"""
Personalized Analysis for {req.first_name}
Target: {req.target_month}

Birth Card: {data['birth_card']}
Period Card: {data['period']['card']} ({data['period']['planet']})

This cycle emphasizes material stability and the pursuit of your higher purpose.
        """
        
        filename = f"manual_{req.first_name}_{req.target_month}.pdf"
        pdf_path = os.path.join(os.getcwd(), filename)
        pdf_generator.build_pdf(pdf_path, req.target_month, req.first_name, content)
        
        shipping_address = {
            "name": req.first_name,
            "address_line1": "123 Mystic Lane",
            "city": "Portland",
            "state": "OR",
            "zip_code": "97204"
        }
        
        lob_response = integrations.send_letter_via_lob(pdf_path, shipping_address)
        
        return {
            "message": "Letter Generated and Mailed",
            "lob_id": lob_response.get("id"),
            "engine_data": data
        }
        
    except Exception as e:
        logger.error(f"Manual Gen Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/tiktok")
async def tiktok_webhook(request: Request):
    return {"status": "success", "mode": "manual"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
