import json
import os
import tempfile

from kafka import KafkaConsumer

from .database import SessionLocal
from . import schemas, crud
from .ocr import extract_text
from .document_structure import extract_document_structure
from .llm.llm_client import extract_information
from .minio_client import download_file


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
print("Storage: MinIO")
print("========================================")


# ============================================================
# Consumer Loop
# ============================================================

for message in consumer:

    db = SessionLocal()

    processing_id = None
    temporary_file_path = None

    try:

        # ====================================================
        # Get Kafka Event
        # ====================================================

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


        # ====================================================
        # Check Event Type
        # ====================================================

        if event.get("event") != "invoice.received":

            print("Skipping unknown event.")
            continue


        # ====================================================
        # Get Event Information
        # ====================================================

        processing_id = event.get("processing_id")
        minio_object_name = event.get("file_path")
        filename = event.get("filename")

        if (
            not processing_id
            or not minio_object_name
            or not filename
        ):

            print(
                "Skipping incomplete invoice event."
            )

            continue


        print(
            f"Processing ID: {processing_id}"
        )

        print(
            f"Processing invoice: {filename}"
        )

        print(
            f"MinIO object: {minio_object_name}"
        )


        # ====================================================
        # Verify MinIO Status
        # ====================================================

        processing = crud.get_document_processing(
            db,
            processing_id
        )

        if not processing:

            print(
                f"Processing record {processing_id} "
                "does not exist. Skipping."
            )

            continue


        if processing.minio_status != "completed":

            error_message = (
                "MinIO document is not marked as completed."
            )

            print(error_message)

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue


        # ====================================================
        # Update Overall Processing Status
        # ====================================================

        crud.update_processing_status(
            db,
            processing_id,
            "processing"
        )


        # ====================================================
        # DOWNLOAD DOCUMENT FROM MINIO
        # ====================================================

        print("\n========================================")
        print("MINIO DOCUMENT RETRIEVAL")
        print("========================================")

        try:

            print(
                "Downloading invoice from MinIO..."
            )

            file_data = download_file(
                minio_object_name
            )

            if not file_data:

                raise Exception(
                    "MinIO returned an empty file."
                )


            # ------------------------------------------------
            # Create Temporary Local File
            # ------------------------------------------------

            file_extension = os.path.splitext(
                filename
            )[1].lower()

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension
            ) as temp_file:

                temp_file.write(file_data)

                temporary_file_path = (
                    temp_file.name
                )


            print(
                "Invoice downloaded successfully."
            )

            print(
                f"Temporary file: "
                f"{temporary_file_path}"
            )


        except Exception as minio_error:

            error_message = (
                "Failed to download invoice "
                f"from MinIO: {str(minio_error)}"
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
                temporary_file_path
            )

        except Exception as ocr_error:

            error_message = (
                f"Tesseract OCR failed: "
                f"{str(ocr_error)}"
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
                    temporary_file_path
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
            # Groq/Gemini can still use the
            # Tesseract OCR text.
            # ------------------------------------------------

            document_structure = ""


        # ====================================================
        # LLM PROCESSING
        # ====================================================

        print("\n========================================")
        print("LLM PROCESSING")
        print("========================================")


        # ----------------------------------------------------
        # Mark LLM processing as Processing
        # ----------------------------------------------------

        crud.update_gemini_status(
            db,
            processing_id,
            "processing"
        )


        print(
            "Sending OCR text and Docling "
            "document structure to Groq..."
        )


        # ----------------------------------------------------
        # Groq → Gemini Fallback
        #
        # llm_client.py handles:
        # Groq first
        # Gemini if Groq fails
        # ----------------------------------------------------

        try:

            structured_data = extract_information(
                ocr_text,
                document_structure
            )

        except Exception as llm_error:

            error_message = (
                "LLM processing failed: "
                f"{str(llm_error)}"
            )

            print("\n========================================")
            print("LLM PROCESSING FAILED")
            print("========================================")

            print(error_message)

            print("========================================")


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
        # Check LLM Result
        # ----------------------------------------------------

        if not structured_data:

            error_message = (
                "LLM returned empty structured data."
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
        # Save LLM Result
        # ----------------------------------------------------

        crud.update_gemini_status(
            db,
            processing_id,
            "completed",
            structured_data
        )

        print(
            "LLM extraction completed."
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
        # FINANCIAL INFORMATION
        # ====================================================
        #
        # IMPORTANT:
        # Do NOT calculate total_estimated_cost from item costs.
        #
        # The LLM extracts total_estimated_cost as the FINAL
        # invoice total. It may include GST/taxes, discounts,
        # shipping, rounding, or other invoice-level charges.
        #
        # Example:
        #   Item amounts total      = 15850
        #   Final invoice total     = 18703
        #
        # We store the LLM's final invoice total directly.
        # The item-cost sum is printed only for visibility.
        # It is NOT used to overwrite the extracted total.
        # ====================================================

        print(
            "\nInvoice financial information:"
        )

        try:

            item_total = sum(
                float(item.estimated_cost)
                for item in validated_data.items
            )

            final_invoice_total = float(
                validated_data.total_estimated_cost
            )

            print(
                f"Sum of individual item amounts: "
                f"{item_total:.2f}"
            )

            print(
                f"LLM extracted FINAL invoice total: "
                f"{final_invoice_total:.2f}"
            )

            print(
                "Using LLM final invoice total for "
                "procurement_requests.total_estimated_cost."
            )

        except Exception as financial_info_error:

            error_message = (
                "Financial information processing failed: "
                f"{str(financial_info_error)}"
            )

            print(error_message)

            crud.save_processing_error(
                db,
                processing_id,
                error_message
            )

            continue


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


    finally:

        # ====================================================
        # Remove Temporary File
        # ====================================================

        if temporary_file_path:

            try:

                if os.path.exists(
                    temporary_file_path
                ):

                    os.remove(
                        temporary_file_path
                    )

                    print(
                        "Temporary invoice file "
                        "removed."
                    )

            except Exception as cleanup_error:

                print(
                    "Could not remove temporary file: "
                    f"{cleanup_error}"
                )


        # ====================================================
        # Close Database Session
        # ====================================================

        db.close()