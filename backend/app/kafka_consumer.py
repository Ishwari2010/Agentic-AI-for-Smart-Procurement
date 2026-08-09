import json
import os

from kafka import KafkaConsumer

from .database import SessionLocal
from . import schemas, crud
from .ocr import extract_text
from .document_structure import extract_document_structure
from .llm.gemini_client import extract_information


# ============================================================
# Kafka Configuration
# ============================================================

KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "invoice-topic"


# ============================================================
# Kafka Consumer
# ============================================================

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="document-intelligence-agent",
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    )
)


# ============================================================
# Startup Message
# ============================================================

print("========================================")
print("Document Intelligence Agent started.")
print(f"Listening to Kafka topic: {KAFKA_TOPIC}")
print("========================================")


# ============================================================
# Consumer Loop
# ============================================================

for message in consumer:

    db = SessionLocal()

    processing_id = None

    try:

        # ----------------------------------------------------
        # Get Kafka Event
        # ----------------------------------------------------

        event = message.value

        print("\n========================================")
        print("Kafka message received")
        print("========================================")

        print(
            json.dumps(
                event,
                indent=2
            )
        )

        # ----------------------------------------------------
        # Check Event Type
        # ----------------------------------------------------

        if event.get("event") != "invoice.received":

            print("Skipping unknown event.")

            continue

        # ----------------------------------------------------
        # Get Event Information
        # ----------------------------------------------------

        processing_id = event.get("processing_id")
        file_path = event.get("file_path")
        filename = event.get("filename")

        if not processing_id or not file_path or not filename:

            print("Skipping incomplete invoice event.")

            continue

        print(
            f"Processing ID: {processing_id}"
        )

        print(
            f"Processing invoice: {filename}"
        )

        # ----------------------------------------------------
        # Update Overall Processing Status
        # ----------------------------------------------------

        crud.update_processing_status(
            db,
            processing_id,
            "processing"
        )

        # ----------------------------------------------------
        # Check File Exists
        # ----------------------------------------------------

        if not os.path.exists(file_path):

            error_message = (
                f"File not found: {file_path}"
            )

            print(error_message)

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        # ====================================================
        # OCR PROCESSING
        # ====================================================

        print("\n========================================")
        print("OCR PROCESSING")
        print("========================================")

        # ----------------------------------------------------
        # Mark OCR as Processing
        # ----------------------------------------------------

        crud.update_ocr_status(
            db,
            processing_id,
            "processing"
        )

        # ----------------------------------------------------
        # Tesseract + OpenCV
        # ----------------------------------------------------

        print(
            "Running Tesseract OCR with "
            "OpenCV preprocessing..."
        )

        try:

            ocr_text = extract_text(
                file_path
            )

        except Exception as ocr_error:

            error_message = (
                f"Tesseract OCR failed: {str(ocr_error)}"
            )

            print(error_message)

            crud.update_ocr_status(
                db,
                processing_id,
                "failed"
            )

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        # ----------------------------------------------------
        # Check OCR Result
        # ----------------------------------------------------

        if not ocr_text or not ocr_text.strip():

            error_message = (
                "Tesseract OCR returned no text."
            )

            print(error_message)

            crud.update_ocr_status(
                db,
                processing_id,
                "failed"
            )

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        # ----------------------------------------------------
        # Save OCR Result
        # ----------------------------------------------------

        crud.update_ocr_status(
            db,
            processing_id,
            "completed",
            ocr_text
        )

        print(
            "OCR completed successfully."
        )

        print("\nOCR TEXT:")
        print("----------------------------------------")
        print(ocr_text)
        print("----------------------------------------")

        # ====================================================
        # DOCLING PROCESSING
        # ====================================================

        print("\n========================================")
        print(
            "DOCLING DOCUMENT STRUCTURE PROCESSING"
        )
        print("========================================")

        document_structure = ""

        try:

            print(
                "Extracting document structure "
                "using Docling..."
            )

            # ------------------------------------------------
            # Mark Docling as Processing
            # ------------------------------------------------

            crud.update_docling_status(
                db,
                processing_id,
                "processing"
            )

            # ------------------------------------------------
            # Run Docling
            # ------------------------------------------------

            document_structure = (
                extract_document_structure(
                    file_path
                )
            )

            # ------------------------------------------------
            # Mark Docling as Completed
            # ------------------------------------------------

            crud.update_docling_status(
                db,
                processing_id,
                "completed"
            )

            print(
                "Docling processing completed."
            )

            print(
                "\nDOCLING DOCUMENT STRUCTURE:"
            )

            print(
                "----------------------------------------"
            )

            print(
                document_structure
            )

            print(
                "----------------------------------------"
            )

        except Exception as docling_error:

            print(
                f"Docling processing failed: "
                f"{docling_error}"
            )

            # ------------------------------------------------
            # Mark Docling as Failed
            # ------------------------------------------------

            crud.update_docling_status(
                db,
                processing_id,
                "failed"
            )

            print(
                "Continuing with OCR text only."
            )

            # ------------------------------------------------
            # Docling is a supporting stage.
            #
            # If it fails, Gemini can still use the
            # Tesseract OCR text.
            # ------------------------------------------------

            document_structure = ""

        # ====================================================
        # GEMINI PROCESSING
        # ====================================================

        print("\n========================================")
        print("GEMINI PROCESSING")
        print("========================================")

        # ----------------------------------------------------
        # Mark Gemini as Processing
        # ----------------------------------------------------

        crud.update_gemini_status(
            db,
            processing_id,
            "processing"
        )

        print(
            "Sending OCR text and Docling "
            "document structure to Gemini..."
        )

        # ----------------------------------------------------
        # Gemini Extraction
        # ----------------------------------------------------

        try:

            structured_data = extract_information(
                ocr_text,
                document_structure
            )

        except Exception as gemini_error:

            error_message = (
                f"Gemini processing failed: "
                f"{str(gemini_error)}"
            )

            print("\n========================================")
            print("GEMINI PROCESSING FAILED")
            print("========================================")
            print(error_message)
            print("========================================")

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT create a procurement request when
            # Gemini fails.
            #
            # This handles:
            # - 429 quota errors
            # - API errors
            # - invalid responses
            # - network errors
            # - authentication errors
            # ------------------------------------------------

            crud.update_gemini_status(
                db,
                processing_id,
                "failed"
            )

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        # ----------------------------------------------------
        # Check Gemini Result
        # ----------------------------------------------------

        if not structured_data:

            error_message = (
                "Gemini returned empty structured data."
            )

            print(error_message)

            crud.update_gemini_status(
                db,
                processing_id,
                "failed"
            )

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        # ----------------------------------------------------
        # Save Gemini Result
        # ----------------------------------------------------

        crud.update_gemini_status(
            db,
            processing_id,
            "completed",
            structured_data
        )

        print(
            "Gemini extraction completed."
        )

        print("\nSTRUCTURED DATA:")
        print("----------------------------------------")

        print(
            json.dumps(
                structured_data,
                indent=2,
                default=str
            )
        )

        print(
            "----------------------------------------"
        )

        # ====================================================
        # PYDANTIC VALIDATION
        # ====================================================

        print(
            "\nValidating extracted data..."
        )

        try:

            validated_data = (
                schemas.ProcurementExtraction(
                    **structured_data
                )
            )

        except Exception as validation_error:

            error_message = (
                "Structured data validation failed: "
                f"{str(validation_error)}"
            )

            print(error_message)

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        print(
            "Data validation completed."
        )

        # ====================================================
        # SAVE PROCUREMENT REQUEST
        # ====================================================

        print(
            "\nSaving procurement request..."
        )

        try:

            db_request = (
                crud.create_procurement_request(
                    db,
                    validated_data
                )
            )

        except Exception as db_error:

            error_message = (
                "Failed to save procurement request: "
                f"{str(db_error)}"
            )

            print(error_message)

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue

        print(
            "Invoice saved to PostgreSQL."
        )

        print(
            f"Request ID: {db_request.id}"
        )

        # ====================================================
        # SAVE FINAL PROCESSING RESULT
        # ====================================================

        crud.save_processing_result(
            db=db,
            processing_id=processing_id,
            ocr_text=ocr_text,
            structured_data=structured_data,
            request_id=db_request.id
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        print(
            "\n========================================"
        )

        print(
            "INVOICE PROCESSING COMPLETED "
            "SUCCESSFULLY"
        )

        print(
            "========================================"
        )

    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as e:

        print(
            "\n========================================"
        )

        print(
            "ERROR PROCESSING INVOICE"
        )

        print(
            "========================================"
        )

        print(
            str(e)
        )

        print(
            "========================================"
        )

        # ----------------------------------------------------
        # Save Failure Information
        # ----------------------------------------------------

        try:

            if processing_id:

                crud.save_processing_error(
                    db,
                    processing_id,
                    str(e)
                )

        except Exception as db_error:

            print(
                f"Could not update failure status: "
                f"{db_error}"
            )

    # ========================================================
    # CLOSE DATABASE SESSION
    # ========================================================

    finally:

        db.close()