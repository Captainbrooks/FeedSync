from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.utils.text import slugify




def getUser(request):
    user=request.user
    return user



class Messenger(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        self.username=self.scope['url_route']['kwargs']['username']
        self.other_username=self.scope['url_route']['kwargs']['other_username']
        
        
        room_members = sorted([self.username, self.other_username])
        sanitized_members = [slugify(member) for member in room_members]
        
        self.room_name = f"chat_{sanitized_members[0]}_{sanitized_members[1]}"
        self.room_group_name = self.room_name
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send_json({'msg':'Welcome to the chat'})
        
        
        
    async def receive(self,text_data):
        print("Someone is sending server the message")
        text_data_json=json.loads(text_data)
        message=text_data_json['message']
        sender=text_data_json['username']
        receiver=text_data_json['other_username']
        
        print(f"Message: {message}")
        print(f"Sender:{sender}")
        print(f" Receiver {receiver}")
        pass
    
    
    
    
    
    
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        
        
    
        
        
        
        
        
        