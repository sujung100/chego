import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session

from . import models
import traceback

@database_sync_to_async
def change_session_data(session_key, data):
    session = Session.objects.get(session_key=session_key)
    session_data = session.get_decoded()
    session_data.update(data)
    session.session_data = Session.objects.encode(session_data)
    session.save()

User = get_user_model()
ADMIN_USERS = { "admin" : True,}

# TEST 코드
class UserConsumer(AsyncWebsocketConsumer):

    async def test_command(self, data):
        print("Test command recived:", data)


    async def connect(self):
        print("유저커넥트실행")
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # print("유져컨수머룸네임", self.room_name)
        self.room_group_name = f"chat_{self.room_name}"
        # print("유저그륩네임", self.room_group_name)

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()
        # self.send(json.dumps({"room_name": self.room_group_name}))
        print(f"유저컨수머 : {self.room_group_name}")


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        print("뭐가 찍히나", data)
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type" : "notification.message",
                "notification_message" : text_data
            }
        )
    
    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def notification_message(self, event):
        if self.should_handle_message():
            message = event["notification_message"]
            await self.send(text_data=message)
        else:
            print("노티피 엘스")
    
    def should_handle_message(self):
        class_names = ["ManagerConsumer"]
        self_class = self.__class__
        return any(self_class == globals().get(class_name) for class_name in class_names)