#!/usr/bin/env python3
"""
Cloud uploader for MAV scraper data.
Uploads JSON files to Google Cloud Storage using gcloud CLI.
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Union
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global cache for gcloud availability to avoid repeated checks
_gcloud_cache = {
    'checked': False,
    'available': False,
    'gcloud_cmd': None
}


class CloudUploader:
    """
    Upload MAV scraper data to Google Cloud Storage using gcloud CLI.
    """
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize the cloud uploader.
        
        Args:
            bucket_name: Name of the GCS bucket
            project_id: Google Cloud project ID (optional)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.base_path = "blog/mav/json_output"
        
        # Verify gcloud is installed and authenticated
        if not self._check_gcloud():
            raise RuntimeError("gcloud CLI not found or not authenticated")
    
    def _check_gcloud(self) -> bool:
        """Check if gcloud CLI is available and authenticated."""
        global _gcloud_cache
        
        # Return cached result if already checked
        if _gcloud_cache['checked']:
            if _gcloud_cache['available']:
                self.gcloud_cmd = _gcloud_cache['gcloud_cmd']
                logger.debug(f"Using cached gcloud: {self.gcloud_cmd}")
                return True
            else:
                return False
        
        try:
            # Try different gcloud executable names for Windows compatibility
            gcloud_commands = ['gcloud', 'gcloud.cmd']
            
            for gcloud_cmd in gcloud_commands:
                try:
                    # Check if gcloud is installed with timeout
                    result = subprocess.run([gcloud_cmd, '--version'], 
                                          capture_output=True, text=True, check=False, timeout=10)
                    if result.returncode == 0:
                        self.gcloud_cmd = gcloud_cmd
                        _gcloud_cache['gcloud_cmd'] = gcloud_cmd
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            else:
                logger.error("gcloud CLI not found or timed out. Please install Google Cloud SDK.")
                _gcloud_cache['checked'] = True
                _gcloud_cache['available'] = False
                return False
            
            # Check if authenticated with timeout
            result = subprocess.run([self.gcloud_cmd, 'auth', 'list', '--filter=status:ACTIVE'], 
                                  capture_output=True, text=True, check=False, timeout=10)
            if result.returncode != 0 or 'ACTIVE' not in result.stdout:
                logger.error("No active gcloud authentication found. Run 'gcloud auth login'")
                _gcloud_cache['checked'] = True
                _gcloud_cache['available'] = False
                return False
                
            logger.info(f"gcloud CLI is available and authenticated (using {self.gcloud_cmd})")
            _gcloud_cache['checked'] = True
            _gcloud_cache['available'] = True
            return True
            
        except Exception as e:
            logger.error(f"Error checking gcloud: {e}")
            return False
    
    def _run_gcloud_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """
        Run a gcloud command and return the result.
        
        Args:
            command: List of command parts
            
        Returns:
            CompletedProcess result
        """
        full_command = [getattr(self, 'gcloud_cmd', 'gcloud')] + command
        if self.project_id:
            full_command.extend(['--project', self.project_id])
            
        logger.debug(f"Running command: {' '.join(full_command)}")
        
        try:
            # Add timeout to prevent hanging uploads (5 minutes should be more than enough)
            result = subprocess.run(full_command, capture_output=True, text=True, check=False, timeout=300)
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Gcloud command timed out after 300 seconds: {' '.join(full_command)}")
            # Return a failed result instead of raising
            return subprocess.CompletedProcess(full_command, 1, '', 'Command timed out')
        except Exception as e:
            logger.error(f"Error running gcloud command: {e}")
            # Return a failed result instead of raising
            return subprocess.CompletedProcess(full_command, 1, '', str(e))
    
    def upload_file(self, local_path: str, remote_path: Optional[str] = None) -> bool:
        """
        Upload a single file to GCS.
        
        Args:
            local_path: Path to local file
            remote_path: Remote path in bucket (relative to base_path)
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return False
        
        if remote_path is None:
            # Use the filename in the base path
            remote_path = os.path.basename(local_path)
        
        # Construct full GCS path
        gcs_path = f"gs://{self.bucket_name}/{self.base_path}/{remote_path}"
        
        # Upload using gsutil cp (part of gcloud SDK)
        command = ['storage', 'cp', local_path, gcs_path]
        result = self._run_gcloud_command(command)
        
        if result.returncode == 0:
            logger.info(f"Successfully uploaded {local_path} -> {gcs_path}")
            return True
        else:
            logger.error(f"Failed to upload {local_path}: {result.stderr}")
            return False
    
    def upload_directory_contents(self, local_dir: str, remote_dir: str) -> Dict[str, bool]:
        """
        FIXED: Upload directory CONTENTS to GCS without creating nested directories.
        
        Args:
            local_dir: Path to local directory (e.g., "json_output/2025-07-18")
            remote_dir: Remote directory name (e.g., "2025-07-18")
            
        Returns:
            Dictionary mapping file paths to upload success status
        """
        if not os.path.exists(local_dir):
            logger.error(f"Local directory not found: {local_dir}")
            return {}
        
        # Construct target GCS path
        gcs_target = f"gs://{self.bucket_name}/{self.base_path}/{remote_dir}/"
        
        # FIXED: Upload contents of directory, not the directory itself
        # This prevents the nested directory issue
        source_pattern = os.path.join(local_dir, "*")
        
        command = ['storage', 'cp', '-r', source_pattern, gcs_target]
        
        result = self._run_gcloud_command(command)
        
        results = {}
        
        if result.returncode == 0:
            logger.info(f"Successfully uploaded directory contents {local_dir}/* -> {gcs_target}")
            # Mark all files as successful
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    results[file_path] = True
        else:
            logger.error(f"Failed to upload directory contents {local_dir}: {result.stderr}")
            # Mark all files as failed
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    results[file_path] = False
        
        return results
    
    def upload_json_output(self, date_filter: Optional[str] = None) -> Dict[str, bool]:
        """
        Upload all JSON files from the json_output directory.
        
        Args:
            date_filter: Optional date string to filter directories (e.g., '2025-07-15')
            
        Returns:
            Dictionary mapping file paths to upload success status
        """
        json_output_dir = "json_output"
        
        if not os.path.exists(json_output_dir):
            logger.error(f"JSON output directory not found: {json_output_dir}")
            return {}
        
        all_results = {}
        
        # Get all date directories
        for date_dir in os.listdir(json_output_dir):
            date_path = os.path.join(json_output_dir, date_dir)
            
            if not os.path.isdir(date_path):
                continue
                
            if date_filter and date_filter not in date_dir:
                continue
            
            logger.info(f"Uploading files from {date_dir}")
            results = self.upload_directory_contents(date_path, date_dir)
            all_results.update(results)
        
        return all_results
    
    def list_bucket_contents(self, prefix: Optional[str] = None) -> List[str]:
        """
        List contents of the bucket with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter results
            
        Returns:
            List of object names
        """
        command = ['storage', 'ls']
        
        if prefix:
            command.append(f"gs://{self.bucket_name}/{self.base_path}/{prefix}")
        else:
            command.append(f"gs://{self.bucket_name}/{self.base_path}/")
        
        result = self._run_gcloud_command(command)
        
        if result.returncode == 0:
            objects = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return objects
        else:
            logger.error(f"Failed to list bucket contents: {result.stderr}")
            return []
    
    def sync_directory(self, local_dir: str, remote_dir: Optional[str] = None, 
                      delete: bool = False) -> bool:
        """
        Sync a local directory with GCS using rsync.
        
        Args:
            local_dir: Path to local directory
            remote_dir: Remote directory in bucket (relative to base_path)
            delete: Whether to delete files in destination that don't exist in source
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(local_dir):
            logger.error(f"Local directory not found: {local_dir}")
            return False
        
        if remote_dir is None:
            remote_dir = os.path.basename(local_dir)
        
        # Construct full GCS path
        gcs_path = f"gs://{self.bucket_name}/{self.base_path}/{remote_dir}/"
        
        # Sync using gsutil rsync
        command = ['storage', 'rsync', '-r']
        if delete:
            command.append('-d')  # Delete files in destination
        command.extend([local_dir, gcs_path])
        
        result = self._run_gcloud_command(command)
        
        if result.returncode == 0:
            logger.info(f"Successfully synced {local_dir} -> {gcs_path}")
            return True
        else:
            logger.error(f"Failed to sync {local_dir}: {result.stderr}")
            return False


def main():
    """Command-line interface for the cloud uploader."""
    parser = argparse.ArgumentParser(description='Upload MAV scraper data to Google Cloud Storage')
    parser.add_argument('--bucket', required=True, help='GCS bucket name')
    parser.add_argument('--project', help='Google Cloud project ID')
    parser.add_argument('--file', help='Upload a single file')
    parser.add_argument('--directory', help='Upload a directory')
    parser.add_argument('--json-output', action='store_true', 
                       help='Upload all JSON output files')
    parser.add_argument('--date-filter', help='Filter by date (e.g., 2025-07-15)')
    parser.add_argument('--sync', action='store_true', 
                       help='Sync directory instead of just copying')
    parser.add_argument('--list', action='store_true', 
                       help='List bucket contents')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        uploader = CloudUploader(args.bucket, args.project)
        
        if args.list:
            objects = uploader.list_bucket_contents()
            print(f"Bucket contents ({len(objects)} objects):")
            for obj in objects:
                print(f"  {obj}")
        
        elif args.file:
            success = uploader.upload_file(args.file)
            if success:
                print(f"Successfully uploaded {args.file}")
            else:
                print(f"Failed to upload {args.file}")
                sys.exit(1)
        
        elif args.directory:
            if args.sync:
                success = uploader.sync_directory(args.directory)
                if success:
                    print(f"Successfully synced {args.directory}")
                else:
                    print(f"Failed to sync {args.directory}")
                    sys.exit(1)
            else:
                # For command line usage, use directory name as remote dir
                remote_dir_name = os.path.basename(args.directory.rstrip('/\\'))
                results = uploader.upload_directory_contents(args.directory, remote_dir_name)
                successful = sum(1 for v in results.values() if v)
                total = len(results)
                print(f"Uploaded {successful}/{total} files from {args.directory}")
        
        elif args.json_output:
            results = uploader.upload_json_output(args.date_filter)
            successful = sum(1 for v in results.values() if v)
            total = len(results)
            print(f"Uploaded {successful}/{total} JSON files")
            
            if total == 0:
                print("No files found to upload")
            elif successful < total:
                print("Some files failed to upload. Check the logs for details.")
                sys.exit(1)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
