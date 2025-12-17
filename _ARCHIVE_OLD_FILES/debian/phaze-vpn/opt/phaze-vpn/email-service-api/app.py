#!/usr/bin/env python3
"""
Email Service API
Core email sending, receiving, and management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database connection
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='mailuser',
        password='mailpass',
        database='mailserver'
    )

# Email configuration
# Use port 25 for localhost (no auth needed - Postfix allows mynetworks)
SMTP_HOST = 'localhost'
SMTP_PORT = 25  # Port 25 for local Postfix (no authentication required)
IMAP_HOST = 'localhost'
IMAP_PORT = 993

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v1/email/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'PhazeVPN Email Service',
        'features': ['send', 'receive', 'list', 'search']
    })

@app.route('/api/v1/email/send', methods=['POST'])
@require_auth
def send_email():
    """Send email via SMTP"""
    data = request.json
    from_email = data.get('from')
    to_email = data.get('to')
    subject = data.get('subject', '')
    body = data.get('body', '')
    html_body = data.get('html_body')
    password = data.get('password')
    
    if not all([from_email, to_email, password]):
        return jsonify({'error': 'from, to, and password required'}), 400
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add List-Unsubscribe header for better deliverability
        unsubscribe_url = f'https://phazevpn.com/unsubscribe?email={to_email}'
        unsubscribe_mailto = f'mailto:unsubscribe@phazevpn.com?subject=Unsubscribe&body=Please unsubscribe {to_email}'
        msg['List-Unsubscribe'] = f'<{unsubscribe_url}>, <{unsubscribe_mailto}>'
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        # Add text and HTML parts
        if html_body:
            part1 = MIMEText(body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Send via SMTP
        # For localhost, always use port 25 (no auth needed - Postfix allows mynetworks)
        if SMTP_HOST == 'localhost' or SMTP_HOST == '127.0.0.1':
            # Use port 25 directly - no authentication needed for localhost
            server = smtplib.SMTP('localhost', 25, timeout=10)
            server.send_message(msg)
            server.quit()
        else:
            # Remote SMTP server - use port 587 with auth
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            try:
                server.starttls()
            except:
                pass  # Continue without TLS if not available
            if password:
                server.login(from_email, password)
            server.send_message(msg)
            server.quit()
        
        return jsonify({
            'message': 'Email sent',
            'from': from_email,
            'to': to_email,
            'subject': subject
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/email/inbox', methods=['GET'])
@require_auth
def get_inbox():
    """Get inbox emails"""
    user_email = request.args.get('user')
    password = request.args.get('password')
    limit = int(request.args.get('limit', 50))
    
    if not user_email or not password:
        return jsonify({'error': 'user and password required'}), 400
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(user_email, password)
        mail.select('INBOX')
        
        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        
        # Get recent emails
        emails = []
        for email_id in email_ids[-limit:]:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Decode headers
            subject = decode_header(email_message['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            from_addr = email_message['From']
            date = email_message['Date']
            
            # Get body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            emails.append({
                'id': email_id.decode(),
                'subject': subject,
                'from': from_addr,
                'date': date,
                'body': body[:500]  # Preview
            })
        
        mail.close()
        mail.logout()
        
        return jsonify({
            'emails': emails,
            'count': len(emails)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/email/read/<email_id>', methods=['GET'])
@require_auth
def read_email(email_id):
    """Read specific email"""
    user_email = request.args.get('user')
    password = request.args.get('password')
    
    if not user_email or not password:
        return jsonify({'error': 'user and password required'}), 400
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(user_email, password)
        mail.select('INBOX')
        
        status, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Decode headers
        subject = decode_header(email_message['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        
        from_addr = email_message['From']
        to_addr = email_message['To']
        date = email_message['Date']
        
        # Get body
        body = ""
        html_body = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode()
                elif part.get('Content-Disposition'):
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
        else:
            body = email_message.get_payload(decode=True).decode()
        
        mail.close()
        mail.logout()
        
        return jsonify({
            'id': email_id,
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body': body,
            'html_body': html_body,
            'attachments': attachments
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/email/search', methods=['POST'])
@require_auth
def search_emails():
    """Search emails"""
    data = request.json
    user_email = data.get('user')
    password = data.get('password')
    query = data.get('query', '')
    
    if not user_email or not password:
        return jsonify({'error': 'user and password required'}), 400
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(user_email, password)
        mail.select('INBOX')
        
        # Search
        status, messages = mail.search(None, f'(SUBJECT "{query}" BODY "{query}")')
        email_ids = messages[0].split()
        
        emails = []
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            subject = decode_header(email_message['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            emails.append({
                'id': email_id.decode(),
                'subject': subject,
                'from': email_message['From'],
                'date': email_message['Date']
            })
        
        mail.close()
        mail.logout()
        
        return jsonify({
            'results': emails,
            'count': len(emails),
            'query': query
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/email/folders', methods=['GET'])
@require_auth
def list_folders():
    """List email folders"""
    user_email = request.args.get('user')
    password = request.args.get('password')
    
    if not user_email or not password:
        return jsonify({'error': 'user and password required'}), 400
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(user_email, password)
        
        status, folders = mail.list()
        
        folder_list = []
        for folder in folders:
            folder_name = folder.decode().split('"')[-2]
            folder_list.append(folder_name)
        
        mail.logout()
        
        return jsonify({'folders': folder_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
