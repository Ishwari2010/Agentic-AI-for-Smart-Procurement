from app.llm.gemini_client import extract_information
from app.schemas import ProcurementExtraction

sample_text = """
Requester Name: Rahul Sharma

Arduino Uno Board 10 5500
ESP32 Development Board 5 4250
Industrial Temperature Sensor 8 2560
Relay Module 4 3000

Grand Total: 18066
"""

# Gemini output
data = extract_information(sample_text)

print("\nGemini Output:")
print(data)

# Validate using Pydantic
validated = ProcurementExtraction(**data)

print("\nValidated Successfully!")
print(validated)