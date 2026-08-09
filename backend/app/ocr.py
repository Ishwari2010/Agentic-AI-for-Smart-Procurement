import os
import pytesseract
import fitz
import cv2
import numpy as np

from PIL import Image


# ============================================================
# Tesseract Configuration
# ============================================================

# If Tesseract is not in PATH, uncomment and adjust this:
#
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )


# ============================================================
# OpenCV Preprocessing
# ============================================================

def preprocess_image(image):
    """
    Preprocess image using OpenCV before Tesseract OCR.
    """

    image_np = np.array(image)

    # PIL RGB -> OpenCV BGR
    image_cv = cv2.cvtColor(
        image_np,
        cv2.COLOR_RGB2BGR
    )

    # Convert to grayscale
    gray = cv2.cvtColor(
        image_cv,
        cv2.COLOR_BGR2GRAY
    )

    # Reduce noise
    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # Improve text/background separation
    processed = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return processed


# ============================================================
# Tesseract OCR
# ============================================================

def run_ocr(image):
    """
    Run Tesseract OCR on a preprocessed image.
    """

    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    return text


# ============================================================
# Main OCR Function
# ============================================================

def extract_text(file_path: str):

    extracted_text = ""

    extension = os.path.splitext(
        file_path
    )[1].lower()


    # ========================================================
    # PDF
    # ========================================================

    if extension == ".pdf":

        document = fitz.open(file_path)

        try:

            for page in document:

                # Render PDF page as image
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                # OpenCV preprocessing
                processed_image = preprocess_image(
                    image
                )

                # Tesseract OCR
                page_text = run_ocr(
                    processed_image
                )

                extracted_text += page_text
                extracted_text += "\n"

        finally:

            document.close()


    # ========================================================
    # Images
    # ========================================================

    elif extension in [
        ".png",
        ".jpg",
        ".jpeg"
    ]:

        image = Image.open(
            file_path
        ).convert("RGB")

        # OpenCV preprocessing
        processed_image = preprocess_image(
            image
        )

        # Tesseract OCR
        extracted_text = run_ocr(
            processed_image
        )


    # ========================================================
    # Unsupported file
    # ========================================================

    else:

        raise Exception(
            "Unsupported file type."
        )


    return extracted_text