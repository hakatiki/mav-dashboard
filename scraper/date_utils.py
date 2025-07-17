"""
Date utilities for organizing JSON outputs by date (yyyy-mm-dd folders).
"""

import os
from datetime import datetime
from typing import Tuple

def get_date_based_output_path(base_output_dir: str, date: datetime = None) -> Tuple[str, str]:
    """
    Create a date-based output directory path.
    
    Args:
        base_output_dir: Base output directory (e.g., "json_output")
        date: Optional datetime object. If None, uses current date.
        
    Returns:
        Tuple of (full_output_path, date_folder_name)
        
    Example:
        get_date_based_output_path("json_output") 
        -> ("json_output/2025-07-15", "2025-07-15")
    """
    if date is None:
        date = datetime.now()
    
    # Create date folder name in yyyy-mm-dd format
    date_folder = date.strftime("%Y-%m-%d")
    
    # Create full path
    full_path = os.path.join(base_output_dir, date_folder)
    
    # Ensure directory exists
    os.makedirs(full_path, exist_ok=True)
    
    return full_path, date_folder

def get_timestamped_filename(base_name: str, extension: str = "json", date: datetime = None) -> str:
    """
    Generate a timestamped filename.
    
    Args:
        base_name: Base name for the file (without extension)
        extension: File extension (default: "json")
        date: Optional datetime object. If None, uses current time.
        
    Returns:
        Timestamped filename
        
    Example:
        get_timestamped_filename("mav_routes_005510017_005517228")
        -> "mav_routes_005510017_005517228_20250715_223456.json"
    """
    if date is None:
        date = datetime.now()
    
    timestamp = date.strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def organize_existing_files(output_dir: str, dry_run: bool = True) -> None:
    """
    Organize existing JSON files into date-based subdirectories.
    Looks for files with timestamps in their names and moves them to appropriate date folders.
    
    Args:
        output_dir: Directory containing JSON files to organize
        dry_run: If True, only shows what would be moved without actually moving files
    """
    if not os.path.exists(output_dir):
        print(f"❌ Directory not found: {output_dir}")
        return
    
    files_to_move = []
    
    # Find JSON files with timestamps
    for filename in os.listdir(output_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(output_dir, filename)
        if os.path.isdir(filepath):
            continue
        
        # Try to extract date from filename
        # Look for patterns like: _20250715_ or _20250715_223456
        import re
        timestamp_match = re.search(r'_(\d{8})_\d{6}', filename)
        if not timestamp_match:
            timestamp_match = re.search(r'_(\d{8})', filename)
        
        if timestamp_match:
            date_str = timestamp_match.group(1)
            try:
                # Parse date (YYYYMMDD)
                file_date = datetime.strptime(date_str, "%Y%m%d")
                date_folder = file_date.strftime("%Y-%m-%d")
                
                # Determine new path
                new_dir = os.path.join(output_dir, date_folder)
                new_path = os.path.join(new_dir, filename)
                
                files_to_move.append({
                    'old_path': filepath,
                    'new_path': new_path,
                    'new_dir': new_dir,
                    'date_folder': date_folder,
                    'filename': filename
                })
            except ValueError:
                # Invalid date format, skip
                continue
    
    if not files_to_move:
        print(f"📂 No files found to organize in {output_dir}")
        return
    
    print(f"📂 Found {len(files_to_move)} files to organize:")
    
    # Group by date folder
    by_date = {}
    for item in files_to_move:
        date_folder = item['date_folder']
        if date_folder not in by_date:
            by_date[date_folder] = []
        by_date[date_folder].append(item)
    
    for date_folder, items in sorted(by_date.items()):
        print(f"\n📅 {date_folder} ({len(items)} files):")
        
        if not dry_run:
            # Create directory
            os.makedirs(items[0]['new_dir'], exist_ok=True)
        
        for item in items:
            if dry_run:
                print(f"   📄 {item['filename']} → {date_folder}/{item['filename']}")
            else:
                try:
                    # Move file
                    os.rename(item['old_path'], item['new_path'])
                    print(f"   ✅ Moved {item['filename']} → {date_folder}/{item['filename']}")
                except Exception as e:
                    print(f"   ❌ Failed to move {item['filename']}: {e}")
    
    if dry_run:
        print(f"\n💡 This was a dry run. To actually move files, run:")
        print(f"   from date_utils import organize_existing_files")
        print(f"   organize_existing_files('{output_dir}', dry_run=False)")
    else:
        print(f"\n✅ File organization complete!")

if __name__ == "__main__":
    # Demo usage
    base_dir = "json_output"
    date_path, date_folder = get_date_based_output_path(base_dir)
    print(f"📂 Date-based path: {date_path}")
    print(f"📅 Date folder: {date_folder}")
    
    filename = get_timestamped_filename("test_route_12345_67890")
    print(f"📄 Timestamped filename: {filename}")
    
    # Show organization preview for existing files
    print(f"\n📋 Preview of file organization:")
    organize_existing_files("json_output", dry_run=True)
    organize_existing_files("output", dry_run=True) 