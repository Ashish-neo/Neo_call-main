from django.test import TestCase

# Create your tests here.
from channels.tests import WebsocketCommunicator
from django.test import TestCase
from .consumers import ConnectionConsumer  # Replace 'your_app' with your actual app name
from .models import Request_User
from asgiref.sync import sync_to_async

class WebSocketTests(TestCase):
    async def test_websocket_connection(self):
        # Create an active user
        user = await sync_to_async(Request_User.objects.create)(username="testuser", is_active=True)

        # Instantiate the WebSocket communicator
        communicator = WebsocketCommunicator(ConnectionConsumer.as_asgi(), "/ws/connection/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a message to accept a connection
        await communicator.send_json_to({
            "type": "connection_accepted",
            "user_id": user.id,
        })

        # Receive a response
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "connection_accepted")

        # Disconnect
        await communicator.disconnect()

        # Verify the user's status was updated
        updated_user = await sync_to_async(Request_User.objects.get)(id=user.id)
        self.assertFalse(updated_user.is_active)
        