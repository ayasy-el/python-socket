import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import logging
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
import uvicorn
from datetime import datetime
from email import message_from_bytes
import html
from typing import List, Dict
import threading
from fastapi.responses import StreamingResponse
import json
import sqlite3
import aiosqlite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger('server')

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Database setup
def init_db():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS emails
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         subject TEXT,
         from_address TEXT,
         to_address TEXT,
         date TEXT,
         content TEXT)
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

email_update_event = asyncio.Event()

class CustomSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        email_content = envelope.content
        email_msg = message_from_bytes(email_content)
        
        # Extract email details
        subject = email_msg.get('subject', 'No Subject')
        from_address = envelope.mail_from
        to_address = ', '.join(envelope.rcpt_tos)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get email body
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    content = part.get_payload(decode=True).decode()
                    break
        else:
            content = email_msg.get_payload(decode=True).decode()
        
        # Store email in SQLite
        async with aiosqlite.connect('emails.db') as db:
            await db.execute(
                'INSERT INTO emails (subject, from_address, to_address, date, content) VALUES (?, ?, ?, ?, ?)',
                (subject, from_address, to_address, date, content)
            )
            await db.commit()
        
        # Notify clients about new email
        email_update_event.set()
        email_update_event.clear()
        logger.info(f'Received email from {from_address} with subject: {subject}')
        return '250 Message accepted for delivery'

async def email_event_generator():
    while True:
        await email_update_event.wait()
        yield 'data: update\n\n'

@app.get("/")
async def home(request: Request):
    # Fetch emails from database
    async with aiosqlite.connect('emails.db') as db:
        async with db.execute('SELECT * FROM emails ORDER BY date DESC') as cursor:
            emails = await cursor.fetchall()
            email_list = [
                {
                    'subject': email[1],
                    'from_address': email[2],
                    'to_address': email[3],
                    'date': email[4],
                    'content': email[5]
                }
                for email in emails
            ]
    
    return templates.TemplateResponse(
        "emails.html",
        {"request": request, "emails": email_list}
    )

@app.get('/stream')
async def stream_emails():
    return StreamingResponse(
        email_event_generator(),
        media_type='text/event-stream'
    )

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def run_smtp():
    handler = CustomSMTPHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=25, ready_timeout=60.0)
    controller.start()
    logger.info("SMTP Server started on 0.0.0.0:25")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down SMTP server.")
        controller.stop()

if __name__ == "__main__":
    # Start FastAPI in a separate thread
    web_thread = threading.Thread(target=run_fastapi)
    web_thread.daemon = True
    web_thread.start()
    
    # Run SMTP server in the main thread
    logger.info("Starting both SMTP and Web servers...")
    asyncio.run(run_smtp())
