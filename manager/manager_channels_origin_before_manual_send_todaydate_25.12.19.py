import json

from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db import transaction


from . import models
from calendar_app import models as rsv
import asyncio

class KnownError(Exception):
    def __init__(self, code, **meta):
        super().__init__(code)
        self.code = code
        self.meta = meta

def success(**meta):
    return {"status": "success", **meta}

def error(code, **meta):
    return {"status": "error", "code": code, **meta}

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


    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return await self.send_json({"status": "error", "message": "INVALID_JSON"})

        key_command = data.get("command")

        if not key_command:
            return await self.send_json(error("MISSING_COMMAND"))
        
        rsv_id = data.get("rsv_id")
        if not rsv_id:
            return await self.send_json(error("MISSING_RSV_ID"))
        
        try:
            store = await self.get_store(rsv_id)
        except Exception:
            return await self.send_json(error("NOT_FOUND", target="store"))

        ### 라우팅
        handlers = {
            "new_message": self.handle_new_message,
            "RSV_mark_as_read": self.handle_mark_as_read,
            "selected_date": self.handle_selected_date,
            "rsv_renewal_cycle": self.handle_renewal_cycle,
            "start_end_date": self.handle_start_end_date,
            "temporary": self.handle_temporary_times,
            "dayoff_set": self.handle_dayoff_set,
            "num_set": self.handle_num_set,
        }
        handler = handlers.get(key_command)
        if not handler:
            return await self.send_json(error("UNKNOWN_COMMAND", command=key_command))
        
        # 실행
        try:
            result = await handler(store, data)
            await self.send_json(success(**(result or {})))
        except KnownError as ke:
            await self.send_json(error(ke.code, **ke.meta))
        except Exception as e:
            await self.send_json(error("SERVER_ERROR"))

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def get_store(self, rsv_id):
        return get_object_or_404(rsv.Store, pk=rsv_id)


    ### 핸들러
    async def handle_new_message(self, store, data):
        return {"message": "ok"}

    async def handle_mark_as_read(self, store, data):
        await self.mark_as_read(rsv_id)
        return {"message": "읽음 처리 완료"}

    async def handle_selected_date(self, store, data):
        print(data)
        return {"message": "logged"}

    # 기간설정 - 자동
    async def handle_renewal_cycle(self, store, data):
        renewal_cycle = data.get("renewal_cycle")
        set_date = data.get("set_date")
        if renewal_cycle is None or set_date is None:
            raise KnownError("INVALID_INPUT", fields=["renewal_cycle", "set_date"])
        await self.svc_set_renewal_cycle(store.pk, renewal_cycle, set_date)
        return {"message": "변경되었습니다."}

    # 기간설정 - 수동 
    async def handle_start_end_date(self, store, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date is None or end_date is None:
            raise KnownError("INVALID_INPUT", fields=["start_date", "end_date"])
        await self.svc_set_manual_period(store.pk, start_date, end_date)
        return {"message": "변경되었습니다."}

    # 시간설정 - 시간값들 저장
    async def handle_temporary_times(self, store, data):
        await self.svc_replace_store_times(store.pk, data)
        return {"message": "변경되었습니다."}
    
    # 휴무설정
    async def handle_dayoff_set(self, store, data):
        dayoff = data.get("dayoff")
        dayoff_cycle = data.get("dayoff_cycle")
        if not isinstance(dayoff, list):
            raise KnownError("INVALID_INPUT", field="dayoff")

        ok, payload = await self.svc_dayoff_set(store.pk, dayoff_cycle, dayoff)
        if not ok:
            raise KnownError("SERVER_ERROR")
        return payload
    
    # 인원설정
    async def handle_num_set(self, store, data):
        max_people = data.get("max_people")
        max_team = data.get("max_team")

        try:
            if max_people is None or max_team is None:
                raise KnownError("INVALID_INPUT", fields=["max_people", "max_team"])
            max_people = int(max_people)
            max_team = int(max_team)
            if max_people < 0 or max_team < 0:
                raise KnownError("INVALID_INPUT", reason="negative_not_allowed")
        except ValueError:
            raise KnownError("INVALID_INPUT", reason="not_integer")

        await self.svc_set_max_numbers(store.pk, max_people, max_team)
        return {"message": "변경되었습니다.", "max_people": max_people, "max_team": max_team}
    

    ### 트랜잭션
    @database_sync_to_async
    def svc_set_renewal_cycle(self, rsv_id, renewal_cycle, set_date):
        with transaction.atomic():
            store = get_object_or_404(rsv.Store, pk=rsv_id)
            store.renewal_cycle = renewal_cycle
            store.base_date = set_date
            store.start_rsv_possible = None
            store.end_rsv_possible = None
            store.save()

    @database_sync_to_async
    def svc_set_manual_period(self, rsv_id, start_date, end_date):
        with transaction.atomic():
            store = get_object_or_404(rsv.Store, pk=rsv_id)
            store.start_rsv_possible = start_date
            store.end_rsv_possible = end_date
            store.renewal_cycle = None
            store.base_date = None
            store.save()

    @database_sync_to_async
    def svc_replace_store_times(self, rsv_id, data):
        with transaction.atomic():
            store = get_object_or_404(rsv.Store, pk=rsv_id)
            rsv.Store_times.objects.filter(store_id=store).delete()

            to_create = []
            for key, value_obj in data.items():
                if key in ("command", "rsv_id"):
                    continue
                sort_type = key
                times_array = (value_obj or {}).get("times", [])
                if not isinstance(times_array, list):
                    continue
                for single_time in times_array:
                    to_create.append(
                        rsv.Store_times(
                            store_id=store,
                            sort_type=sort_type,
                            reservation_time=single_time
                        )
                    )

            if to_create:
                rsv.Store_times.objects.bulk_create(to_create)

    @database_sync_to_async
    def svc_dayoff_set(self, rsv_id, dayoff_cycle, dayoff_list):
        # 혹시몰라서 정규화
        normalize = lambda s: str(s).strip().lower()[:10]
        target = {normalize(v) for v in dayoff_list}

        try:
            with transaction.atomic():
                store = get_object_or_404(rsv.Store, pk=rsv_id)
                store.dayoff_cycle = dayoff_cycle
                store.save()

                # 얘도 혹시몰라
                if hasattr(store, "dayoff_cycle"):
                    store.dayoff_cycle = str(dayoff_cycle)[:20]
                    store.save()

                current_qs = rsv.Dayoff.objects.filter(store_id=store).values_list("dayoff", flat=True)
                current = set((v or "").strip().lower() for v in current_qs)

                to_add = list(target - current)
                to_del = list(current - target)

                # 추가
                if to_add:
                    rsv.Dayoff.objects.bulk_create(
                        [rsv.Dayoff(store_id=store, dayoff=v[:10]) for v in to_add],
                        ignore_conflicts=True
                    )

                # 삭제
                if to_del:
                    rsv.Dayoff.objects.filter(store_id=store, dayoff__in=to_del).delete()

                final = list(rsv.Dayoff.objects.filter(store_id=store).values_list("dayoff", flat=True))

            return True, {
                "message": "변경되었습니다.",
                "dayoff_cycle": getattr(store, "dayoff_cycle", None),
                "added": to_add,
                "deleted": to_del,
                "final": final,
            }
        except Exception:
            return False, {"message": "서버에러"}
        
    @database_sync_to_async
    def svc_set_max_numbers(self, rsv_id, max_people, max_team):
        with transaction.atomic():
            store = get_object_or_404(rsv.Store, pk=rsv_id)
            store.max_people = max_people
            store.max_team = max_team
            store.save()
            
            
    async def mark_as_read(self, rsvuser_id):
        rsv_read = await sync_to_async(rsv.Reservation_user.objects.get, thread_sensitive=True)(id=rsvuser_id)
        await sync_to_async(rsv_read.rsv_check, thread_sensitive=True)()

    async def send_chat_messages(self, message):
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )


    # async def send_to_front(self, message):
    #     print("전송할 메시지:", message)
    #     await self.channel_layer.group_send(
    #         # 인덱스 그룹에 전송(main_consumer)
    #         "index", {"type": "setting.message", "message": message}
    #     )

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

