import asyncio
import json
import logging
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response
from starlette.status import HTTP_303_SEE_OTHER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger('webclient')

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Store message in memory (for demo purposes)
message_state = {"message": None, "status": None}

async def tcp_client(sender, receiver, subject, message):
    try:
        reader, writer = await asyncio.open_connection('192.168.50.2', 8888)

        # Format data exactly like client.py
        data = {
            'sender': sender,
            'receiver': receiver,  # Single receiver
            'subject': subject,
            'message': message
        }
        message_data = json.dumps(data)
        
        logger.info(f'>> {message_data}')
        writer.write(message_data.encode())
        await writer.drain()

        response = await reader.read(4096)
        response_text = response.decode()
        logger.info(f'<< {response_text}')

        writer.close()
        await writer.wait_closed()

        # Check if response indicates success
        if "OK" == response_text:
            return True, "Email sent successfully!"
        else:
            return False, f"Server error: {response_text}"
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False, f"Connection error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    message = message_state["message"]
    status = message_state["status"]
    # Reset message after showing
    message_state["message"] = None
    message_state["status"] = None
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Client</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #6366f1;
                --primary-hover: #4f46e5;
                --bg-color: #f8fafc;
                --card-bg: #ffffff;
                --text-color: #1e293b;
                --border-color: #e2e8f0;
            }}

            body {{ 
                font-family: 'Poppins', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                min-height: 100vh;
                display: flex;
                align-items: center;
                padding: 2rem 0;
            }}

            .email-container {{
                max-width: 700px;
                margin: 0 auto;
                background-color: var(--card-bg);
                padding: 2.5rem;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
                border: 1px solid var(--border-color);
            }}

            .page-title {{
                font-weight: 600;
                color: var(--text-color);
                margin-bottom: 2rem;
                font-size: 1.75rem;
                text-align: center;
            }}

            .form-label {{
                font-weight: 500;
                color: var(--text-color);
                margin-bottom: 0.5rem;
            }}

            .form-control {{
                border: 1px solid var(--border-color);
                padding: 0.75rem 1rem;
                border-radius: 8px;
                transition: all 0.3s ease;
            }}

            .form-control:focus {{
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
                border-color: var(--primary-color);
            }}

            .btn-primary {{
                background-color: var(--primary-color);
                border: none;
                padding: 0.75rem 2rem;
                font-weight: 500;
                border-radius: 8px;
                transition: all 0.3s ease;
            }}

            .btn-primary:hover {{
                background-color: var(--primary-hover);
                transform: translateY(-1px);
            }}

            .alert {{
                border: none;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
            }}

            .alert-success {{
                background-color: #ecfdf5;
                color: #065f46;
            }}

            .alert-danger {{
                background-color: #fef2f2;
                color: #991b1b;
            }}

            .btn-close {{
                opacity: 0.5;
                transition: opacity 0.3s ease;
            }}

            .btn-close:hover {{
                opacity: 1;
            }}

            .form-floating {{
                margin-bottom: 1rem;
            }}

            .form-floating > label {{
                padding: 0.75rem 1rem;
            }}

            .form-floating > .form-control {{
                height: calc(3.5rem + 2px);
                line-height: 1.25;
            }}

            .form-floating > textarea.form-control {{
                height: auto;
                min-height: 200px;
            }}

            @media (max-width: 768px) {{
                .email-container {{
                    margin: 1rem;
                    padding: 1.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="email-container">
                <h1 class="page-title">Send Email</h1>
                
                {f'<div class="alert alert-{status if status == "success" else "danger"} alert-dismissible fade show" role="alert">{message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>' if message else ''}
                
                <form action="/send" method="post">
                    <div class="form-floating mb-3">
                        <input type="email" class="form-control" id="sender" name="sender" placeholder="name@example.com" required>
                        <label for="sender">From</label>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="email" class="form-control" id="receiver" name="receiver" placeholder="name@example.com" required>
                        <label for="receiver">To</label>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="text" class="form-control" id="subject" name="subject" placeholder="Email subject" required>
                        <label for="subject">Subject</label>
                    </div>
                    <div class="form-floating mb-4">
                        <textarea class="form-control" id="message" name="message" placeholder="Type your message here" style="height: 200px" required></textarea>
                        <label for="message">Message</label>
                    </div>
                    <div class="text-center">
                        <button type="submit" class="btn btn-primary">Send Email</button>
                    </div>
                </form>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js"></script>
    </body>
    </html>
    """

@app.post("/send")
async def send_email(
    request: Request,
    sender: str = Form(...),
    receiver: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...)
):
    # Send email via TCP
    success, message_result = await tcp_client(sender.strip(), receiver.strip(), subject.strip(), message.strip())
    message_state["message"] = message_result
    message_state["status"] = "success" if success else "danger"
    
    return Response(status_code=HTTP_303_SEE_OTHER, headers={"Location": "/"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
