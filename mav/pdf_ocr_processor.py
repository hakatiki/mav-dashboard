#!/usr/bin/env python3
"""
Enhanced PDF OCR Processor - Converts scanned PDF to searchable text with better table handling
"""

import os
import sys
from pathlib import Path
import json
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import argparse

def setup_tesseract():
    """Setup Tesseract OCR engine path for Windows"""
    # Common Tesseract installation paths on Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
    ]
    
    for path in possible_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            pytesseract.pytesseract.tesseract_cmd = expanded_path
            print(f"Found Tesseract at: {expanded_path}")
            return True
    
    # Try to use system PATH
    try:
        pytesseract.get_tesseract_version()
        print("Using Tesseract from system PATH")
        return True
    except:
        return False

def install_tesseract_instructions():
    """Provide instructions for installing Tesseract on Windows"""
    print("\n" + "="*60)
    print("TESSERACT OCR NOT FOUND")
    print("="*60)
    print("To use this script, you need to install Tesseract OCR:")
    print("\n1. Download Tesseract for Windows from:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print("\n2. Or use chocolatey:")
    print("   choco install tesseract")
    print("\n3. Or use winget:")
    print("   winget install UB-Mannheim.TesseractOCR")
    print("\n4. After installation, restart your terminal")
    print("="*60)

def enhance_image_for_ocr(image):
    """
    Enhance image quality for better OCR results, especially for tables and numbers
    """
    # Convert PIL image to OpenCV format
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to handle varying lighting
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Remove noise with morphological operations
    kernel = np.ones((1,1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Enhance contrast
    enhanced = cv2.convertScaleAbs(binary, alpha=1.2, beta=10)
    
    # Convert back to PIL Image
    enhanced_pil = Image.fromarray(enhanced)
    
    # Additional PIL enhancements
    enhancer = ImageEnhance.Contrast(enhanced_pil)
    enhanced_pil = enhancer.enhance(1.5)
    
    enhancer = ImageEnhance.Sharpness(enhanced_pil)
    enhanced_pil = enhancer.enhance(2.0)
    
    return enhanced_pil

def extract_text_with_multiple_methods(image, language='eng'):
    """
    Extract text using multiple OCR configurations for better results
    """
    results = []
    
    # Method 1: Standard OCR with table detection
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁÉÍÓÖŐÚÜŰáéíóöőúüű.,;:!?()-+*/=% '
    try:
        text1 = pytesseract.image_to_string(image, lang=language, config=custom_config)
        results.append(("Standard OCR", text1))
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: OCR optimized for tables and structured data
    table_config = r'--oem 3 --psm 4'
    try:
        text2 = pytesseract.image_to_string(image, lang=language, config=table_config)
        results.append(("Table OCR", text2))
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: OCR with sparse text detection
    sparse_config = r'--oem 3 --psm 11'
    try:
        text3 = pytesseract.image_to_string(image, lang=language, config=sparse_config)
        results.append(("Sparse OCR", text3))
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    # Method 4: Get structured data (word-level bounding boxes)
    try:
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
        structured_text = reconstruct_layout_from_data(data)
        results.append(("Structured OCR", structured_text))
    except Exception as e:
        print(f"Method 4 failed: {e}")
    
    return results

def reconstruct_layout_from_data(data):
    """
    Reconstruct text layout from OCR data to preserve table structure
    """
    lines = {}
    
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 30:  # Only use confident detections
            text = data['text'][i].strip()
            if text:
                top = data['top'][i]
                left = data['left'][i]
                
                # Group words by approximate line (within 10 pixels)
                line_key = round(top / 10) * 10
                if line_key not in lines:
                    lines[line_key] = []
                
                lines[line_key].append((left, text))
    
    # Sort lines by vertical position and words by horizontal position
    sorted_lines = []
    for line_key in sorted(lines.keys()):
        words = sorted(lines[line_key], key=lambda x: x[0])
        line_text = ' '.join([word[1] for word in words])
        sorted_lines.append(line_text)
    
    return '\n'.join(sorted_lines)

def choose_best_ocr_result(results):
    """
    Choose the best OCR result based on various criteria
    """
    if not results:
        return ""
    
    # Score each result
    scored_results = []
    for method, text in results:
        score = 0
        
        # Prefer longer texts (more content extracted)
        score += len(text) * 0.1
        
        # Prefer texts with more numbers (important for financial documents)
        score += sum(1 for c in text if c.isdigit()) * 0.5
        
        # Prefer texts with table-like structure (multiple spaces, tabs)
        score += text.count('  ') * 0.2  # Multiple spaces
        score += text.count('\t') * 0.3   # Tabs
        
        # Penalize texts with too many OCR errors (weird characters)
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in 'ÁÉÍÓÖŐÚÜŰáéíóöőúüű')
        score -= weird_chars * 0.1
        
        scored_results.append((score, method, text))
    
    # Sort by score and return the best result
    scored_results.sort(reverse=True)
    best_score, best_method, best_text = scored_results[0]
    
    print(f"    Best method: {best_method} (score: {best_score:.1f})")
    return best_text

def process_pdf_to_text(pdf_path, output_path=None, language='eng', enhance_images=True):
    """
    Convert scanned PDF to text using enhanced OCR with better table handling
    
    Args:
        pdf_path: Path to the scanned PDF file
        output_path: Path for output text file (optional)
        language: OCR language (default: 'eng')
        enhance_images: Whether to enhance images before OCR (default: True)
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    # Setup output path
    if output_path is None:
        output_path = pdf_path.with_suffix('_enhanced.txt')
    else:
        output_path = Path(output_path)
    
    print(f"Processing PDF: {pdf_path}")
    print(f"Output file: {output_path}")
    print(f"Image enhancement: {'Enabled' if enhance_images else 'Disabled'}")
    
    try:
        # Convert PDF to images with higher DPI for better quality
        print("Converting PDF pages to images...")
        images = convert_from_path(pdf_path, dpi=400)  # Increased DPI
        
        all_text = []
        total_pages = len(images)
        
        print(f"Processing {total_pages} pages with enhanced OCR...")
        
        for i, image in enumerate(images, 1):
            print(f"Processing page {i}/{total_pages}...")
            
            # Enhance image if requested
            if enhance_images:
                print(f"  Enhancing image quality...")
                enhanced_image = enhance_image_for_ocr(image)
            else:
                enhanced_image = image
            
            # Extract text using multiple methods
            print(f"  Running OCR with multiple methods...")
            ocr_results = extract_text_with_multiple_methods(enhanced_image, language)
            
            # Choose the best result
            best_text = choose_best_ocr_result(ocr_results)
            
            # Add page separator
            page_header = f"\n{'='*60}\nPAGE {i}\n{'='*60}\n"
            all_text.append(page_header + best_text)
            
            print("  ✓ Complete")
        
        # Save extracted text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_text))
        
        print(f"\n✅ Enhanced OCR processing completed!")
        print(f"📄 Extracted text saved to: {output_path}")
        print(f"📊 Total pages processed: {total_pages}")
        
        # Show a preview of the extracted text
        preview_length = 800
        full_text = '\n'.join(all_text)
        if len(full_text) > preview_length:
            preview = full_text[:preview_length] + "..."
        else:
            preview = full_text
        
        print(f"\n📋 Preview of extracted text:")
        print("-" * 40)
        print(preview)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert scanned PDF to searchable text using enhanced OCR')
    parser.add_argument('pdf_file', help='Path to the scanned PDF file')
    parser.add_argument('-o', '--output', help='Output text file path (optional)')
    parser.add_argument('-l', '--language', default='eng', help='OCR language (default: eng)')
    parser.add_argument('--no-enhance', action='store_true', help='Disable image enhancement')
    
    args = parser.parse_args()
    
    # Setup Tesseract
    if not setup_tesseract():
        install_tesseract_instructions()
        return 1
    
    # Process the PDF
    success = process_pdf_to_text(args.pdf_file, args.output, args.language, 
                                 enhance_images=not args.no_enhance)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 