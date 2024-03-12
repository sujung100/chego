import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session
from django.db.models import Q

from . import models
import traceback

# @database_sync_to_async
# def change_session_data(session_key, data):
#     session = Session.objects.get(session_key=session_key)
#     session_data = session.get_decoded()
#     session_data.update(data)
#     session.session_data = Session.objects.encode(session_data)
#     session.save()

# User = get_user_model()
# ADMIN_USERS = { "admin" : True,}

# # TEST 코드
# class UserConsumer(AsyncWebsocketConsumer):

#     async def test_command(self, data):
#         print("Test command recived:", data)


#     async def connect(self):
#         print("유저커넥트실행")
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         # print("유져컨수머룸네임", self.room_name)
#         self.room_group_name = f"chat_{self.room_name}"
#         # print("유저그륩네임", self.room_group_name)

#         await self.channel_layer.group_add(
#             self.room_group_name, self.channel_name
#         )
#         await self.accept()
#         # self.send(json.dumps({"room_name": self.room_group_name}))
#         print(f"유저컨수머 : {self.room_group_name}")


#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name, self.channel_name
#         )

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         print("뭐가 찍히나", data)
#         await self.channel_layer.group_send(
#             self.room_group_name, {
#                 "type" : "notification.message",
#                 "notification_message" : text_data
#             }
#         )
    
#     async def chat_message(self, event):
#         message = event["message"]
#         await self.send(text_data=json.dumps(message))

#     async def notification_message(self, event):
#         if self.should_handle_message():
#             message = event["notification_message"]
#             await self.send(text_data=message)
#         else:
#             print("노티피 엘스")
    
#     def should_handle_message(self):
#         class_names = ["ManagerConsumer"]
#         self_class = self.__class__
#         return any(self_class == globals().get(class_name) for class_name in class_names)

# 이거 뭔지모름..필수인가?
# @database_sync_to_async
# def change_session_data(session_key, data):
#     session = Session.objects.get(session_key=session_key)
#     session_data = session.get_decoded()
#     session_data.update(data)
#     session.session_data = Session.objects.encode(session_data)
#     session.save()

# User = get_user_model()
# ADMIN_USERS = { "admin" : True,}

class CheckingRsvConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        storeId = text_data_json['storeId']
        reservationTime = text_data_json['reservationTime']

        # 예약 확인 로직
        dates_info = await self.check_reservation(storeId, reservationTime)

        # 클라이언트에게 응답 송신
        await self.send(text_data=json.dumps({
            'exists': dates_info
        }))

    async def check_reservation(self, storeId, reservationTime):
        # 예약 확인 로직 구현 (동기 ORM 호출을 비동기로 처리하기 위해 sync_to_async 사용)
        from asgiref.sync import sync_to_async
        dates_info = await sync_to_async(models.Reservation_user.objects.filter)(
            Q(store_id=storeId) & Q(user_time=reservationTime)
        ).exists()
        return dates_info