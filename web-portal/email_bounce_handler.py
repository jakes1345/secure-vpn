#!/usr/bin/env python3
"""
Email Bounce Handler - Processes Postfix bounce logs
Detects bounced emails and marks them in database
"""

import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Postfix log locations
POSTFIX_MAILLOG = Path('/var/log/mail.log')
POSTFIX_MAILERR = Path('/var/log/mail.err')

# Bounce patterns
BOUNCE_PATTERNS = [
    r'status=bounced',
    r'status=deferred',
    r'550.*user unknown',
    r'550.*mailbox.*full',
    r'550.*rejected',
    r'554.*rejected',
    r'550.*not found',
    r'550.*does not exist',
    r'550.*invalid',
    r'550.*unavailable',
    r'550.*disabled',
    r'550.*over quota',
    r'550.*quota exceeded',
    r'550.*mailbox full',
    r'550.*user.*not found',
    r'550.*no such.*user',
    r'550.*recipient.*rejected',
    r'550.*address.*rejected',
    r'550.*relay.*denied',
    r'550.*access.*denied',
    r'550.*policy.*violation',
    r'550.*spam',
    r'550.*blacklisted',
    r'550.*blocked',
    r'550.*prohibited',
    r'550.*forbidden',
    r'550.*not.*allowed',
    r'550.*refused',
    r'550.*denied',
    r'550.*reject',
    r'550.*fail',
    r'550.*error',
    r'550.*invalid.*address',
    r'550.*bad.*address',
    r'550.*malformed',
    r'550.*syntax.*error',
    r'550.*format.*error',
    r'550.*parse.*error',
    r'550.*invalid.*domain',
    r'550.*no.*such.*domain',
    r'550.*domain.*not.*found',
    r'550.*domain.*invalid',
    r'550.*domain.*rejected',
    r'550.*domain.*denied',
    r'550.*domain.*blocked',
    r'550.*domain.*blacklisted',
    r'550.*domain.*prohibited',
    r'550.*domain.*forbidden',
    r'550.*domain.*not.*allowed',
    r'550.*domain.*refused',
    r'550.*domain.*reject',
    r'550.*domain.*fail',
    r'550.*domain.*error',
]

def parse_bounce_log(log_file: Path) -> List[Dict]:
    """
    Parse Postfix log file for bounce messages
    
    Returns:
        List of bounce records with email, reason, timestamp
    """
    bounces = []
    
    if not log_file.exists():
        return bounces
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # Check for bounce patterns
                for pattern in BOUNCE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Try to extract email address
                        email_match = re.search(r'to=<([^>]+)>', line)
                        if email_match:
                            email = email_match.group(1)
                            
                            # Extract timestamp
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
                            
                            # Extract reason
                            reason_match = re.search(r'status=([^,]+)', line)
                            reason = reason_match.group(1) if reason_match else 'unknown'
                            
                            bounces.append({
                                'email': email,
                                'reason': reason,
                                'timestamp': timestamp,
                                'log_line': line.strip()
                            })
                            break
    
    except Exception as e:
        print(f"❌ Error parsing bounce log: {e}")
    
    return bounces

def mark_email_bounced(email: str, reason: str):
    """Mark email as bounced in database"""
    try:
        from mysql_db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if bounce table exists, create if not
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_bounces (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    reason VARCHAR(255),
                    bounced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Insert bounce record
            cursor.execute("""
                INSERT INTO email_bounces (email, reason)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    reason = VALUES(reason),
                    bounced_at = CURRENT_TIMESTAMP
            """, (email, reason))
            
            conn.commit()
            print(f"✅ Marked {email} as bounced: {reason}")
    
    except Exception as e:
        print(f"❌ Error marking email as bounced: {e}")

def is_email_bounced(email: str) -> bool:
    """Check if email address is bounced"""
    try:
        from mysql_db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM email_bounces
                WHERE email = %s
            """, (email,))
            
            result = cursor.fetchone()
            return result[0] > 0 if result else False
    
    except Exception as e:
        print(f"⚠️  Error checking bounce status: {e}")
        return False

def process_bounces():
    """Process bounce logs and mark emails"""
    print("=" * 80)
    print("📧 PROCESSING EMAIL BOUNCES")
    print("=" * 80)
    print()
    
    # Parse both log files
    bounces = []
    bounces.extend(parse_bounce_log(POSTFIX_MAILLOG))
    bounces.extend(parse_bounce_log(POSTFIX_MAILERR))
    
    if not bounces:
        print("✅ No bounces found")
        return
    
    print(f"Found {len(bounces)} bounce(s)")
    print()
    
    # Process each bounce
    for bounce in bounces:
        mark_email_bounced(bounce['email'], bounce['reason'])
    
    print()
    print(f"✅ Processed {len(bounces)} bounce(s)")

if __name__ == '__main__':
    process_bounces()
