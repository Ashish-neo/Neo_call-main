import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Send connection established message with user ID
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'id': str(self.scope['user'].id),
            'message': 'Connected successfully'
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'call_request':
            # Forward call request to target user
            target_id = data.get('target_id')
            from_id = data.get('from_id')
            
            # Broadcast to target user (you'll need to implement user-specific messaging)
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"user_{target_id}",
                {
                    'type': 'call_request',
                    'target_id': target_id,
                    'from_id': from_id
                }
            )
            
        elif message_type == 'call_accept':
            # Handle call acceptance
            target_id = data.get('target_id')
            from_id = data.get('from_id')
            
            # Notify both users to start WebRTC
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"user_{target_id}",
                {
                    'type': 'start_webrtc',
                    'target_id': target_id,
                    'from_id': from_id
                }
            )
            await channel_layer.group_send(
                f"user_{from_id}",
                {
                    'type': 'start_webrtc',
                    'target_id': from_id,
                    'from_id': target_id
                }
            )

    async def call_request(self, event):
        # Send call request to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'call_request',
            'from_id': event['from_id'],
            'target_id': event['target_id']
        }))

    async def start_webrtc(self, event):
        # Send WebRTC start signal
        await self.send(text_data=json.dumps({
            'type': 'start_webrtc',
            'from_id': event['from_id'],
            'target_id': event['target_id']
        }))
# # call/consumers.py
# from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer
# import json

# class MyConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()

#     def disconnect(self, close_code):
#         pass

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         print(data)
#         message = data['message']
#         await self.receive(text_data=json.dumps({
#             "message":message
#         }))
        #self.send(text_data=json.dumps({"message": "Echo: " + data['message']}))

# class ConnectionConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         await self.send(text_data=json.dumps({
#             'type': 'connection_established',
#             'message': 'Connected successfully!'
#         }))

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
        
#         # Echo back the message
#         await self.send(text_data=json.dumps({
#             'type': 'echo',
#             'message': f"You said: {message}"
#         }))

#     async def disconnect(self, close_code):
#         pass

# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from asgiref.sync import sync_to_async
# from django.db.models import F
# from .models import Request_User  # Replace 'your_app' with your actual app name

# class ConnectionConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Accept the WebSocket connection
#         await self.accept()

#         # Fetch all active users
#         active_users = await sync_to_async(list)(Request_User.objects.filter(is_active=True))

#         # Send connection requests to all active users
#         for user in active_users:
#             await self.send_connection_request(user)

#     async def send_connection_request(self, user):
#         # Simulate sending a connection request
#         await self.send(text_data=json.dumps({
#             'type': 'connection_request',
#             'user_id': user.id,
#             'username': user.username,
#         }))

#     async def receive(self, text_data):
#         data = json.loads(text_data)

#         # Handle user accepting the connection
#         if data.get('type') == 'connection_accepted':
#             user_id = data.get('user_id')

#             # Update the user's is_active status to False
#             await self.update_user_status(user_id)

#     @sync_to_async
#     def update_user_status(self, user_id):
#         # Update the user's status to is_active = False
#         user = Request_User.objects.get(id=user_id)
#         user.is_active = False
#         user.save(update_fields=["is_active"])
#         print(f"User {user_id} has been marked as inactive.")

#     async def disconnect(self, close_code):
#         print("WebSocket disconnected")




# import json
# from asgiref.sync import async_to_sync
# from channels.generic.websocket import WebsocketConsumer

# class CallConsumer(WebsocketConsumer):
#     def connect(self):
#         self.accept()

#         # response to client, that we are connected.
#         self.send(text_data=json.dumps({
#             'type': 'connection',
#             'data': {
#                 'message': "Connected"
#             }
#         }))

#     def disconnect(self, close_code):
#         # Leave room group
#         async_to_sync(self.channel_layer.group_discard)(
#             self.my_name,
#             self.channel_name
#         )

#     # Receive message from client WebSocket
#     def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         # print(text_data_json)

#         eventType = text_data_json['type']

#         if eventType == 'login':
#             name = text_data_json['data']['name']
#             # we will use this as room name as well
#             self.my_name = name
#             # Join room
#             async_to_sync(self.channel_layer.group_add)(
#                 self.my_name,
#                 self.channel_name
#             )
            
#         if eventType == 'call':
#             name = text_data_json['data']['name']
#             print(self.my_name, "is calling", name);
#             # print(text_data_json)


#             # to notify the callee we sent an event to the group name
#             # and their's groun name is the name
#             async_to_sync(self.channel_layer.group_send)(
#                 name,
#                 {
#                     'type': 'call_received',
#                     'data': {
#                         'caller': self.my_name,
#                         'rtcMessage': text_data_json['data']['rtcMessage']
#                     }
#                 }
#             )

#         if eventType == 'answer_call':
#             # has received call from someone now notify the calling user
#             # we can notify to the group with the caller name
                
#             caller = text_data_json['data']['caller']
#             # print(self.my_name, "is answering", caller, "calls.")

#             async_to_sync(self.channel_layer.group_send)(
#                 caller,
#                 {
#                     'type': 'call_answered',
#                     'data': {
#                         'rtcMessage': text_data_json['data']['rtcMessage']
#                     }
#                 }
#             )

#         if eventType == 'ICEcandidate':

#             user = text_data_json['data']['user']

#             async_to_sync(self.channel_layer.group_send)(
#                 user,
#                 {
#                     'type': 'ICEcandidate',
#                     'data': {
#                         'rtcMessage': text_data_json['data']['rtcMessage']
#                     }
#                 }
#             )

#     def call_received(self, event):

#         # print(event)
#         print('Call received by ', self.my_name )
#         self.send(text_data=json.dumps({
#             'type': 'call_received',
#             'data': event['data']
#         }))


#     def call_answered(self, event):

#         # print(event)
#         print(self.my_name, "'s call answered")
#         self.send(text_data=json.dumps({
#             'type': 'call_answered',
#             'data': event['data']
#         }))

#     def ICEcandidate(self, event):
#         self.send(text_data=json.dumps({
#             'type': 'ICEcandidate',
#             'data': event['data']
#         }))
