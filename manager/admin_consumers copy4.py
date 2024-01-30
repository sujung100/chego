import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from django.db.models import Max

from . import models

User = get_user_model()
ADMIN_USERS = { "admin" : True,}
# TEST 코드
class AdminChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None  # Initialize room_group_name

    async def fetch_messages(self,data):
        messages = await sync_to_async(models.Message.all_messages)()
        content = {
            "messages" : self.messages_to_json(messages)
        }
        await self.send_chat_messages(content)


    async def fetch_latest_message(self, chatroom_name):
        get_latest_message = sync_to_async(
            lambda: models.Message.latest_messages().filter(chatroom=chatroom_name).first()
        )
        latestMessage = await get_latest_message()

        message_json = {
            # "author" : latestMessage['author'],
            "content" : latestMessage["recent_content"],
            "timestamp" : latestMessage["recent_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        }

        return message_json


    
    async def new_message(self,data):
        author = data["from"]

        author = author.strip('"')
        try:
            author_user = await sync_to_async(User.objects.get)(username=author)
        except User.DoesNotExist:
            users = User.objects.all()
            for user in users:
                print(user.username)
            return


        message = await sync_to_async(models.Message.objects.create)(author=author_user, content=data["message"], chatroom=self.room_name)

        latestMessage = await self.fetch_latest_message(self.room_name)
        content = {
                "command" : "new_message",
                "message" : self.message_to_json(message),
                "lates_message" : latestMessage,
            }
        await self.send_chat_messages(content)
        


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
        
    async def test_command(self, data):
        print("Test command recived:", data)

    async def mark_as_read(self, data):
        print("컨수머 마크애즈리드", data)

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = {
            "fetch_messages" : self.fetch_messages,
            "new_message" : self.new_message,
            "test" : self.test_command,
            "message_id" : self.mark_as_read,
        }
    # commands = {
    #     "fetch_messages" : fetch_messages,
    #     "new_message" : new_message,
    #     "test" : test_command,
    #     "message_id" : mark_as_read,
    # }




    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()



    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.room_group_name is not None:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        else:
            print("디스커넥트에서 못찾음.")
        # # Leave room group
        # await self.channel_layer.group_discard(
        #     self.room_group_name, self.channel_name
        # )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        print("리시브 데이터임", data)

        data_command = data.get("command")

        if data_command == "mark_as_read":
            message_id = data.get("message_id")
            if message_id is not None:
                message = await sync_to_async(models.Message.objects.get, thread_sensitive=True)(id=message_id)
                await sync_to_async(message.read_message, thread_sensitive=True)()
        
        # await self.send(text_data=json.dumps({
        #     "message" : "읽었다.",
        # }))
        elif data_command == "new_message":
            command = data.get("command")
            if command in self.commands:
                await self.commands[command](data)
            else:
                print(f"Unknown command: {command}")

        else:
            print(f"Unknown command : {data_command}")
        # await self.commands[data["command"]](self, data)


        # Send notification to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'message': data["message"],
        #         'notification': 'New message!'
        #     }
        # )

    async def send_chat_messages(self, message):

        if hasattr(self, 'room_group_name'):
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat.message", "message": message}
            )
        else:
            # Handle error: 'room_group_name' is not defined
            print("'room_group_name' is not defined")
        # # Send message to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name, {"type": "chat.message", "message": message}
        # )

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        # print("챗메세지가 지금은 뭐냐", message)
        # notification = event["notification"]
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))

        # await self.send(text_data=json.dumps({
        #     "message" : message,
        #     "notification" : notification,
        # }))