#!/usr/bin/env python3
"""
Automated MAV Scraper for Cloud Deployment
Combines bulk scraping with automatic cloud upload.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import local modules
from bulk_scraper import BulkMAVScraper
from cloud_uploader import CloudUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AutomatedMAVScraper:
    """
    Automated scraper that runs the full pipeline:
    1. Bulk scraping of MAV data
    2. Automatic upload to Google Cloud Storage
    """
    
    def __init__(self, 
                 csv_file: str,
                 bucket_name: str,
                 project_id: Optional[str] = None,
                 output_dir: str = "json_output"):
        """
        Initialize the automated scraper.
        
        Args:
            csv_file: Path to CSV file with station pairs
            bucket_name: GCS bucket name for uploads
            project_id: Google Cloud project ID
            output_dir: Local output directory
        """
        self.csv_file = csv_file
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.output_dir = output_dir
        
        # Initialize components
        self.bulk_scraper = BulkMAVScraper(csv_file, output_dir)
        
        # Only initialize uploader if bucket is provided
        self.uploader = None
        if bucket_name:
            try:
                self.uploader = CloudUploader(bucket_name, project_id)
                logger.info(f"Cloud uploader initialized for bucket: {bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize cloud uploader: {e}")
                self.uploader = None
    
    def run_daily_scraping(self, 
                          max_pairs: Optional[int] = None,
                          delay: float = 2.0,
                          upload: bool = True,
                          incremental_upload_interval: int = 100) -> bool:
        """
        Run the daily scraping pipeline.
        
        Args:
            max_pairs: Maximum number of pairs to process
            delay: Delay between requests in seconds
            upload: Whether to upload results to cloud
            incremental_upload_interval: Upload every N processed pairs (0 to disable)
            
        Returns:
            True if successful, False otherwise
        """
        start_time = datetime.now()
        
        # Track upload statistics
        self.upload_stats = {
            'incremental_uploads': 0,
            'incremental_files_uploaded': 0,
            'final_files_uploaded': 0,
            'total_upload_attempts': 0,
            'upload_errors': 0
        }
        
        try:
            # Define incremental upload callback
            def incremental_upload_callback(processed_count, total_count, scraping_stats):
                """Callback for incremental uploads every N processed pairs."""
                if not upload or not self.uploader:
                    return
                
                try:
                    logger.info(f" Starting incremental upload #{self.upload_stats['incremental_uploads'] + 1} at {processed_count}/{total_count} processed pairs")
                    
                    # Get today's date for filtering
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    # Upload today's data
                    upload_results = self.uploader.upload_json_output(date_filter=today)
                    
                    successful_uploads = sum(1 for v in upload_results.values() if v)
                    total_files = len(upload_results)
                    
                    # Update statistics
                    self.upload_stats['incremental_uploads'] += 1
                    self.upload_stats['incremental_files_uploaded'] += successful_uploads
                    self.upload_stats['total_upload_attempts'] += total_files
                    
                    if total_files > 0:
                        upload_success_rate = successful_uploads / total_files
                        logger.info(f" Incremental upload #{self.upload_stats['incremental_uploads']} completed: {successful_uploads}/{total_files} files ({upload_success_rate*100:.1f}% success)")
                        
                        if upload_success_rate < 0.8:  # Less than 80% success
                            logger.warning(f" Some files failed in incremental upload #{self.upload_stats['incremental_uploads']}")
                            self.upload_stats['upload_errors'] += (total_files - successful_uploads)
                    else:
                        logger.info(f" Incremental upload #{self.upload_stats['incremental_uploads']}: No new files to upload")
                    
                except Exception as e:
                    logger.error(f" Incremental upload failed: {e}")
                    self.upload_stats['upload_errors'] += 1
                    # Continue scraping even if upload fails
                    logger.info(" Upload failed but continuing scraping process...")
            
            # Step 1: Run bulk scraping with incremental uploads
            logger.info(" Starting bulk scraping...")
            if upload and incremental_upload_interval > 0:
                logger.info(f"Incremental uploads enabled every {incremental_upload_interval} processed pairs")
                self.bulk_scraper.run_bulk_scraping(
                    max_pairs=max_pairs, 
                    base_delay_seconds=delay,
                    progress_callback=incremental_upload_callback,
                    progress_interval=incremental_upload_interval
                )
            else:
                self.bulk_scraper.run_bulk_scraping(max_pairs, delay)
            
            scraping_success = (self.bulk_scraper.stats['successful'] > 0 and 
                              self.bulk_scraper.stats['failed'] < self.bulk_scraper.stats['processed'] * 0.5)
            
            if not scraping_success:
                logger.error(" Scraping failed or had too many failures")
                return False
            
            logger.info(f" Scraping completed successfully: {self.bulk_scraper.stats['successful']}/{self.bulk_scraper.stats['processed']} pairs")
            
            # Step 2: Final upload to cloud (if enabled and configured)
            if upload and self.uploader:
                logger.info(" Starting final cloud upload...")
                
                # Get today's date for filtering
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Upload today's data (this will catch any files missed by incremental uploads)
                upload_results = self.uploader.upload_json_output(date_filter=today)
                
                successful_uploads = sum(1 for v in upload_results.values() if v)
                total_files = len(upload_results)
                
                # Update final upload statistics
                self.upload_stats['final_files_uploaded'] = successful_uploads
                self.upload_stats['total_upload_attempts'] += total_files
                
                if total_files > 0:
                    upload_success_rate = successful_uploads / total_files
                    logger.info(f" Final upload completed: {successful_uploads}/{total_files} files ({upload_success_rate*100:.1f}% success)")
                    
                    if upload_success_rate < 0.8:  # Less than 80% success
                        logger.warning(" Some files failed in final upload.")
                        self.upload_stats['upload_errors'] += (total_files - successful_uploads)
                else:
                    logger.info(" Final upload: No additional files to upload")
                
                # Log upload summary
                total_uploaded = self.upload_stats['incremental_files_uploaded'] + self.upload_stats['final_files_uploaded']
                logger.info(f" Upload Summary:")
                logger.info(f"   • Incremental uploads: {self.upload_stats['incremental_uploads']}")
                logger.info(f"   • Files uploaded incrementally: {self.upload_stats['incremental_files_uploaded']}")
                logger.info(f"   • Files uploaded in final: {self.upload_stats['final_files_uploaded']}")
                logger.info(f"   • Total files uploaded: {total_uploaded}")
                logger.info(f"   • Upload errors: {self.upload_stats['upload_errors']}")
            
            return True
            
        except Exception as e:
            logger.error(f" Automated scraping error: {e}")
            return False
        
        finally:
            # Calculate total duration
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Total pipeline duration: {duration}")
    
    def run_test_mode(self) -> bool:
        """Run in test mode with limited pairs."""
        logger.info(" Running in test mode...")
        return self.run_daily_scraping(max_pairs=3, delay=1.0, upload=False)
    
    def health_check(self) -> bool:
        """
        Perform health check for cloud deployment.
        
        Returns:
            True if system is healthy, False otherwise
        """
        try:
            # Check if CSV file exists
            if not os.path.exists(self.csv_file):
                logger.error(f" CSV file not found: {self.csv_file}")
                return False
            
            # Check if output directory can be created
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Check cloud uploader if configured
            if self.uploader:
                # This will verify gcloud authentication
                objects = self.uploader.list_bucket_contents()
                logger.info(f" Cloud connection verified. Bucket has {len(objects)} objects")
            
            logger.info(" Health check passed")
            return True
            
        except Exception as e:
            logger.error(f" Health check failed: {e}")
            return False


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="🚆 Automated MAV Scraper with Cloud Upload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run daily scraping with upload
  python automated_scraper.py routes.csv --bucket my-bucket --project my-project
  
  # Run without upload
  python automated_scraper.py routes.csv --no-upload
  
  # Test mode
  python automated_scraper.py routes.csv --test
  
  # Health check only
  python automated_scraper.py routes.csv --health-check
  
  # Custom settings
  python automated_scraper.py routes.csv --bucket my-bucket --max-pairs 100 --delay 2.0
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file with station pairs')
    parser.add_argument('--bucket', help='GCS bucket name for uploads')
    parser.add_argument('--project', help='Google Cloud project ID')
    parser.add_argument('--output-dir', default='json_output', help='Output directory (default: json_output)')
    parser.add_argument('--max-pairs', type=int, help='Maximum number of pairs to process')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--incremental-upload-interval', type=int, default=100, 
                       help='Upload every N processed pairs (default: 100, 0 to disable)')
    parser.add_argument('--no-upload', action='store_true', help='Skip cloud upload')
    parser.add_argument('--test', action='store_true', help='Run in test mode (3 pairs only)')
    parser.add_argument('--health-check', action='store_true', help='Run health check only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create automated scraper
    try:
        scraper = AutomatedMAVScraper(
            csv_file=args.csv_file,
            bucket_name=args.bucket,
            project_id=args.project,
            output_dir=args.output_dir
        )
        
        # Run based on mode
        if args.health_check:
            success = scraper.health_check()
            sys.exit(0 if success else 1)
        
        elif args.test:
            success = scraper.run_test_mode()
        
        else:
            upload = not args.no_upload
            success = scraper.run_daily_scraping(
                max_pairs=args.max_pairs,
                delay=args.delay,
                upload=upload,
                incremental_upload_interval=getattr(args, 'incremental_upload_interval', 100)
            )
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f" Failed to run automated scraper: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 