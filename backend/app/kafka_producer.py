import json

from kafka import KafkaProducer


KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "invoice-topic"


producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda value:
        json.dumps(value).encode("utf-8")
)


def publish_invoice_event(
    processing_id: int,
    filename: str,
    file_path: str
):

    event = {
        "event": "invoice.received",

        "processing_id": processing_id,

        "filename": filename,

        "file_path": file_path
    }

    future = producer.send(
        KAFKA_TOPIC,
        value=event
    )

    # Wait for Kafka confirmation
    future.get(timeout=10)

    producer.flush()

    return event