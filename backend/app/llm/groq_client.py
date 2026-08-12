import os
import json

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()


# ============================================================
# Initialize Groq Client
# ============================================================

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# Groq Information Extraction
# ============================================================

def extract_information(
    ocr_text: str,
    document_structure: str
):
    """
    Sends both Tesseract OCR text and Docling document
    structure to Groq and returns structured procurement
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
    "address": "",
    "phone_number": "",
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

5. Extract the requester/buyer's address when available.

6. Extract the requester/buyer's phone number when available.

7. If the address is genuinely missing, return "".

8. If the phone number is genuinely missing, return "".

9. Preserve the phone number as TEXT.
   Do not convert it into a numeric value.
   Preserve country codes, + signs, leading zeros,
   and other meaningful formatting when possible.

10. If the invoice contains both buyer/requester and
    vendor/supplier information, do NOT confuse them.

11. Extract the buyer/requester address and phone number,
    not the vendor/supplier address and phone number,
    when the invoice clearly identifies both separately.

12. Extract EVERY procurement item listed in the invoice.

13. For EACH item, preserve the relationship between:
    - description
    - quantity
    - unit price
    - amount

14. IMPORTANT:
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

15. Use the table structure from Docling to help determine
    row and column relationships.

16. Use the Tesseract OCR text to recover text that may have
    been missed or incorrectly represented by Docling.

17. If Tesseract and Docling contain slightly different
    representations of the same value, use the most
    consistent interpretation based on the complete invoice.

18. Do not invent information.

19. If a value is genuinely missing:

    - Use "" for missing text.
    - Use 0 for missing numeric values.

20. Quantity must be numeric.

21. estimated_cost must be numeric.

22. total_estimated_cost must be numeric.

23. For each item, use the item's invoice amount as
    estimated_cost when an amount is available.

24. Do not confuse:

    - subtotal
    - tax
    - GST
    - CGST
    - SGST
    - total amount

    with an individual item's estimated cost.

25. If the invoice contains multiple items, return ALL
    items in the "items" array.

26. Do not merge separate invoice items into one item.

27. Do not create items from:

    - bank details
    - invoice numbers
    - dates
    - GST numbers
    - phone numbers
    - addresses
    - other non-item information

28. The final total should represent the invoice's final
    total amount when clearly available.

29. If the invoice has multiple items, make sure each item's
    quantity and amount belong to the correct description.


============================================================
FINAL CHECK
============================================================

Before returning the JSON, verify that:

- Requester name is correct.
- Requester address is correct when available.
- Requester phone number is correct when available.
- Vendor information has not been confused with requester
  information.
- Every visible invoice item is represented.
- Each quantity belongs to the correct item.
- Each amount belongs to the correct item.
- Taxes are not treated as item costs.
- The final total is not confused with an item amount.
- The JSON is syntactically valid.

Return ONLY the JSON.
"""

    # ========================================================
    # Call Groq
    # ========================================================

    try:

        print(
            "Sending OCR text and Docling "
            "document structure to Groq..."
        )

        response = client.responses.create(
            model="llama-3.3-70b-versatile",
            input=prompt
        )

        result = response.output_text.strip()

        # ----------------------------------------------------
        # Remove Markdown Code Fences
        # ----------------------------------------------------

        if result.startswith("```"):

            result = result.replace(
                "```json",
                ""
            )

            result = result.replace(
                "```",
                ""
            )

            result = result.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        structured_data = json.loads(result)

        return structured_data

    except Exception as e:

        print("Groq Error:", e)

        # IMPORTANT:
        # Propagate the error so llm_client.py can
        # automatically fall back to Gemini.

        raise