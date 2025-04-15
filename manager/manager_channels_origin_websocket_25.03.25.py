import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from channels.layers import get_channel_layer

from . import models
from calendar_app import models as rsv
import asyncio

@database_sync_to_async
def change_session_data(session_key, data):
    session = Session.objects.get(session_key=session_key)
    session_data = session.get_decoded()
    session_data.update(data)
    session.session_data = Session.objects.encode(session_data)
    session.save()

User = get_user_model()
ADMIN_USERS = { "admin" : True,}


# 달력 합치기 전 확인용...추후 삭제예정
class CheckConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None  # Initialize room_group_name

    async def fetch_messages(self, data):
        messages = models.Message.all_messages()
        messages = await sync_to_async(models.Message.all_messages)()
        content = {
            "messages" : await self.messages_to_json(messages)
        }
        await self.send_chat_messages(content)

    async def new_message(self, data):
        print("매니져 뉴메세지")
        author = data["from"]
        recipient_username = "admin"

        author = author.strip('"')
        try:
            # author_user = User.objects.get(username=author)
            # recipient_user = User.objects.get(username=recipient_username)
            author_user = await sync_to_async(User.objects.get)(username=author)
            # recipient_user = await sync_to_async(User.objects.get)(username=recipient_user)
        except User.DoesNotExist:
            users = User.objects.all()
            for user in users:
                print(user.username)
            return

        # message = models.Message.objects.create(author=author_user, recipient=recipient_user, content=data["message"], chatroom=self.room_name)
        # message = models.Message.objects.create(author=author_user, content=data["message"], chatroom=self.room_name)
        message = await sync_to_async(models.Message.objects.create)(author=author_user, content=data["message"], chatroom=self.room_name)
        content = {
            "command" : "new_message",
            # "message" : self.message_to_json(message)
            "message" : await self.message_to_json(message),
        }
        await self.send_chat_messages(content)

    async def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(await self.message_to_json(message))
        return result

    async def message_to_json(self, message):
        return {
            "author" : message.author.username,
            "content" : message.content,
            "timestamp" : message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = {
            "fetch_messages" : self.fetch_messages,
            "new_message" : self.new_message,
        }

    # commands = {
    #     "fetch_messages" : fetch_messages,
    #     "new_message" : new_message,
    # }

    async def connect(self):
        print("매니저 커넥트 실행")
        # ROOM_NAME = {}
        current_user = self.scope["user"].username

        # ROOM_NAME[current_user] = current_user
        # for admin_user in ADMIN_USERS.keys():
        #     ROOM_NAME[admin_user] = admin_user

        self.room_name = current_user
        self.room_group_name = f"chat_{self.room_name}"
        # print("매니저그륩네임",self.room_group_name)

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.accept()
        print(f"매니저컨수머 : {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("매니져 리시브 찍히나", data)
        # self.commands[data["command"]](self, data)
        key_command = data.get("command")
        rsv_id = data.get("rsv_id")

        if key_command == "new_message":
            await self.commands[key_command](data)

        elif key_command == "RSV_mark_as_read":
            await self.mark_as_read(rsv_id)

        elif key_command == "selected_date":
            print(data)
    

    async def mark_as_read(self, rsvuser_id):
        rsv_read = await sync_to_async(rsv.Reservation_user.objects.get, thread_sensitive=True)(id=rsvuser_id)
        await sync_to_async(rsv_read.rsv_check, thread_sensitive=True)()

    async def send_chat_messages(self, message):
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def notification_message(self, event):
        print("매니저노티피캐이션")
        message = event["notification_message"]
        client_message = {
            "type" : "notification",
            "content" : message
        }
        await self.send(text_data=json.dumps(client_message))



class ManagerConsumer(AsyncWebsocketConsumer):

    async def fetch_messages(self, data):
        messages = models.Message.all_messages()
        content = {
            "messages" : self.messages_to_json(messages)
        }
        await self.send_chat_messages(content)

    async def new_message(self, data):
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

        message = models.Message.objects.create(author=author_user, recipient=recipient_user, content=data["message"], chatroom=self.room_name)
        content = {
            "command" : "new_message",
            "message" : self.message_to_json(message)
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

    commands = {
        "fetch_messages" : fetch_messages,
        "new_message" : new_message,
    }

    async def connect(self):
        print("매니저 커넥트 실행")
        # ROOM_NAME = {}
        current_user = self.scope["user"].username

        # ROOM_NAME[current_user] = current_user
        # for admin_user in ADMIN_USERS.keys():
        #     ROOM_NAME[admin_user] = admin_user

        self.room_name = current_user
        self.room_group_name = f"chat_{self.room_name}"
        # print("매니저그륩네임",self.room_group_name)

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.accept()
        print(f"매니저컨수머 : {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )


    async def receive(self, text_data):
        data = json.loads(text_data)
        # print("매니져 리시브 찍히나", data)
        # self.commands[data["command"]](self, data)
        key_command = data.get("command")
        rsv_id = data.get("rsv_id")
        if key_command == "new_message":
            await self.commands[key_command](data)
        elif key_command == "RSV_mark_as_read":
            await self.mark_as_read(rsv_id)
        elif key_command == "selected_date":
            selected_date_list = data.get("select_date")  # 웹소켓에서 받아온 날짜 정보
            store_id = data.get("store_id")  # 웹소켓에서 받아온 스토어 정보
            await self.get_reservation_dates(selected_date_list, store_id)
            

    async def mark_as_read(self, rsvuser_id):
        rsv_read = await sync_to_async(rsv.Reservation_user.objects.get, thread_sensitive=True)(id=rsvuser_id)
        await sync_to_async(rsv_read.rsv_check, thread_sensitive=True)()
    


    async def get_reservation_dates(self, selected_date_list, store_id):
        selected_date = '-'.join(selected_date_list)  # 리스트를 문자열로 변환

        # 별도의 동기 함수 생성
        def fetch_reservations(selected_date):
            user = self.scope["user"]
            print("유저", user.id)
            reservations = rsv.Reservation_user.objects.filter(reservation_date=selected_date, store_id__owner_id=user.id, store_id=store_id)
            reservation_details = []

            for reservation in reservations:
                detail = {
                    'user_name': reservation.user_name,
                    'user_phone': reservation.user_phone,
                    'store_id': reservation.store_id.id, # ForeignKey 필드라서 .id를 사용하여 실제 id 값을 가져옴
                    'reservation_date': reservation.reservation_date,
                    'user_time': reservation.user_time,
                    'visitor_num': reservation.visitor_num
                }
                reservation_details.append(detail)

            return reservation_details

        try:
            # 선택된 날짜와 일치하는 예약 정보 가져오기
            async_func = sync_to_async(fetch_reservations)
            reservation_details = await async_func(selected_date)

            print("reservation_details", reservation_details)
            # return reservation_details
            
             # 결과를 클라이언트에게 전송
            await self.send(text_data=json.dumps({
                'message_type': 'reservation_details',
                'data': reservation_details
            }))

        except ObjectDoesNotExist:
            # 예약 정보가 없을 경우
            pass


    async def send_chat_messages(self, message):
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def notification_message(self, event):
        print("매니저노티피캐이션")
        message = event["notification_message"]
        client_message = {
            "type" : "notification",
            "content" : message
        }
        await self.send(text_data=json.dumps(client_message))



# class TestConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         print("테스트 커넥트 실행")

#         current_user = self.scope["user"].username

#         self.room_name = current_user
#         self.room_group_name = f"chat_{self.room_name}"

#         await self.channel_layer.group_add(
#             self.room_group_name, self.channel_name
#         )

#         await self.accept()
#         print(f"테스트 컨수머 : {self.room_group_name}")

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name, self.channel_name
#         )


#     # 아직 아무것도 안함
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']

#         # 클라이언트에 메시지 전송
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))

# checkconsumer이름만 바꿈
class TestConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None  # Initialize room_group_name

    async def fetch_messages(self, data):
        messages = models.Message.all_messages()
        messages = await sync_to_async(models.Message.all_messages)()
        content = {
            "messages" : await self.messages_to_json(messages)
        }
        await self.send_chat_messages(content)

    async def new_message(self, data):
        print("매니져 뉴메세지")
        author = data["from"]
        recipient_username = "admin"

        author = author.strip('"')
        try:
            # author_user = User.objects.get(username=author)
            # recipient_user = User.objects.get(username=recipient_username)
            author_user = await sync_to_async(User.objects.get)(username=author)
            # recipient_user = await sync_to_async(User.objects.get)(username=recipient_user)
        except User.DoesNotExist:
            users = User.objects.all()
            for user in users:
                print(user.username)
            return

        # message = models.Message.objects.create(author=author_user, recipient=recipient_user, content=data["message"], chatroom=self.room_name)
        # message = models.Message.objects.create(author=author_user, content=data["message"], chatroom=self.room_name)
        message = await sync_to_async(models.Message.objects.create)(author=author_user, content=data["message"], chatroom=self.room_name)
        content = {
            "command" : "new_message",
            # "message" : self.message_to_json(message)
            "message" : await self.message_to_json(message),
        }
        await self.send_chat_messages(content)

    async def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(await self.message_to_json(message))
        return result

    async def message_to_json(self, message):
        return {
            "author" : message.author.username,
            "content" : message.content,
            "timestamp" : message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = {
            "fetch_messages" : self.fetch_messages,
            "new_message" : self.new_message,
        }

    # commands = {
    #     "fetch_messages" : fetch_messages,
    #     "new_message" : new_message,
    # }

    async def connect(self):
        print("매니저 커넥트 실행")
        print("겟", get_channel_layer())
        # ROOM_NAME = {}
        current_user = self.scope["user"].username

        # ROOM_NAME[current_user] = current_user
        # for admin_user in ADMIN_USERS.keys():
        #     ROOM_NAME[admin_user] = admin_user

        self.room_name = current_user
        self.room_group_name = f"chat_{self.room_name}"
        # print("매니저그륩네임",self.room_group_name)

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.accept()
        print(f"매니저컨수머 : {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("매니져 리시브 찍히나", data)
        # self.commands[data["command"]](self, data)
        key_command = data.get("command")
        rsv_id = data.get("rsv_id")

        if key_command == "new_message":
            await self.commands[key_command](data)

        elif key_command == "RSV_mark_as_read":
            await self.mark_as_read(rsv_id)

        elif key_command == "selected_date":
            print(data)
    
        elif key_command == "start_end_date":
            # 시작 날짜와 종료 날짜, 버튼 값 저장
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            button_values = data.get("buttonValues")

        elif key_command == "auto_choice_value":
            # 자동 수동 설정에서의 값
            radioValue = data.get("radioValue")
            todayDate = data.get("todayDate")
            # print("자동수동1", radioValue)
            # print("자동수동2", todayDate)
            message_to_send = {
            "radioValue": radioValue,
            "todayDate": todayDate
            }
            # 25.03.20
            await self.send_to_front(message_to_send)
            # await get_channel_layer().group_send(
            # "index", {"type": "setting.message", "message": "아무말"}
            #  )

            
            
    async def mark_as_read(self, rsvuser_id):
        rsv_read = await sync_to_async(rsv.Reservation_user.objects.get, thread_sensitive=True)(id=rsvuser_id)
        await sync_to_async(rsv_read.rsv_check, thread_sensitive=True)()

    async def send_chat_messages(self, message):
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    async def send_to_front(self, message):
        print("전송할 메시지:", message)
        await self.channel_layer.group_send(
            # 인덱스 그룹에 전송(main_consumer)
            "index", {"type": "setting.message", "message": message}
        )

    # 25.03.20
    # async def setting_message(self, event):
    #     message = event["message"]
    #     await self.send(text_data=message)

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def notification_message(self, event):
        print("매니저노티피캐이션")
        message = event["notification_message"]
        client_message = {
            "type" : "notification",
            "content" : message
        }
        await self.send(text_data=json.dumps(client_message))

