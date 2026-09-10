"""
Image preprocessing and perceptual hash utilities for screen vision.
"""

import hashlib
from typing import Tuple
from PIL import Image, ImageOps, ImageEnhance


class ImagePreprocessor:
    """
    Handles image scaling, cropping, contrast enhancement, and perceptual hash generation.
    """

    @staticmethod
    def resize_max_bounds(img: Image.Image, max_width: int = 1280, max_height: int = 720) -> Image.Image:
        """Resizes image to fit within max_width and max_height while preserving aspect ratio."""
        if img.width <= max_width and img.height <= max_height:
            return img

        res = img.copy()
        res.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return res

    @staticmethod
    def crop_region(img: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
        """Crops specified bounding box region."""
        box = (x, y, x + width, y + height)
        return img.crop(box)

    @staticmethod
    def enhance_for_ocr(img: Image.Image) -> Image.Image:
        """Converts to grayscale and enhances contrast for OCR accuracy."""
        gray = img.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        return enhancer.enhance(1.8)

    @staticmethod
    def compute_perceptual_hash(img: Image.Image, hash_size: int = 8) -> str:
        """
        Computes difference hash (dHash) for fast screen change detection.
        """
        # Resize to (hash_size + 1, hash_size) in grayscale
        resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
        if hasattr(resized, "get_flattened_data"):
            pixels = list(resized.get_flattened_data())
        else:
            pixels = list(resized.getdata())

        difference = []
        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = pixels[row * (hash_size + 1) + col]
                pixel_right = pixels[row * (hash_size + 1) + col + 1]
                difference.append(pixel_left > pixel_right)

        decimal_value = 0
        hex_string = []
        for i, val in enumerate(difference):
            if val:
                decimal_value += 2 ** (i % 8)
            if (i % 8) == 7:
                hex_string.append(f"{decimal_value:02x}")
                decimal_value = 0

        return "".join(hex_string)
