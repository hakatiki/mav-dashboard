#!/usr/bin/env python3
"""
JSON Output Organization Script
Organizes existing JSON files into date-based directories and tests the new structure.
"""

import os
import sys
from datetime import datetime
from date_utils import organize_existing_files, get_date_based_output_path, get_timestamped_filename
from mav_scraper import MAVScraper
from json_saver import JSONSaver

def organize_all_existing_files():
    """Organize all existing JSON files in output directories."""
    print("🗂️ Organizing Existing JSON Files")
    print("=" * 50)
    
    # Organize files in each output directory
    directories_to_organize = ['output', 'json_output']
    
    for directory in directories_to_organize:
        if os.path.exists(directory):
            print(f"\n📂 Organizing files in '{directory}':")
            organize_existing_files(directory, dry_run=False)
        else:
            print(f"\n📂 Directory '{directory}' does not exist - skipping")

def test_new_date_structure():
    """Test the new date-based directory structure."""
    print("\n🧪 Testing New Date-Based Structure")
    print("=" * 50)
    
    # Test date-based path creation
    base_dir = "test_output"
    output_path, date_folder = get_date_based_output_path(base_dir)
    print(f"📅 Date folder: {date_folder}")
    print(f"📂 Full path: {output_path}")
    
    # Test filename generation
    base_name = "test_route_12345_67890"
    filename = get_timestamped_filename(base_name)
    print(f"📄 Generated filename: {filename}")
    
    # Test with JSONSaver
    print(f"\n🔧 Testing JSONSaver with new structure...")
    try:
        saver = JSONSaver("test_json_output")
        print(f"✅ JSONSaver initialized successfully")
        print(f"📂 Base output directory: {saver.base_output_dir}")
        
        # Clean up test directory
        import shutil
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")
        if os.path.exists("test_json_output"):
            shutil.rmtree("test_json_output")
        
    except Exception as e:
        print(f"❌ Error testing JSONSaver: {e}")

def demo_structure():
    """Demonstrate the new directory structure."""
    print("\n📋 New Directory Structure")
    print("=" * 50)
    
    # Show what the structure looks like
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    structure = f"""
📁 json_output/
├── 📁 {current_date}/
│   ├── 📄 mav_routes_005510017_005517228_20250715_143022.json
│   ├── 📄 mav_routes_005510017_005517228_20250715_143022_compact.json
│   ├── 📄 simplified_005510017_005517228_20250715_143156.json
│   └── 📄 minimal_005510017_005517228_20250715_143156.json
├── 📁 2025-07-14/
│   ├── 📄 mav_routes_004302246_004305538_20250714_091122.json
│   └── 📄 simplified_004302246_004305538_20250714_091156.json
└── 📁 2025-07-13/
    └── 📄 mav_routes_005510033_005513912_20250713_163022.json

📁 output/
├── 📁 {current_date}/
│   ├── 📄 simplified_budapest_szeged_20250715_143456.json
│   └── 📄 koszeg_szombathely_routes_20250715_144022.json
└── 📁 2025-07-14/
    └── 📄 simplified_szombathely_koszeg_20250714_092156.json
"""
    
    print(structure)

def show_organization_benefits():
    """Show the benefits of the new organization."""
    print("\n💡 Benefits of Date-Based Organization")
    print("=" * 50)
    
    benefits = [
        "📅 Easy to find files by date",
        "🗂️ Automatic cleanup by removing old date folders",
        "📊 Better analysis of usage patterns over time",
        "🚀 Faster file access for recent data",
        "🧹 Cleaner directory structure",
        "📈 Easy to track API usage by day",
        "🔍 Simplified log analysis and debugging"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")

def main():
    """Main function."""
    print("🗂️ MÁV JSON Output Organization Tool")
    print("=" * 50)
    
    # Show help information
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Available commands:")
        print("  python organize_json_outputs.py               - Organize existing files")
        print("  python organize_json_outputs.py --dry-run     - Preview organization")
        print("  python organize_json_outputs.py --demo        - Show demo structure")
        print("  python organize_json_outputs.py --test        - Test new structure")
        return
    
    # Check for flags
    dry_run = '--dry-run' in sys.argv
    demo_only = '--demo' in sys.argv
    test_only = '--test' in sys.argv
    
    if demo_only:
        demo_structure()
        show_organization_benefits()
        return
    
    if test_only:
        test_new_date_structure()
        return
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("=" * 50)
        
        directories_to_check = ['output', 'json_output']
        for directory in directories_to_check:
            if os.path.exists(directory):
                print(f"\n📂 Preview organization for '{directory}':")
                organize_existing_files(directory, dry_run=True)
            else:
                print(f"\n📂 Directory '{directory}' does not exist - skipping")
        return
    
    # Show current structure
    print("📋 Current structure:")
    for directory in ['output', 'json_output']:
        if os.path.exists(directory):
            files = [f for f in os.listdir(directory) if f.endswith('.json')]
            if files:
                print(f"  📁 {directory}/: {len(files)} JSON files")
                for f in files[:3]:  # Show first 3 files
                    print(f"    📄 {f}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")
            else:
                print(f"  📁 {directory}/: empty")
    
    # Ask for confirmation
    response = input("\n❓ Organize files into date-based directories? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Organization cancelled")
        return
    
    # Organize existing files
    organize_all_existing_files()
    
    # Show demo structure
    demo_structure()
    show_organization_benefits()
    
    print("\n✅ Organization complete!")
    print("\n💡 From now on, all new JSON files will be automatically saved to date-based directories.")

if __name__ == "__main__":
    main() 