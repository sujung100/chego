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
connected_count = 0
# TEST 코드
class AdminChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None  # Initialize room_group_name

    async def fetch_messages(self,data):
        messages = await sync_to_async(models.Message.all_messages)()
        content = {
            "messages" : await self.messages_to_json(messages)
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
            "is_read" : latestMessage["recent_is_read"],
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
                "message" : await self.message_to_json(message),
                "lates_message" : latestMessage,
            }
        await self.send_chat_messages(content)
        


    async def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(await self.message_to_json(message))
        return result

    async def message_to_json(self, message):
        unread_count = await sync_to_async(message.unread_messages)(self.room_name)
        return {
            "id" : message.id,
            "author" : message.author.username,
            "content" : message.content,
            "timestamp" : message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "unread_messages" : message.is_read,
            "chatroom" : message.chatroom,
            "unread_count" : unread_count,
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
            # "real_time_new_message" : self.new_message,
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
        global connected_count
        connected_count += 1
        await self.accept()
        print(f'Current connections: {connected_count}')



    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.room_group_name is not None:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            global connected_count
            connected_count -= 1
            print(f'Current connections: {connected_count}')
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

        key_command = data.get("command")
        key_message_id = data.get("message_id")

        # if key_command == ""

        if key_command == "mark_as_read":
            # if key_message_id is not None:
            if key_message_id :
                await self.mark_as_read(key_message_id)
        
        # await self.send(text_data=json.dumps({
        #     "message" : "읽었다.",
        # }))
        elif key_command == "new_message":
            # if key_command in self.commands:
            await self.commands[key_command](data)
            # self.send(text_data=json.dumps({
            #     "message" : "메세지 왔다.",
            # }))
            # else:
            #     print(f"Unknown command: {key_command}")
        
        elif key_command == "real_time_new_message":
            await self.mark_as_read(key_message_id)


        else:
            print(f"Unknown command : {key_command}")

    async def mark_as_read(self, message_id):
        message = await sync_to_async(models.Message.objects.get, thread_sensitive=True)(id=message_id)
        await sync_to_async(message.read_message, thread_sensitive=True)()
        

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