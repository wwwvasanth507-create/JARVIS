"""
Unit tests for ImagePreprocessor.
"""

import pytest
from PIL import Image
from jarvis.computer.vision.preprocessing import ImagePreprocessor


def test_image_preprocessing_resize_and_crop():
    img = Image.new("RGB", (2000, 1500), color=(100, 100, 100))

    resized = ImagePreprocessor.resize_max_bounds(img, max_width=1000, max_height=800)
    assert resized.width <= 1000
    assert resized.height <= 800

    cropped = ImagePreprocessor.crop_region(img, 10, 10, 50, 50)
    assert cropped.width == 50
    assert cropped.height == 50


def test_perceptual_hash_calculation():
    img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))

    hash1 = ImagePreprocessor.compute_perceptual_hash(img1)
    hash2 = ImagePreprocessor.compute_perceptual_hash(img2)

    assert len(hash1) > 0
    assert hash1 == hash2
