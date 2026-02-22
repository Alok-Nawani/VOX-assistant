import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import logging

class EmailManager:
    def __init__(self):
        """Initialize email manager with credentials from environment"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        if not all([self.email_address, self.email_password]):
            logging.warning("Email credentials not found in environment variables. Legacy Email skill will be limited.")
            
    async def send_email(self, to: str, subject: str, body: str, user_id: int = 1) -> bool:
        """Send an email using Gmail API, macOS Mail, or SMTP fallback"""
        
        # Priority 1: Gmail API (Multi-user friendly)
        try:
            from ..tools.google_calendar import GoogleAuthManager
            from googleapiclient.discovery import build
            import base64
            
            auth_manager = GoogleAuthManager()
            creds = await auth_manager.get_credentials(user_id)
            
            if creds:
                logging.info(f"Gmail API attempting transmission to: {to}")
                gmail_service = build('gmail', 'v1', credentials=creds)
                
                message = MIMEMultipart()
                message['To'] = to
                message['Subject'] = subject
                message.attach(MIMEText(body, 'plain'))
                
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                gmail_service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
                
                logging.info(f"Gmail API transmission SUCCESS for user {user_id}")
                return True
        except Exception as e:
            logging.warning(f"Gmail API dispatch failed for user {user_id}: {e}")

        # Priority 2: macOS Native Mail (Context-aware fallback)
        if os.name == 'posix':
            import subprocess
            safe_to = to.replace('"', '\\"')
            safe_subject = subject.replace('"', '\\"')
            safe_body = body.replace('"', '\\"')
            
            applescript = f'''
            tell application "Mail"
                set msg to make new outgoing message with properties {{subject: "{safe_subject}", content: "{safe_body}", visible: false}}
                tell msg
                    make new to recipient with properties {{address: "{safe_to}"}}
                    send
                end tell
            end tell
            '''
            try:
                subprocess.run(['osascript', '-e', applescript], check=True)
                logging.info(f"Native macOS Mail transmission dispatched for user {user_id}")
                return True
            except Exception as e:
                logging.error(f"Native mail dispatch failed for user {user_id}: {e}")

        # Priority 3: SMTP Fallback (Legacy)
        try:
            if not all([self.email_address, self.email_password]): return False
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            return True
        except Exception as e:
            logging.error(f"Critical Transmission Failure: {e}")
            return False

    async def read_emails(self, folder: str = "INBOX", limit: int = 5, user_id: int = 1) -> List[Dict]:
        """Read recent emails using Gmail API or IMAP"""
        try:
            # Try Gmail API first
            from ..tools.google_calendar import GoogleAuthManager
            from googleapiclient.discovery import build
            
            auth_manager = GoogleAuthManager()
            creds = await auth_manager.get_credentials(user_id)
            
            if creds:
                service = build('gmail', 'v1', credentials=creds)
                results = service.users().messages().list(userId='me', labelIds=[folder.upper()], maxResults=limit).execute()
                messages = results.get('messages', [])
                
                email_data = []
                for msg in messages:
                    m = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = m['payload']['headers']
                    subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                    sender = next(h['value'] for h in headers if h['name'] == 'From')
                    snippet = m['snippet']
                    email_data.append({
                        "subject": subject,
                        "from": sender,
                        "date": "Recently",
                        "content": snippet
                    })
                return email_data
        except Exception as e:
            logging.warning(f"Gmail API read failed for user {user_id}: {e}")
            
        # Original IMAP fallback
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select(folder)
            _, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            start_idx = max(0, len(email_ids) - limit)
            recent_emails = []
            for i in range(start_idx, len(email_ids)):
                _, msg_data = mail.fetch(email_ids[i], "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            break
                else:
                    content = msg.get_payload(decode=True).decode()
                recent_emails.append({
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "date": msg["date"],
                    "content": content[:200]
                })
            mail.logout()
            return recent_emails
        except Exception as e:
            logging.error(f"Legacy IMAP read failed: {e}")
            return []

    async def search_emails(self, query: str, folder: str = "INBOX", user_id: int = 1) -> List[Dict]:
        """Search emails using Gmail API or IMAP"""
        # (Simplified for now, similar to read_emails)
        return await self.read_emails(folder, 5, user_id)
