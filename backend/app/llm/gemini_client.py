import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Initialize Gemini Client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def extract_information(ocr_text: str):
    """
    Sends OCR text to Gemini and returns structured procurement information.
    """

    prompt = f"""
You are an AI Information Extraction Agent for a Smart Procurement System.

Extract the procurement details from the OCR text.

Return ONLY valid JSON.

JSON Schema:

{{
  "requester_name": "",
  "items": [
    {{
      "description": "",
      "quantity": 0,
      "estimated_cost": 0
    }}
  ],
  "total_estimated_cost": 0
}}

Rules:
- Return ONLY JSON.
- Do not include markdown.
- Do not include explanations.
- If information is missing, use "" or 0.
- Quantity and estimated_cost must be numeric.

OCR TEXT:

{ocr_text}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        result = response.text.strip()

        # Remove markdown if Gemini wraps the JSON
        if result.startswith("```"):
            result = result.replace("```json", "")
            result = result.replace("```", "")
            result = result.strip()

        return json.loads(result)

    except Exception as e:

        print("Gemini Error:", e)

        return {
            "requester_name": "",
            "items": [],
            "total_estimated_cost": 0,
            "error": str(e)
        }