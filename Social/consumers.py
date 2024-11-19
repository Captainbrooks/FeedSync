from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.utils.text import slugify
from django.contrib.auth.models import User
from FeedSync.models import Messages,Notification,Profile
from asgiref.sync import sync_to_async
from django.db.models import Q
import base64
from django.utils import timezone








def image_to_base64(image_path):
    return base64.b64encode(image_path.read()).decode('utf-8')


# To convert the base64 string into the actual image so that we can display the real image in the UI

def base64_to_image(base64_string):
    return f"data:image/png;base64,{base64_string}"

class Messenger(AsyncJsonWebsocketConsumer):
    
    @sync_to_async
    def get_unread_message_count(self, sender, receiver):
        return Messages.objects.filter(
            sender=sender,
            receiver=receiver,
            is_read=False
        ).count()

    @sync_to_async
    def mark_messages_as_read(self, sender, receiver):
        """Mark messages from sender to receiver as read."""
        Messages.objects.filter(sender=receiver, receiver=sender, is_read=False).update(is_read=True)
        
        

    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.other_username = self.scope['url_route']['kwargs']['other_username']

        room_members = sorted([self.username, self.other_username])
        sanitized_members = [slugify(member) for member in room_members]  #slugify helps to create dash instead of any spaces for eg (Milton Gaire) => (Milton-Gaire)
        self.room_name = f"chat_{sanitized_members[0]}_{sanitized_members[1]}"
        self.room_group_name = self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        conversation = await self.get_previous_messages(self.username, self.other_username)

        # Mark messages as read
        sender = await self.get_user(self.username)
        receiver = await self.get_user(self.other_username)
        await self.mark_messages_as_read(sender, receiver)  # Mark messages as read

        await self.send_json({
            'type': 'conversation',
            'conversation': conversation,
            'msg': 'Welcome to the chat'
        })


# activates when we send message through web sockets from frontend..
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        
        message_content = text_data_json['message']
        sender_username = text_data_json['username']
        receiver_username = text_data_json['other_username']

        sender = await self.get_user(sender_username)
        receiver = await self.get_user(receiver_username)

        await self.save_message(sender, receiver, message_content)

        unread_count = await self.get_unread_message_count(sender, receiver)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'username': sender_username,
                'other_username': receiver_username,
                'created_at':timezone.now().isoformat()
            }
        )
        
        

        profile_picture=await self.get_user_profile_picture(sender)
        

        await self.channel_layer.group_send(
            f"user_{receiver.id}_notifications",
            {
                'type': 'send_notification',
                'notification': f"{sender.username} sent you a message.",
                "profile_picture":profile_picture,
                'unread_count': unread_count,
                'sender': sender.username,
                'receiver':receiver.username
            }
        )
        
        notification=f"{sender} has sent you a message"
        
        await self.save_notification(sender,receiver,notification,profile_picture)
        
        

    async def chat_message(self, event):
        await self.send_json({
            'message': event['message'],
            'username': event['username'],
            'other_username': event['other_username']
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        
        
    @sync_to_async
    def save_notification(self,sender,receiver,notification,profile_picture,):
        message=f"{sender} sent you a message"
        return Notification.objects.create(sender=sender,receiver=receiver,notification=message,profile_picture=profile_picture)

    @sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)
    
    
    @sync_to_async
    def get_user_profile_picture(self, username):
        profile = Profile.objects.filter(user=username).first()
        profile_picture = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
        
        return profile_picture

    @sync_to_async
    def save_message(self, sender, receiver, content):
        Messages.objects.create(sender=sender, receiver=receiver, content=content)

    @sync_to_async
    def get_previous_messages(self, username1, username2):
        user1 = User.objects.get(username=username1)
        user2 = User.objects.get(username=username2)

        messages = Messages.objects.filter(
            (Q(sender=user1) & Q(receiver=user2)) |
            (Q(sender=user2) & Q(receiver=user1))
        ).order_by('created_at')

        defaultProfileImage = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"

        return [
            {
                'sender': msg.sender.username,
                'content': msg.content,
                'receiver': msg.receiver.username,
                'defaultpp': defaultProfileImage,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]


        
        
       
        
        







class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_group_name = f"user_{self.user.id}_notifications"
        
        

        if self.user.is_authenticated:
            # Join the notification group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave the notification group
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)


    async def send_notification(self, event):
        notification = event["notification"]
        profile_picture=event.get("profile_picture","")
        unread_count = event.get("unread_count", 0)
        sender = event.get("sender", "")
        receiver=event.get('receiver',"")
        
        
        
        await self.send(text_data=json.dumps({
            "notification": notification,
            "unread_count": unread_count,
            "profile_picture":profile_picture,
            "sender": sender,
            'receiver':receiver
        }))
        
        
        


            
        
