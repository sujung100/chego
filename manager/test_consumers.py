
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer




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
