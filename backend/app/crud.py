from sqlalchemy.orm import Session

from . import models, schemas


# ============================================================
# Create Procurement Request
# ============================================================

def create_procurement_request(
    db: Session,
    data: schemas.ProcurementExtraction
):
    """
    Saves one procurement request and all extracted items.
    """

    # Create main procurement request
    db_request = models.ProcurementRequest(
        requester_name=data.requester_name,
        total_estimated_cost=data.total_estimated_cost
    )

    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    # Save extracted items
    for item in data.items:

        db_item = models.ProcurementItem(
            request_id=db_request.id,
            description=item.description,
            quantity=item.quantity,
            estimated_cost=item.estimated_cost
        )

        db.add(db_item)

    db.commit()
    db.refresh(db_request)

    return db_request


# ============================================================
# Create Document Processing Record
# ============================================================

def create_document_processing(
    db: Session,
    filename: str,
    file_path: str
):
    """
    Creates a tracking record when an invoice is uploaded.
    """

    processing = models.DocumentProcessing(
        filename=filename,
        file_path=file_path,
        status="queued",
        ocr_status="pending",
        gemini_status="pending"
    )

    db.add(processing)
    db.commit()
    db.refresh(processing)

    return processing


# ============================================================
# Get Document Processing
# ============================================================

def get_document_processing(
    db: Session,
    processing_id: int
):
    """
    Retrieves a document processing record by ID.
    """

    return (
        db.query(models.DocumentProcessing)
        .filter(
            models.DocumentProcessing.id == processing_id
        )
        .first()
    )


# ============================================================
# Update Overall Processing Status
# ============================================================

def update_processing_status(
    db: Session,
    processing_id: int,
    status: str
):
    """
    Updates the overall document processing status.
    """

    processing = get_document_processing(
        db,
        processing_id
    )

    if processing:

        processing.status = status

        db.commit()
        db.refresh(processing)

    return processing


# ============================================================
# Update OCR Status
# ============================================================

def update_ocr_status(
    db: Session,
    processing_id: int,
    status: str,
    ocr_text: str = None
):
    """
    Updates OCR processing status and optionally
    stores the extracted OCR text.
    """

    processing = get_document_processing(
        db,
        processing_id
    )

    if processing:

        processing.ocr_status = status

        if ocr_text is not None:
            processing.ocr_text = ocr_text

        db.commit()
        db.refresh(processing)

    return processing


# ============================================================
# Update Gemini Status
# ============================================================

def update_gemini_status(
    db: Session,
    processing_id: int,
    status: str,
    structured_data: dict = None
):
    """
    Updates Gemini processing status and optionally
    stores the structured extraction result.
    """

    processing = get_document_processing(
        db,
        processing_id
    )

    if processing:

        processing.gemini_status = status

        if structured_data is not None:
            processing.structured_data = structured_data

        db.commit()
        db.refresh(processing)

    return processing


# ============================================================
# Save Processing Result
# ============================================================

def save_processing_result(
    db: Session,
    processing_id: int,
    ocr_text: str,
    structured_data: dict,
    request_id: int
):
    """
    Saves the final successful processing result.
    """

    processing = get_document_processing(
        db,
        processing_id
    )

    if processing:

        processing.status = "completed"

        processing.ocr_status = "completed"

        processing.gemini_status = "completed"

        processing.ocr_text = ocr_text

        processing.structured_data = structured_data

        processing.request_id = request_id

        processing.error_message = None

        db.commit()
        db.refresh(processing)

    return processing


# ============================================================
# Save Processing Error
# ============================================================

def save_processing_error(
    db: Session,
    processing_id: int,
    error_message: str
):
    """
    Marks document processing as failed and stores
    the error message.
    """

    processing = get_document_processing(
        db,
        processing_id
    )

    if processing:

        processing.status = "failed"

        processing.error_message = error_message

        db.commit()
        db.refresh(processing)

    return processing

# ============================================================
# Get All Document Processing Records
# ============================================================

def get_all_document_processing(
    db: Session
):
    return (
        db.query(models.DocumentProcessing)
        .order_by(
            models.DocumentProcessing.created_at.desc()
        )
        .all()
    )


# ============================================================
# Delete Document Processing Record
# ============================================================

def delete_document_processing(
    db: Session,
    processing_id: int
):
    processing = get_document_processing(
        db,
        processing_id
    )

    if not processing:
        return None

    db.delete(processing)
    db.commit()

    return processing


# ============================================================
# Reset Document For Reprocessing
# ============================================================

def reset_document_processing(
    db: Session,
    processing_id: int
):
    processing = get_document_processing(
        db,
        processing_id
    )

    if not processing:
        return None

    processing.status = "queued"
    processing.ocr_status = "pending"
    processing.gemini_status = "pending"

    processing.ocr_text = None
    processing.structured_data = None
    processing.request_id = None
    processing.error_message = None

    db.commit()
    db.refresh(processing)

    return processing