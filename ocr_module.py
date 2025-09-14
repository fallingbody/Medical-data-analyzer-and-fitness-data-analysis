from PIL import Image
import pytesseract
import cv2
import numpy as np

def deskew(image):
    """Corrects the skew of a binary image."""
    gray = cv2.bitwise_not(image)
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    (h, w) = image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255))
    return rotated

def preprocess_image(image_path):
    """Applies a series of preprocessing steps to improve OCR accuracy."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    deskewed_image = deskew(thresh)
    return Image.fromarray(deskewed_image)

def extract_text_from_image(image_path):
    """
    Extracts text from an image using an improved preprocessing pipeline
    and optimized Tesseract configuration.
    """
    preprocessed_img = preprocess_image(image_path)
    custom_config = r'--oem 3 --psm 3'
    return pytesseract.image_to_string(preprocessed_img, config=custom_config)