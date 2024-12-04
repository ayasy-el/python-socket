import asyncio
import smtplib
import json
import logging
from email.mime.text import MIMEText

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger('forwarder')

async def handle_client(reader, writer):
    data = await reader.read(4096)
    message = data.decode()
    logger.info(f">> {writer.get_extra_info('peername')}: {message}")

    try:
        parsed_data = json.loads(message)
        sender = parsed_data['sender']
        receiver = parsed_data['receiver']
        subject = parsed_data['subject']
        message_content = parsed_data['message']

        try:
            # Create MIMEText message
            msg = MIMEText(message_content)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = receiver

            with smtplib.SMTP('192.168.50.3', 25) as smtp:
                smtp.send_message(msg)
                logger.info(f"Email: {sender} -> {receiver}, Subject: {subject}")
                writer.write(b"OK")
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            writer.write(b"FAIL")
    except json.JSONDecodeError:
        logger.error("Invalid message format")
        writer.write(b"INVALID FORMAT")
    except KeyError as e:
        logger.error(f"Missing field: {str(e)}")
        writer.write(b"MISSING FIELD")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        writer.write(b"ERROR")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())