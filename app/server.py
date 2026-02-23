from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import datetime
import logging
import os
from . import engine, integrations, pdf_generator

app = FastAPI(title="Analog Algorithm Engine", version="1.1.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LetterRequest(BaseModel):
    first_name: str
    birth_date: str
    target_month: str

# THE DASHBOARD HTML (Inlined to ensure it loads)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Analog Algorithm | Writer's Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --paper: #f9f7f2; --ink: #2c2c2c; --accent: #8b7d6b; }
        body { font-family: 'Inter', sans-serif; background-color: #f0f0f0; color: var(--ink); margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background-color: var(--paper); padding: 3rem; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 100%; max-width: 500px; border: 1px solid #e0e0e0; }
        h1 { font-family: 'Crimson Pro', serif; font-weight: 600; font-size: 2rem; margin-bottom: 1.5rem; text-align: center; }
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem; color: var(--accent); }
        input { width: 100%; padding: 0.8rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
        button { width: 100%; padding: 1rem; background-color: var(--ink); color: white; border: none; border-radius: 4px; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 1rem; }
        #result { margin-top: 2rem; padding: 1rem; border-radius: 4px; display: none; font-size: 0.9rem; line-height: 1.5; }
        .success { background: #e8f5e9; border: 1px solid #c8e6c9; }
        .error { background: #ffebee; border: 1px solid #ffcdd2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Writer's Dashboard</h1>
        <div class="form-group">
            <label>Customer Name</label>
            <input type="text" id="firstName" placeholder="e.g. Cassidy">
        </div>
        <div class="form-group">
            <label>Birth Date</label>
            <input type="date" id="birthDate">
        </div>
        <div class="form-group">
            <label>Letter Month</label>
            <input type="month" id="targetMonth" value="2026-03">
        </div>
        <button onclick="generateLetter()">Generate & Mail Letter</button>
        <div id="result"></div>
    </div>
    <script>
        async function generateLetter() {
            const resDiv = document.getElementById('result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = 'Consulting the cards...';
            try {
                const response = await fetch('/admin/generate-test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        first_name: document.getElementById('firstName').value,
                        birth_date: document.getElementById('birthDate').value,
                        target_month: document.getElementById('targetMonth').value
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    resDiv.className = 'success';
                    resDiv.innerHTML = `Success! Card: ${data.engine_data.birth_card}. Mailed via Lob.`;
                } else {
                    resDiv.className = 'error';
                    resDiv.innerText = "Error: " + data.detail;
                }
            } catch (err) { resDiv.innerText = "Error: " + err.message; }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/health")
async def health():
    return {"status": "alive"}

@app.post("/admin/generate-test")
async def generate_test_letter(req: LetterRequest):
    try:
        b_year, b_month, b_day = map(int, req.birth_date.split("-"))
        target_date = f"{req.target_month}-15"
        data = engine.calculate_letter_data(req.first_name, b_year, b_month, b_day, target_date)
        
        # Generate Professional Prose
        period_card = data['period']['card']
        planet = data['period']['planet']
        archetype = engine.get_rank_archetype(period_card)
        realm = engine.get_suit_realm(period_card)
        
        prose = f"""You're already doing that thing again.

The pattern running right now is the {archetype} in the {realm.lower()} domain, activated through {planet.lower()} perception.

The uncomfortable line: this is costing you more than you're admitting.

The question that lingers: what would a single day look like if you measured it by what you kept instead of what you shipped?

This cycle isn't about productivity; it's about structural integrity. The friction you feel is the algorithm attempting to correct for a variable you've been trying to ignore. Pay attention to what breaks when you stop pushing."""
        
        filename = f"manual_{req.first_name}.pdf"
        pdf_path = os.path.join(os.getcwd(), filename)
        pdf_generator.build_pdf(pdf_path, req.target_month, req.first_name, prose, additional_data=data)
        
        addr = {"name": req.first_name, "address_line1": "123 Test St", "city": "Portland", "state": "OR", "zip_code": "97204"}
        integrations.send_letter_via_lob(pdf_path, addr)
        
        return {"message": "Success", "engine_data": data}
    except Exception as e:
        logger.error(f"Error generating test letter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
