import asyncio
import nats
from flask import Flask, render_template, request
import threading
import json
import nats.aio
import nats.aio.msg


async def connect():
    # Config variables
    port_num = 8001
    client_name = f'client-{port_num}'

    # Callbacks
    async def error_cb(e):
        print('There was an error. Connection failed.')
        exit(-1)
    
    # Recieved message handler
    messages = []

    async def handler(msg:nats.aio.msg.Msg):
        print(f'Received a message on {msg.subject} {msg.reply} {msg.headers}: {msg.data}')
        messages.append({
            f'subject': f'{msg.subject}', 
            f'data': f'{msg.data.decode()}'
            })
        if msg.reply != '':
            await msg.respond(b'OK')

    # Message sender
    async def publish_message(message_string:str):
        message = message_string.encode('utf-8')
        subject = f'chat.{client_name}'
        await nc.publish(f'chat.{client_name}', message)
        print(f'Sent a message on \'{subject}\': {message}')


    # Connect to NATS
    nc = await nats.connect(
        name=client_name,
        error_cb=error_cb
        )
    
    print(f'Connected successfully! Client id: {nc.client_id}, Server: {nc.connected_url.netloc}')

    # Subscribe for the 'chat' subject
    await nc.subscribe('chat.*', cb=handler)

    # Website server
    def serve():
        app = Flask(__name__)

        # Default renderer
        @app.route('/', methods=['GET'])
        async def index():
            return render_template('chat.html', client_name=client_name)

        # Fetch messages
        @app.route('/fetch_messages', methods=['GET'])
        def get_messages():
            messages.append(client_name)
            fetched_messages = json.dumps(messages)
            messages.clear()

            return fetched_messages
        
        # Send message
        @app.route('/send_message', methods=['POST'])
        async def send_message():
            message = json.loads(request.get_data())['message']
            await publish_message(message)

            return 'Message sent successfully.'

        # Start serving the webapp
        app.run(debug=False, port=port_num, use_reloader=False)

    # Serve website on a different thread
    flask_thread = threading.Thread(target=serve)
    flask_thread.start()

    # Listen infinitelly to messages
    while True:
        await asyncio.sleep(0)

if __name__ == '__main__':
    # Start the process
    asyncio.run(connect())
