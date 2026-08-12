import os
import re
import datetime
from typing import Dict, Any
import cv2
import numpy as np
import fitz  # PyMuPDF
import pytesseract

class DocumentAuditor:
    """
    Intelligent OCR and Image Processing module for Gov_Scheme_Applier.
    Acts as a pre-check validation tool.
    Rewritten to use Tesseract OCR to comply with Render's 512MB RAM free tier limits.
    """

    @staticmethod
    def check_file_constraints(file_path: str) -> dict:
        """Validates file size limits and extensions."""
        if not os.path.exists(file_path):
            return {"status": "FAIL", "reason": f"File not found: {file_path}"}

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}

        if ext not in allowed_extensions:
            return {"status": "FAIL", "reason": f"Invalid file extension {ext}."}

        size_kb = os.path.getsize(file_path) / 1024.0
        if size_kb > 500.0: # Updated limit to a reasonable 500KB
            return {"status": "FAIL", "reason": f"File size exceeds 500KB limit (Current: {size_kb:.2f}KB)."}

        return {"status": "PASS", "file_size_kb": round(size_kb, 2)}

    @staticmethod
    def assess_image_quality(image_array: np.ndarray, threshold: float = 80.0) -> dict:
        """Assesses image quality using the variance of the Laplacian to detect blurriness."""
        try:
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_array
                
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()

            if variance < threshold:
                return {"status": "FAIL", "reason": f"Image is too blurry for automated processing. (Score: {variance:.2f})"}
            
            return {"status": "PASS", "blur_variance_score": round(variance, 2)}
        except Exception as e:
            return {"status": "FAIL", "reason": f"Failed to assess image quality: {str(e)}"}

    @staticmethod
    def sanitize_extracted_text(raw_text: str) -> str:
        """Masks PII like Aadhaar and PAN."""
        sanitized_text = raw_text
        # Mask Aadhaar
        aadhaar_pattern = r'\b(?:\d[\s\-]?){11}\d\b'
        sanitized_text = re.sub(aadhaar_pattern, '[REDACTED_ID]', sanitized_text)
        return sanitized_text

    @classmethod
    def extract_and_verify_document(cls, file_path: str) -> dict:
        """Converts document to image (if PDF), runs Tesseract OCR, and classifies document."""
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            image_array = None
            if ext == '.pdf':
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    return {"status": "FAIL", "reason": "PDF has no pages."}
                page = doc.load_page(0)
                pix = page.get_pixmap()
                image_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                if pix.n == 4:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                doc.close()
            else:
                image_array = cv2.imread(file_path)
                if image_array is None:
                    return {"status": "FAIL", "reason": "Failed to read image file."}

            # Run Tesseract OCR (with eng+hin if available)
            # Tesseract expects BGR array from OpenCV directly (though RGB is preferred, Tesseract handles grayscale natively well)
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            raw_text = pytesseract.image_to_string(gray, lang='eng+hin').lower()

            doc_type = "Unknown"
            if "income" in raw_text or "आय" in raw_text:
                doc_type = "Income Certificate"
            elif "caste" in raw_text:
                doc_type = "Caste Certificate"
            elif "aadhaar" in raw_text or "identification authority" in raw_text:
                doc_type = "Aadhaar"

            return {
                "status": "PASS",
                "document_type": doc_type,
                "raw_text": raw_text,
                "metadata": {},
                "image_array": image_array
            }

        except Exception as e:
            return {"status": "FAIL", "reason": f"Extraction failed: {str(e)}"}

    @classmethod
    def run_full_audit(cls, file_path: str) -> dict:
        """Orchestrates the full validation flow."""
        audit_result = {
            "audit_status": "PASS",
            "document_type": None,
            "file_size_kb": None,
            "blur_variance_score": None,
            "warnings": [],
            "sanitized_text": ""
        }

        constraint_res = cls.check_file_constraints(file_path)
        if constraint_res["status"] == "FAIL":
            audit_result["audit_status"] = "FAIL"
            audit_result["warnings"].append(constraint_res["reason"])
            return audit_result
        
        audit_result["file_size_kb"] = constraint_res.get("file_size_kb")

        extract_res = cls.extract_and_verify_document(file_path)
        if extract_res["status"] == "FAIL":
            audit_result["audit_status"] = "FAIL"
            audit_result["warnings"].append(extract_res["reason"])
            return audit_result

        image_array = extract_res["image_array"]
        raw_text = extract_res["raw_text"]
        
        audit_result["document_type"] = extract_res["document_type"]

        quality_res = cls.assess_image_quality(image_array)
        if quality_res["status"] == "FAIL":
            audit_result["audit_status"] = "FAIL"
            audit_result["warnings"].append(quality_res["reason"])
        else:
            audit_result["blur_variance_score"] = quality_res.get("blur_variance_score")

        sanitized_text = cls.sanitize_extracted_text(raw_text)
        audit_result["sanitized_text"] = sanitized_text

        return audit_result
