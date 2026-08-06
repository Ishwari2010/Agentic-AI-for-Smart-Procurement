from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import shutil

from .database import engine, Base, get_db
from . import schemas, crud

from .ocr import extract_text
from .llm.gemini_client import extract_information

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic AI Smart Procurement API")

# Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "Agentic AI Smart Procurement Backend Running Successfully!"
    }


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:
        # -----------------------------
        # Save uploaded file
        # -----------------------------
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # -----------------------------
        # OCR
        # -----------------------------
        ocr_text = extract_text(file_path)

        # -----------------------------
        # Gemini Information Extraction
        # -----------------------------
        structured_data = extract_information(ocr_text)

        # -----------------------------
        # Validate using Pydantic
        # -----------------------------
        validated_data = schemas.ProcurementExtraction(
            **structured_data
        )

        # -----------------------------
        # Save to PostgreSQL
        # -----------------------------
        db_request = crud.create_procurement_request(
            db,
            validated_data
        )

        # -----------------------------
        # Response
        # -----------------------------
        return {
            "message": "Invoice processed successfully",

            "filename": file.filename,

            "ocr_text": ocr_text,

            "structured_data": structured_data,

            "request_id": db_request.id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )