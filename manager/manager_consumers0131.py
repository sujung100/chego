import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session

from . import models

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
class ChatConsumer(WebsocketConsumer):

    def fetch_messages(self,data):
        messages = models.Message.all_messages()
        content = {
            "messages" : self.messages_to_json(messages)
        }
        self.send_chat_messages(content)

    def new_message(self,data):
        author = data["from"]
        recipient_username = "admin"

        author = author.strip('"')
        try:
            author_user = User.objects.get(username=author)
            recipient_user = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            users = User.objects.all()
            for user in users:
                print(user.username)
            return

        # if author_user.username not in ALLOWED_USERS and recipient_user.username not in ALLOWED_USERS:
        #     return

        message = models.Message.objects.create(author=author_user, recipient=recipient_user ,content=data["message"], chatroom=self.room_name)
        content = {
                "command" : "new_message",
                "message" : self.message_to_json(message)
            }
        return self.send_chat_messages(content)
        

        

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
     
            "author" : message.author.username,
            "content" : message.content,
            "timestamp" : message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    commands = {
        "fetch_messages" : fetch_messages,
        "new_message" : new_message,
    }


    def connect(self):
        ROOM_NAME = {}
        current_user = self.scope["user"].username
        
        ROOM_NAME[current_user] = current_user
        for admin_user in ADMIN_USERS.keys():
            ROOM_NAME[admin_user] = admin_user

        
        self.room_name = ".".join(ROOM_NAME.values())
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()
        # self.send(json.dumps({"room_name": self.room_group_name}))


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        print("뭐가 찍히나", data)
        self.commands[data["command"]](self, data)

    def send_chat_messages(self, message):

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))