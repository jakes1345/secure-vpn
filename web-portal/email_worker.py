#!/usr/bin/env python3
"""
Email Worker - Background process for processing email queue
Run this as a systemd service for continuous email processing
"""

import time
import signal
import sys
from email_queue import process_email_queue, process_retry_queue, get_queue_stats

# Worker configuration
PROCESS_INTERVAL = 5  # Process queue every 5 seconds
RETRY_CHECK_INTERVAL = 60  # Check retry queue every 60 seconds
STATS_INTERVAL = 300  # Print stats every 5 minutes

running = True

def signal_handler(sig, frame):
    """Handle shutdown signal"""
    global running
    print("\n🛑 Shutting down email worker...")
    running = False
    sys.exit(0)

def main():
    """Main worker loop"""
    global running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 80)
    print("📧 EMAIL WORKER STARTING")
    print("=" * 80)
    print()
    print(f"Process interval: {PROCESS_INTERVAL}s")
    print(f"Retry check interval: {RETRY_CHECK_INTERVAL}s")
    print()
    
    last_retry_check = 0
    last_stats_print = time.time()
    
    while running:
        try:
            # Process main queue
            process_email_queue()
            
            # Check retry queue periodically
            now = time.time()
            if now - last_retry_check >= RETRY_CHECK_INTERVAL:
                process_retry_queue()
                last_retry_check = now
            
            # Print stats periodically
            if now - last_stats_print >= STATS_INTERVAL:
                stats = get_queue_stats()
                print(f"📊 Queue Stats: Queue={stats['queue_size']}, Retry={stats['retry_queue_size']}, DLQ={stats['dlq_size']}")
                last_stats_print = now
            
            # Sleep before next iteration
            time.sleep(PROCESS_INTERVAL)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Worker error: {e}")
            time.sleep(PROCESS_INTERVAL)
    
    print("✅ Email worker stopped")

if __name__ == '__main__':
    main()
