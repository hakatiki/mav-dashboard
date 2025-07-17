#!/usr/bin/env python3
"""
Hungarian OCR Processor - Optimized for Hungarian text on blurry PDFs
"""

import os
import sys
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
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

def preprocess_image_for_hungarian(pil_img):
    """
    Preprocess image specifically for Hungarian OCR on blurry PDFs
    """
    # Convert to grayscale
    img = np.array(pil_img.convert('L'))
    
    # Upscale image for better OCR (2x scaling)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Apply Gaussian blur to remove noise
    img = cv2.GaussianBlur(img, (3, 3), 0)
    
    # Use OTSU thresholding for automatic binarization
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Optional: Apply morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    return Image.fromarray(img)

def alternative_preprocess_adaptive(pil_img):
    """
    Alternative preprocessing using adaptive thresholding
    """
    img = np.array(pil_img.convert('L'))
    
    # Upscale
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Apply adaptive thresholding
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                               cv2.THRESH_BINARY, 11, 2)
    
    return Image.fromarray(img)

def extract_text_hungarian_optimized(image, use_structured=False):
    """
    Extract text using Hungarian language model with multiple PSM modes
    """
    results = []
    
    # Set up language - try Hungarian first, fallback to English
    languages = ['hun', 'eng']
    
    for lang in languages:
        try:
            # Test if language is available
            pytesseract.get_languages()
            
            # PSM 6: Uniform block of text (best for paragraphs)
            try:
                config = f'--oem 3 --psm 6'
                text = pytesseract.image_to_string(image, lang=lang, config=config)
                results.append((f"{lang}_uniform", text, len(text)))
            except Exception as e:
                print(f"PSM 6 failed for {lang}: {e}")
            
            # PSM 4: Single column of text of variable sizes
            try:
                config = f'--oem 3 --psm 4'
                text = pytesseract.image_to_string(image, lang=lang, config=config)
                results.append((f"{lang}_column", text, len(text)))
            except Exception as e:
                print(f"PSM 4 failed for {lang}: {e}")
            
            # PSM 11: Sparse text
            try:
                config = f'--oem 3 --psm 11'
                text = pytesseract.image_to_string(image, lang=lang, config=config)
                results.append((f"{lang}_sparse", text, len(text)))
            except Exception as e:
                print(f"PSM 11 failed for {lang}: {e}")
            
            # Structured output if requested
            if use_structured:
                try:
                    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
                    structured_text = reconstruct_structured_layout(data)
                    results.append((f"{lang}_structured", structured_text, len(structured_text)))
                except Exception as e:
                    print(f"Structured OCR failed for {lang}: {e}")
            
            # If Hungarian worked, prioritize it
            if lang == 'hun' and results:
                break
                
        except Exception as e:
            print(f"Language {lang} not available: {e}")
            continue
    
    return results

def reconstruct_structured_layout(data):
    """
    Reconstruct text layout from OCR data with better spacing for tables
    """
    lines = {}
    
    for i in range(len(data['text'])):
        confidence = int(data['conf'][i])
        text = data['text'][i].strip()
        
        if confidence > 30 and text:  # Only confident detections
            top = data['top'][i]
            left = data['left'][i]
            width = data['width'][i]
            height = data['height'][i]
            
            # Group words by line (within 20 pixels vertically)
            line_key = round(top / 20) * 20
            if line_key not in lines:
                lines[line_key] = []
            
            lines[line_key].append((left, text, confidence, width))
    
    # Sort lines by vertical position and words by horizontal position
    sorted_lines = []
    for line_key in sorted(lines.keys()):
        words = sorted(lines[line_key], key=lambda x: x[0])
        
        # Reconstruct line with appropriate spacing for tables
        line_parts = []
        prev_right = 0
        
        for left, text, conf, width in words:
            # Add extra spaces for large gaps (likely table columns)
            gap = left - prev_right
            if prev_right > 0 and gap > 100:  # Large gap = new column
                line_parts.append("    ")  # Tab-like spacing
            elif prev_right > 0 and gap > 50:  # Medium gap
                line_parts.append("  ")   # Double space
            
            line_parts.append(text)
            prev_right = left + width
        
        if line_parts:
            sorted_lines.append(" ".join(line_parts))
    
    return "\n".join(sorted_lines)

def choose_best_hungarian_result(results):
    """
    Choose the best OCR result optimized for Hungarian text
    """
    if not results:
        return "", "None", 0
    
    scored_results = []
    for method, text, length in results:
        score = 0
        
        # Base score on length
        score += length * 0.1
        
        # Bonus for Hungarian characters
        hungarian_chars = sum(1 for c in text if c in 'ÁÉÍÓÖŐÚÜŰáéíóöőúüű')
        score += hungarian_chars * 1.0  # Higher weight for Hungarian chars
        
        # Bonus for numbers (important in financial documents)
        digits = sum(1 for c in text if c.isdigit())
        score += digits * 0.5
        
        # Bonus for proper word patterns
        words = text.split()
        if words:
            # Bonus for capitalized words (proper nouns, beginnings)
            capitalized = sum(1 for word in words if word and word[0].isupper())
            score += capitalized * 0.3
            
            # Bonus for common Hungarian words
            hungarian_words = ['és', 'vagy', 'hogy', 'ezt', 'azt', 'egy', 'nem', 'van', 'volt', 'lesz', 'Ft', 'millió', 'ezer']
            for word in words:
                if word.lower() in hungarian_words:
                    score += 2.0
        
        # Bonus for structured content (multiple lines)
        lines = text.count('\n')
        score += lines * 0.3
        
        # Penalty for weird characters
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in 'ÁÉÍÓÖŐÚÜŰáéíóöőúüű')
        score -= weird_chars * 0.3
        
        # Bonus for Hungarian language model results
        if method.startswith('hun_'):
            score += 10.0  # Strong preference for Hungarian
        
        scored_results.append((score, method, text))
    
    # Sort by score and return the best
    scored_results.sort(reverse=True)
    best_score, best_method, best_text = scored_results[0]
    
    return best_text, best_method, best_score

def process_pdf_hungarian(pdf_path, output_path=None, use_structured=False):
    """
    Process PDF optimized for Hungarian text recognition
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    # Setup output path
    if output_path is None:
        output_path = pdf_path.with_suffix('_hungarian.txt')
    else:
        output_path = Path(output_path)
    
    print(f"Processing PDF: {pdf_path}")
    print(f"Output file: {output_path}")
    print(f"Structured output: {'Enabled' if use_structured else 'Disabled'}")
    
    # Set environment variable for Hungarian language data
    current_dir = Path.cwd()
    if (current_dir / 'hun.traineddata').exists():
        os.environ['TESSDATA_PREFIX'] = str(current_dir)
        print(f"Using local Hungarian language data: {current_dir}")
    
    try:
        # Convert PDF to images with high DPI (400 DPI for better quality)
        print("Converting PDF pages to images at 400 DPI...")
        images = convert_from_path(pdf_path, dpi=400)
        
        all_text = []
        total_pages = len(images)
        
        print(f"Processing {total_pages} pages with Hungarian OCR...")
        
        for i, image in enumerate(images, 1):
            print(f"Processing page {i}/{total_pages}...")
            
            # Try different preprocessing methods
            preprocessed_images = []
            
            # Method 1: OTSU thresholding
            img1 = preprocess_image_for_hungarian(image)
            preprocessed_images.append(("OTSU", img1))
            
            # Method 2: Adaptive thresholding
            img2 = alternative_preprocess_adaptive(image)
            preprocessed_images.append(("Adaptive", img2))
            
            # Method 3: Original image (mild enhancement)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            img3 = enhancer.enhance(1.1)
            preprocessed_images.append(("Original", img3))
            
            # Test OCR on all preprocessed versions
            all_results = []
            for prep_method, prep_img in preprocessed_images:
                print(f"  Testing {prep_method} preprocessing...")
                results = extract_text_hungarian_optimized(prep_img, use_structured)
                
                # Add preprocessing method to result names
                for method, text, length in results:
                    all_results.append((f"{prep_method}_{method}", text, length))
            
            # Choose the best result
            if all_results:
                best_text, best_method, best_score = choose_best_hungarian_result(all_results)
                print(f"  Best method: {best_method} (score: {best_score:.1f})")
                
                # Show top 3 results
                scored = [(score, method, text) for score, method, text in 
                         [(choose_best_hungarian_result([(m, t, l)])[2], m, t) 
                          for m, t, l in all_results]]
                scored.sort(reverse=True)
                
                print(f"  Top methods:")
                for j, (score, method, text) in enumerate(scored[:3]):
                    preview = text[:100].replace('\n', ' ').strip()
                    print(f"    {j+1}. {method}: {len(text)} chars - {preview}...")
            else:
                best_text = ""
                best_method = "None"
                print(f"  No successful OCR methods")
            
            # Add page separator
            page_header = f"\n{'='*60}\nPAGE {i} (Method: {best_method})\n{'='*60}\n"
            all_text.append(page_header + best_text)
            
            print("  ✓ Complete")
        
        # Save extracted text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_text))
        
        print(f"\n✅ Hungarian OCR processing completed!")
        print(f"📄 Extracted text saved to: {output_path}")
        print(f"📊 Total pages processed: {total_pages}")
        
        # Show a preview
        preview_length = 1000
        full_text = '\n'.join(all_text)
        if len(full_text) > preview_length:
            preview = full_text[:preview_length] + "..."
        else:
            preview = full_text
        
        print(f"\n📋 Preview of extracted text:")
        print("-" * 50)
        print(preview)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert scanned PDF to text using Hungarian-optimized OCR')
    parser.add_argument('pdf_file', help='Path to the scanned PDF file')
    parser.add_argument('-o', '--output', help='Output text file path (optional)')
    parser.add_argument('--structured', action='store_true', help='Enable structured output for tables')
    
    args = parser.parse_args()
    
    # Setup Tesseract
    if not setup_tesseract():
        print("Tesseract not found!")
        return 1
    
    # Process the PDF
    success = process_pdf_hungarian(args.pdf_file, args.output, args.structured)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 