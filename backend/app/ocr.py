import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path


def extract_text(file_path: str):

    extracted_text = ""

    extension = os.path.splitext(file_path)[1].lower()

    # ---------- PDF ----------
    if extension == ".pdf":

        pages = convert_from_path(file_path)

        for page in pages:

            text = pytesseract.image_to_string(page)

            extracted_text += text
            extracted_text += "\n"

    # ---------- Images ----------
    elif extension in [".png", ".jpg", ".jpeg"]:

        image = Image.open(file_path)

        extracted_text = pytesseract.image_to_string(image)

    else:

        raise Exception("Unsupported file type.")

    return extracted_text