from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.utils.text import slugify
from django.contrib.auth.models import User
from FeedSync.models import Messages
from asgiref.sync import sync_to_async
from django.db.models import Q

class Messenger(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.other_username = self.scope['url_route']['kwargs']['other_username']

        # Generate unique room name
        room_members = sorted([self.username, self.other_username])
        sanitized_members = [slugify(member) for member in room_members]
        self.room_name = f"chat_{sanitized_members[0]}_{sanitized_members[1]}"
        self.room_group_name = self.room_name

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Fetch previous messages asynchronously
        conversation = await self.get_previous_messages(self.username, self.other_username)
        
        

        # Build the conversation list to send to the frontend
        
        convo = [
            {
                'sender': msg['sender'],
                'content': msg['content'],
                'receiver': msg['receiver'],
                'timestamp': msg['created_at'],  # Change this as needed for the correct timestamp format
            }
            for msg in conversation
        ]
    

        # Send the previous messages to the frontend
        await self.send_json({
            'type': 'conversation',
            'conversation':convo,
            'msg': 'Welcome to the chat'
        })

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        sender_username = text_data_json['username']
        receiver_username = text_data_json['other_username']

        # Get sender and receiver asynchronously
        sender = await self.get_user(sender_username)
        receiver = await self.get_user(receiver_username)

        # Save the message to the database asynchronously
        await self.save_message(sender, receiver, message_content)

        # Broadcast the message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'username': sender_username,
                'other_username': receiver_username,
            }
        )

    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send_json({
            'message': event['message'],
            'username': event['username'],
            'other_username': event['other_username']
        })

    async def disconnect(self, close_code):
        """Leave the room group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @sync_to_async
    def get_user(self, username):
        """Fetch a user by username."""
        return User.objects.get(username=username)

    @sync_to_async
    def save_message(self, sender, receiver, content):
        """Save a message to the database."""
        Messages.objects.create(sender=sender, receiver=receiver, content=content)

    @sync_to_async
    def get_previous_messages(self, username1, username2):
        """Fetch previous messages between two users."""
        user1 = User.objects.get(username=username1)
        user2 = User.objects.get(username=username2)

        messages=Messages.objects.filter(
                (Q(sender=user1) & Q(receiver=user2)) |
                (Q(sender=user2) & Q(receiver=user1))
            ).order_by('created_at')
        
        
        return [
            
            {
                'sender': msg.sender.username,
                'content': msg.content,
                'receiver': msg.receiver.username,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Format as needed
            }
            for msg in messages
        ]
            
            
        
