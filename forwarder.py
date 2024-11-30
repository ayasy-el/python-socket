import asyncio
import smtplib
import json

async def handle_client(reader, writer):
    data = await reader.read(100)
    message = data.decode()

    try:
        parsed_data = json.loads(message)
        sender = parsed_data['sender']
        receiver = parsed_data['receiver']
        message = parsed_data['message']

        addr = writer.get_extra_info('peername')
        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        try:
            with smtplib.SMTP('127.0.0.1', 1025) as server:
                server.sendmail(sender, receiver, message)
        except Exception as e:
            print(f"Error sending email: {e}")

    except json.JSONDecodeError:
        print("Invalid JSON received")

    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())