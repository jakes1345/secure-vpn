#!/usr/bin/env python3
"""
Email Queue System - Redis-based reliable email delivery
Handles queuing, retries, and dead letter queue
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available. Install with: pip3 install redis")

# Redis configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Queue names
EMAIL_QUEUE = 'email:queue'
EMAIL_RETRY_QUEUE = 'email:retry'
EMAIL_DLQ = 'email:dlq'  # Dead Letter Queue
EMAIL_PROCESSING = 'email:processing'

# Retry configuration
MAX_RETRIES = 5
RETRY_BACKOFFS = [60, 300, 900, 3600, 86400]  # 1min, 5min, 15min, 1hr, 24hr

def get_redis_connection():
    """Get Redis connection"""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        r.ping()
        return r
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        return None

def queue_email(to_email: str, subject: str, html_content: str, 
                text_content: Optional[str] = None, priority: int = 0) -> bool:
    """
    Queue email for sending
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
        priority: Priority (0=normal, 1=high, 2=urgent)
    
    Returns:
        True if queued successfully, False otherwise
    """
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        # Fallback: Try to send directly if Redis unavailable
        print("⚠️  Redis unavailable - attempting direct send")
        try:
            from email_api import send_email
            return send_email(to_email, subject, html_content, text_content)[0]
        except:
            return False
    
    # Create email job
    job = {
        'to_email': to_email,
        'subject': subject,
        'html_content': html_content,
        'text_content': text_content,
        'created_at': datetime.now().isoformat(),
        'retry_count': 0,
        'priority': priority
    }
    
    try:
        # Add to queue (use priority for ordering)
        redis_conn.zadd(EMAIL_QUEUE, {json.dumps(job): priority})
        print(f"✅ Email queued for {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to queue email: {e}")
        return False

def process_email_queue():
    """
    Process emails from queue
    This should be run by a background worker
    """
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        print("❌ Redis unavailable - cannot process queue")
        return
    
    try:
        # Get next email from queue (highest priority first)
        job_data = redis_conn.zrange(EMAIL_QUEUE, 0, 0, withscores=True)
        
        if not job_data:
            return  # No emails in queue
        
        job_json, priority = job_data[0]
        job = json.loads(job_json)
        
        # Move to processing queue
        redis_conn.zrem(EMAIL_QUEUE, job_json)
        redis_conn.setex(
            f"{EMAIL_PROCESSING}:{job['to_email']}:{time.time()}",
            300,  # 5 minute timeout
            job_json
        )
        
        # Try to send email
        try:
            from email_api import send_email
            success, message = send_email(
                job['to_email'],
                job['subject'],
                job['html_content'],
                job.get('text_content')
            )
            
            if success:
                print(f"✅ Email sent to {job['to_email']}")
                # Remove from processing
                redis_conn.delete(f"{EMAIL_PROCESSING}:{job['to_email']}:{time.time()}")
            else:
                # Failed - schedule retry
                schedule_retry(job, redis_conn)
        
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            schedule_retry(job, redis_conn)
    
    except Exception as e:
        print(f"❌ Queue processing error: {e}")

def schedule_retry(job: Dict, redis_conn):
    """Schedule email for retry with exponential backoff"""
    retry_count = job.get('retry_count', 0) + 1
    
    if retry_count > MAX_RETRIES:
        # Max retries exceeded - move to dead letter queue
        print(f"❌ Max retries exceeded for {job['to_email']} - moving to DLQ")
        redis_conn.lpush(EMAIL_DLQ, json.dumps(job))
        return
    
    # Calculate retry time (exponential backoff)
    backoff_seconds = RETRY_BACKOFFS[min(retry_count - 1, len(RETRY_BACKOFFS) - 1)]
    retry_time = time.time() + backoff_seconds
    
    # Update job
    job['retry_count'] = retry_count
    job['next_retry_at'] = datetime.fromtimestamp(retry_time).isoformat()
    
    # Add to retry queue (sorted by retry time)
    redis_conn.zadd(EMAIL_RETRY_QUEUE, {json.dumps(job): retry_time})
    print(f"⏳ Scheduled retry #{retry_count} for {job['to_email']} in {backoff_seconds}s")

def process_retry_queue():
    """Process emails ready for retry"""
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        return
    
    try:
        now = time.time()
        
        # Get emails ready for retry
        ready_jobs = redis_conn.zrangebyscore(EMAIL_RETRY_QUEUE, 0, now, withscores=True)
        
        for job_json, retry_time in ready_jobs:
            job = json.loads(job_json)
            
            # Move back to main queue
            redis_conn.zrem(EMAIL_RETRY_QUEUE, job_json)
            redis_conn.zadd(EMAIL_QUEUE, {job_json: job.get('priority', 0)})
            
            print(f"🔄 Retrying email to {job['to_email']}")
    
    except Exception as e:
        print(f"❌ Retry queue processing error: {e}")

def get_queue_stats() -> Dict:
    """Get queue statistics"""
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        return {
            'queue_size': 0,
            'retry_queue_size': 0,
            'dlq_size': 0,
            'redis_available': False
        }
    
    return {
        'queue_size': redis_conn.zcard(EMAIL_QUEUE),
        'retry_queue_size': redis_conn.zcard(EMAIL_RETRY_QUEUE),
        'dlq_size': redis_conn.llen(EMAIL_DLQ),
        'redis_available': True
    }

if __name__ == '__main__':
    print("=" * 80)
    print("📧 EMAIL QUEUE SYSTEM")
    print("=" * 80)
    print()
    
    redis_conn = get_redis_connection()
    
    if redis_conn:
        print("✅ Redis connected")
        stats = get_queue_stats()
        print(f"   Queue: {stats['queue_size']} emails")
        print(f"   Retry: {stats['retry_queue_size']} emails")
        print(f"   DLQ: {stats['dlq_size']} emails")
    else:
        print("❌ Redis not available")
        print("   Install: sudo apt install redis-server")
        print("   Python: pip3 install redis")
