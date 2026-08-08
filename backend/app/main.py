from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

import os
import shutil

from .database import SessionLocal
from . import crud, schemas
from .kafka_producer import publish_invoice_event


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="Agentic AI Smart Procurement API",
    description="Backend API for Smart Procurement",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# Upload Folder
# ============================================================

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# Database Dependency
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return {
        "message":
            "Agentic AI Smart Procurement Backend Running Successfully!",

        "status":
            "online"
    }


# ============================================================
# Upload Invoice
# ============================================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:

        # ----------------------------------------------------
        # Validate filename
        # ----------------------------------------------------

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )


        # ----------------------------------------------------
        # Validate file type
        # ----------------------------------------------------

        ALLOWED_EXTENSIONS = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg"
        }

        file_extension = os.path.splitext(
            file.filename
        )[1].lower()


        if file_extension not in ALLOWED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only PDF, PNG, JPG, and JPEG "
                    "files are allowed"
                )
            )


        # ----------------------------------------------------
        # Save file
        # ----------------------------------------------------

        file_path = os.path.join(
            UPLOAD_FOLDER,
            file.filename
        )


        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        # ----------------------------------------------------
        # Create document processing record
        # ----------------------------------------------------

        processing = (
            crud.create_document_processing(
                db=db,
                filename=file.filename,
                file_path=file_path
            )
        )


        # ----------------------------------------------------
        # Publish Kafka event
        # ----------------------------------------------------

        kafka_event = (
            publish_invoice_event(

                processing_id=processing.id,

                filename=file.filename,

                file_path=file_path
            )
        )


        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {

            "message":
                "Invoice uploaded and queued for processing",

            "processing_id":
                processing.id,

            "filename":
                file.filename,

            "status":
                "queued",

            "kafka_topic":
                "invoice-topic",

            "event":
                kafka_event
        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=(
                f"Invoice upload failed: {str(e)}"
            )
        )


# ============================================================
# Get Processing Status / Result
# ============================================================

@app.get(
    "/processing/{processing_id}",
    response_model=schemas.DocumentProcessingResponse
)
def get_processing_result(

    processing_id: int,

    db: Session = Depends(get_db)
):

    processing = (
        crud.get_document_processing(
            db,
            processing_id
        )
    )


    if not processing:

        raise HTTPException(

            status_code=404,

            detail="Processing record not found"
        )


    return processing

# ============================================================
# Document History
# ============================================================

@app.get("/documents")
def get_documents(
    db: Session = Depends(get_db)
):
    documents = crud.get_all_document_processing(db)

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "file_path": document.file_path,
            "status": document.status,
            "ocr_status": document.ocr_status,
            "gemini_status": document.gemini_status,
            "request_id": document.request_id,
            "created_at": document.created_at,
            "error_message": document.error_message
        }
        for document in documents
    ]


# ============================================================
# View Document Details
# ============================================================

@app.get("/documents/{processing_id}")
def get_document_details(
    processing_id: int,
    db: Session = Depends(get_db)
):
    document = crud.get_document_processing(
        db,
        processing_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "file_path": document.file_path,
        "status": document.status,
        "ocr_status": document.ocr_status,
        "gemini_status": document.gemini_status,
        "ocr_text": document.ocr_text,
        "structured_data": document.structured_data,
        "request_id": document.request_id,
        "error_message": document.error_message,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }


# ============================================================
# Delete Document
# ============================================================

@app.delete("/documents/{processing_id}")
def delete_document(
    processing_id: int,
    db: Session = Depends(get_db)
):
    document = crud.get_document_processing(
        db,
        processing_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    deleted = crud.delete_document_processing(
        db,
        processing_id
    )

    return {
        "message": "Document deleted successfully",
        "processing_id": deleted.id,
        "filename": deleted.filename
    }


# ============================================================
# Reprocess Document
# ============================================================

@app.post("/documents/{processing_id}/reprocess")
def reprocess_document(
    processing_id: int,
    db: Session = Depends(get_db)
):
    document = crud.get_document_processing(
        db,
        processing_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=404,
            detail="Original document file not found"
        )

    # Reset processing information
    processing = crud.reset_document_processing(
        db,
        processing_id
    )

    # Publish the document to Kafka again
    kafka_event = publish_invoice_event(
        processing_id=processing.id,
        filename=processing.filename,
        file_path=processing.file_path
    )

    return {
        "message": "Document queued for reprocessing",
        "processing_id": processing.id,
        "filename": processing.filename,
        "status": "queued",
        "kafka_topic": "invoice-topic",
        "event": kafka_event
    }