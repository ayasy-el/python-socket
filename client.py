import asyncio
import json

async def tcp_client(sender, receiver, message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    data = {
        'sender': sender,
        'receiver': receiver,
        'message': message
    }
    message = json.dumps(data)
    
    print(f'Sending: {message}')
    writer.write(message.encode())
    await writer.drain()

    response = await reader.read(100)
    print(f'Received: {response.decode()}')

    print('Closing the connection')
    writer.close()
    await writer.wait_closed()

def main():
    print("sender: ",end="")
    sender = input()
    print("receiver: ",end="")
    receiver = input()
    print("message: ",end="")
    message = input()
    asyncio.run(tcp_client(sender, receiver, message))

if __name__ == "__main__":
    main()
