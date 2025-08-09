#!/usr/bin/env python3
"""
Web Service for MAV Scraper
Provides HTTP endpoints for triggering scraping and health checks.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Optional, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from automated_scraper import AutomatedMAVScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'mpt-all-sources')
PROJECT_ID = os.environ.get('PROJECT_ID', 'eti-industries')
CSV_FILE = './scraper/data/route_station_pairs.csv'

# Global variables for tracking scraping status
scraping_status = {
    'is_running': False,
    'start_time': None,
    'end_time': None,
    'progress': 0,
    'total': 0,
    'status': 'idle',
    'message': 'No scraping process active',
    'last_error': None,
    'upload_stats': {
        'incremental_uploads': 0,
        'incremental_files_uploaded': 0,
        'final_files_uploaded': 0,
        'total_upload_attempts': 0,
        'upload_errors': 0
    }
}
scraping_lock = threading.Lock()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def run_scraper():
    """Main endpoint that runs the MAV scraper when triggered."""
    global scraping_status
    
    try:
        logger.info(" Web service received request to run MAV scraper")
        
        # Parse request data (handle both GET and POST)
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
        else:
            data = {}
        
        # Determine action
        action = data.get('action', 'run_daily')
        
        if action == 'health_check':
            return health_check()
        
        elif action == 'status':
            return get_scraping_status()
        
        elif action == 'run_daily':
            return start_daily_scraping()
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown action: {action}',
                'timestamp': datetime.now().isoformat()
            }), 400
    
    except Exception as e:
        logger.error(f" Error in web service: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        logger.info(" Running health check...")
        
        # Create scraper instance for health check
        scraper = AutomatedMAVScraper(
            csv_file=CSV_FILE,
            bucket_name=BUCKET_NAME,
            project_id=PROJECT_ID
        )
        
        # Run health check
        is_healthy = scraper.health_check()
        
        if is_healthy:
            return jsonify({
                'status': 'healthy',
                'message': 'MAV scraper is ready',
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'bucket': BUCKET_NAME,
                    'project': PROJECT_ID,
                    'csv_file': CSV_FILE
                }
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Health check failed',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f" Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Health check error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def get_scraping_status():
    """Get current scraping status."""
    global scraping_status
    
    with scraping_lock:
        current_status = scraping_status.copy()
    
    # Calculate duration if running
    if current_status['is_running'] and current_status['start_time']:
        duration = (datetime.now() - current_status['start_time']).total_seconds()
        current_status['duration_seconds'] = duration
    
    return jsonify({
        'status': 'success',
        'scraping_status': current_status,
        'timestamp': datetime.now().isoformat()
    })

def start_daily_scraping():
    """Start the daily scraping process asynchronously."""
    global scraping_status
    
    with scraping_lock:
        if scraping_status['is_running']:
            return jsonify({
                'status': 'error',
                'message': 'Scraping is already running',
                'scraping_status': scraping_status,
                'timestamp': datetime.now().isoformat()
            }), 409
        
        # Reset status
        scraping_status.update({
            'is_running': True,
            'start_time': datetime.now(),
            'end_time': None,
            'progress': 0,
            'total': 0,
            'status': 'starting',
            'message': 'Scraping process initiated',
            'last_error': None,
            'upload_stats': {
                'incremental_uploads': 0,
                'incremental_files_uploaded': 0,
                'final_files_uploaded': 0,
                'total_upload_attempts': 0,
                'upload_errors': 0
            }
        })
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_daily_scraping_background, daemon=True)
    thread.start()
    
    logger.info(" Daily scraping started in background thread")
    
    return jsonify({
        'status': 'success',
        'message': 'Daily scraping started successfully in background',
        'scraping_status': scraping_status,
        'timestamp': datetime.now().isoformat(),
        'instructions': 'Use GET /status to check progress'
    })

def run_daily_scraping_background():
    """Run the daily scraping process in background."""
    global scraping_status
    
    try:
        start_time = datetime.now()
        logger.info(f" Starting daily MAV scraping at {start_time}")
        
        # Update status
        with scraping_lock:
            scraping_status.update({
                'status': 'running',
                'message': 'Creating scraper instance...'
            })
        
        # Create scraper instance
        scraper = AutomatedMAVScraper(
            csv_file=CSV_FILE,
            bucket_name=BUCKET_NAME,
            project_id=PROJECT_ID
        )
        
        # Update status with total count (will be updated once bulk scraping starts)
        with scraping_lock:
            scraping_status.update({
                'total': 966,  # Default estimate, will be updated when scraping starts
                'message': 'Initializing bulk scraper...'
            })
        
        # Custom progress tracking
        original_process_pair = scraper.bulk_scraper.process_pair
        
        def tracked_process_pair(*args, **kwargs):
            result = original_process_pair(*args, **kwargs)
            with scraping_lock:
                # Update progress and total count from bulk scraper stats
                scraping_status['progress'] = scraper.bulk_scraper.stats.get('processed', 0)
                total_pairs = scraper.bulk_scraper.stats.get('total_pairs', scraping_status['total'])
                if total_pairs != scraping_status['total']:
                    scraping_status['total'] = total_pairs
                
                if scraping_status['total'] > 0:
                    progress_pct = (scraping_status['progress'] / scraping_status['total']) * 100
                    # Check if incremental upload just happened
                    upload_info = ""
                    if hasattr(scraper, 'upload_stats') and scraper.upload_stats.get('incremental_uploads', 0) > 0:
                        upload_info = f" | Uploads: {scraper.upload_stats['incremental_uploads']}"
                    scraping_status['message'] = f'Processing pairs... {scraping_status["progress"]}/{scraping_status["total"]} ({progress_pct:.1f}%){upload_info}'
                    
                    # Update upload stats in real-time if available
                    if hasattr(scraper, 'upload_stats'):
                        scraping_status['upload_stats'] = scraper.upload_stats.copy()
            return result
        
        # Monkey patch for progress tracking
        scraper.bulk_scraper.process_pair = tracked_process_pair
        
        # Run scraping with incremental uploads every 100 pairs
        success = scraper.run_daily_scraping(
            max_pairs=None,  # Process all pairs
            delay=2.0,       # 2 second delay between requests
            upload=True,     # Upload to cloud
            incremental_upload_interval=100  # Upload every 100 processed pairs
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        with scraping_lock:
            # Get upload stats from scraper if available
            upload_stats = getattr(scraper, 'upload_stats', {
                'incremental_uploads': 0,
                'incremental_files_uploaded': 0,
                'final_files_uploaded': 0,
                'total_upload_attempts': 0,
                'upload_errors': 0
            })
            
            scraping_status.update({
                'is_running': False,
                'end_time': end_time,
                'status': 'completed' if success else 'failed',
                'message': f'Scraping {"completed successfully" if success else "failed"} in {duration}',
                'progress': scraper.bulk_scraper.stats.get('processed', 0),
                'upload_stats': upload_stats
            })
        
        if success:
            logger.info(f" Daily scraping completed successfully in {duration}")
        else:
            logger.error(f" Daily scraping failed after {duration}")
            
    except Exception as e:
        logger.error(f" Error in background scraping: {e}")
        with scraping_lock:
            scraping_status.update({
                'is_running': False,
                'end_time': datetime.now(),
                'status': 'error',
                'message': f'Scraping failed with error: {str(e)}',
                'last_error': str(e)
            })

if __name__ == '__main__':
    logger.info(" Starting MAV Scraper Web Service")
    
    # Health check on startup
    try:
        scraper = AutomatedMAVScraper(
            csv_file=CSV_FILE,
            bucket_name=BUCKET_NAME,
            project_id=PROJECT_ID
        )
        if scraper.health_check():
            logger.info(" Startup health check passed")
        else:
            logger.warning(" Startup health check failed")
    except Exception as e:
        logger.error(f" Startup health check error: {e}")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 