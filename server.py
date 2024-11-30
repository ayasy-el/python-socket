import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message

class CustomSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        print('Message from:', envelope.mail_from)
        print('Message to:', envelope.rcpt_tos)
        print('Message content:')
        print(envelope.content.decode('utf-8', errors='replace'))
        print('-' * 50)
        return '250 Message accepted for delivery'

async def run_server():
    handler = CustomSMTPHandler()
    controller = Controller(handler, hostname='127.0.0.1', port=1025)
    controller.start()
    print("SMTP server running on 127.0.0.1:1025. Press Ctrl+C to stop.\n")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server.")
        controller.stop()

if __name__ == "__main__":
    asyncio.run(run_server())
