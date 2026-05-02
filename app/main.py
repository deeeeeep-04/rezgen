from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from .generator import generate_resume
import traceback

app = FastAPI(title="Rezgen API")


class ResumeRequest(BaseModel):
    raw_data: str  # freeform text describing the user's background


@app.get("/")
def root():
    return {"status": "Rezgen is running!"}


@app.post("/generate")
def generate(request: ResumeRequest):
    """
    Accepts raw resume information as text, returns a PDF.
    The response is a direct PDF download.
    """
    if not request.raw_data.strip():
        raise HTTPException(status_code=400, detail="raw_data cannot be empty")
    
    try:
        pdf_bytes = generate_resume(request.raw_data)
    except RuntimeError as e:
        # LaTeX compilation error — surface it clearly during development
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"}
    )