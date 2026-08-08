import json
import os

from kafka import KafkaConsumer

from .database import SessionLocal
from . import schemas, crud
from .ocr import extract_text
from .llm.gemini_client import extract_information


# ============================================================
# Kafka Configuration
# ============================================================

KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "invoice-topic"


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
        # Get Kafka event
        # ----------------------------------------------------

        event = message.value

        print("\n========================================")
        print("Kafka message received")
        print("========================================")

        print(json.dumps(event, indent=2))


        # ----------------------------------------------------
        # Check event type
        # ----------------------------------------------------

        if event.get("event") != "invoice.received":

            print("Skipping unknown event.")

            continue


        # ----------------------------------------------------
        # Get event information
        # ----------------------------------------------------

        processing_id = event.get("processing_id")
        file_path = event.get("file_path")
        filename = event.get("filename")


        if not processing_id or not file_path or not filename:

            print("Skipping incomplete invoice event.")

            continue


        print(f"Processing ID: {processing_id}")
        print(f"Processing invoice: {filename}")


        # ----------------------------------------------------
        # Update overall status
        # ----------------------------------------------------

        crud.update_processing_status(
            db,
            processing_id,
            "processing"
        )


        # ----------------------------------------------------
        # Check file exists
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

        # Mark OCR as processing

        crud.update_ocr_status(
            db,
            processing_id,
            "processing"
        )


        print("Running Tesseract OCR...")

        ocr_text = extract_text(file_path)


        # Check whether OCR returned anything

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


        # Save OCR result and mark completed

        crud.update_ocr_status(
            db,
            processing_id,
            "completed",
            ocr_text
        )


        print("OCR completed successfully.")

        print("\nOCR TEXT:")
        print("----------------------------------------")
        print(ocr_text)
        print("----------------------------------------")


        # ====================================================
        # GEMINI PROCESSING
        # ====================================================

        print("\n========================================")
        print("GEMINI PROCESSING")
        print("========================================")


        # Mark Gemini as processing

        crud.update_gemini_status(
            db,
            processing_id,
            "processing"
        )


        print("Sending OCR text to Gemini...")


        structured_data = extract_information(
            ocr_text
        )


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


        # Save Gemini result and mark completed

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

        print("----------------------------------------")


        # ====================================================
        # PYDANTIC VALIDATION
        # ====================================================

        print("\nValidating extracted data...")


        validated_data = (
            schemas.ProcurementExtraction(
                **structured_data
            )
        )


        print(
            "Data validation completed."
        )


        # ====================================================
        # SAVE PROCUREMENT REQUEST
        # ====================================================

        print("\nSaving procurement request...")


        db_request = (
            crud.create_procurement_request(
                db,
                validated_data
            )
        )


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

        print("\n========================================")
        print(
            "INVOICE PROCESSING COMPLETED SUCCESSFULLY"
        )
        print("========================================")


    except Exception as e:

        print("\n========================================")
        print("ERROR PROCESSING INVOICE")
        print("========================================")

        print(str(e))

        print("========================================")


        # ----------------------------------------------------
        # Mark processing as failed
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

        db.close()