import os
import json

from dotenv import load_dotenv
from google import genai


# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()


# ============================================================
# Initialize Gemini Client
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# Gemini Information Extraction
# ============================================================

def extract_information(
    ocr_text: str,
    document_structure: str
):
    """
    Sends both Tesseract OCR text and Docling document
    structure to Gemini and returns structured procurement
    information.
    """

    prompt = f"""
You are an AI Information Extraction Agent for a Smart
Procurement System.

Your task is to extract procurement information from an invoice.

You are given TWO sources of information:

1. TESSERACT OCR TEXT
2. DOCLING DOCUMENT STRUCTURE

Use BOTH sources together to understand the invoice.

============================================================
TESSERACT OCR TEXT
============================================================

{ocr_text}


============================================================
DOCLING DOCUMENT STRUCTURE
============================================================

{document_structure}


============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON using exactly this structure:

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


============================================================
IMPORTANT EXTRACTION RULES
============================================================

1. Return ONLY valid JSON.

2. Do not include markdown.

3. Do not include explanations.

4. Extract the requester/buyer name from the invoice.

5. Extract EVERY procurement item listed in the invoice.

6. For EACH item, preserve the relationship between:
   - description
   - quantity
   - unit price
   - amount

7. IMPORTANT:
   Do NOT treat table columns as independent lists.

   For example, if an invoice contains:

   Description:
   Item A
   Item B
   Item C

   Quantity:
   2
   5
   1

   Amount:
   1000
   2500
   800

   The values must remain associated with their
   corresponding item.

8. Use the table structure from Docling to help determine
   row and column relationships.

9. Use the Tesseract OCR text to recover text that may have
   been missed or incorrectly represented by Docling.

10. If Tesseract and Docling contain slightly different
    representations of the same value, use the most
    consistent interpretation based on the complete invoice.

11. Do not invent information.

12. If a value is genuinely missing:
    - Use "" for missing text.
    - Use 0 for missing numeric values.

13. Quantity must be numeric.

14. estimated_cost must be numeric.

15. total_estimated_cost must be numeric.

16. For each item, use the item's invoice amount as
    estimated_cost when an amount is available.

17. Do not confuse:
    - subtotal
    - tax
    - GST
    - CGST
    - SGST
    - total amount

    with an individual item's estimated cost.

18. If the invoice contains multiple items, return ALL
    items in the "items" array.

19. Do not merge separate invoice items into one item.

20. Do not create items from bank details, invoice numbers,
    dates, GST numbers, phone numbers, or other non-item
    information.

21. The final total should represent the invoice's final
    total amount when clearly available.

============================================================
FINAL CHECK
============================================================

Before returning the JSON, verify that:

- Every visible invoice item is represented.
- Each quantity belongs to the correct item.
- Each amount belongs to the correct item.
- Taxes are not treated as item costs.
- The final total is not confused with an item amount.
- The JSON is syntactically valid.

Return ONLY the JSON.
"""

    # ========================================================
    # Call Gemini
    # ========================================================

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        result = response.text.strip()

        # ----------------------------------------------------
        # Remove Markdown Code Fences if Gemini adds them
        # ----------------------------------------------------

        if result.startswith("```"):

            result = result.replace("```json", "")
            result = result.replace("```", "")
            result = result.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        structured_data = json.loads(result)

        return structured_data

    except Exception as e:

        print("Gemini Error:", e)

        # IMPORTANT:
        # Do not return fake/empty structured data.
        # Propagate the error so kafka_consumer.py can mark
        # Gemini processing as failed and avoid inserting
        # an invalid procurement request.

        raise