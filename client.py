import asyncio
import json
import logging
from email_validator import validate_email, EmailNotValidError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger('client')

def validate_email_address(email):
    try:
        validation = validate_email(email, check_deliverability=False)
        return True, validation.normalized
    except EmailNotValidError as e:
        return False, str(e)

async def tcp_client(sender, receiver, subject, message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    data = {
        'sender': sender,
        'receiver': receiver,
        'subject': subject,
        'message': message
    }
    message = json.dumps(data)
    
    logger.info(f'>> {message}')
    writer.write(message.encode())
    await writer.drain()

    response = await reader.read(4096)
    logger.info(f'<< {response.decode()}')

    logger.info('Closing the connection')
    writer.close()
    await writer.wait_closed()

def get_valid_email(prompt):
    while True:
        email = input(prompt)
        is_valid, result = validate_email_address(email)
        if is_valid:
            return result
        else:
            print(f"Email is invalid")

def main():
    sender = get_valid_email("sender email: ")
    receiver = get_valid_email("receiver email: ")
    
    while True:
        subject = input("subject: ").strip()
        if subject:
            break
        print("Subject cannot be empty")
    
    while True:
        message = input("message: ").strip()
        if message:
            break
        print("Message cannot be empty")
    
    asyncio.run(tcp_client(sender, receiver, subject, message))

if __name__ == "__main__":
    main()
