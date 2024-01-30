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
ALLOWED_USERS = {"user1", "user2", "user3"}
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
        author = author.strip('"')
        author_user = User.objects.filter(username = author)[0]
        # try:
        #     author_user = User.objects.get(username=author)
        # except User.DoesNotExist:
        #     print(f"No user with username {author}")
        #     print(f"Actual value of author: {author}")
        #     users = User.objects.all()
        #     for user in users:
        #         print(user.username)
        #     return


        message = models.Message.objects.create(author=author_user, content=data["message"], chatroom=author)
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
            # "author" : models.Message.author.username,
            # "content" : models.Message.content,
            # "timestamp" : str(models.Message.timestamp),
            "author" : message.author.username,
            "content" : message.content,
            "timestamp" : message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    commands = {
        "fetch_messages" : fetch_messages,
        "new_message" : new_message,
    }

    
    def connect(self):
        print("셀프유저", self.scope["user"])
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    # 기본 connect()
    # def connect(self):
    #     print(self.scope["url_route"])
    #     self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
    #     self.room_group_name = f"chat_{self.room_name}"

    #     # Join room group
    #     async_to_sync(self.channel_layer.group_add)(
    #         self.room_group_name, self.channel_name
    #     )

    #     self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        # print("테스트 리시브",data)
        # print("이건 뭐지",self.commands[data["command"]](self, data))
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