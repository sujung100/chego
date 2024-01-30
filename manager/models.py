from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.db.models import OuterRef, Subquery

def get_admin_user_id():
    return User.objects.get(username='admin').id


User2 = get_user_model()
# Create your models here.
class Message(models.Model):
  author = models.ForeignKey(User2, related_name="author_messages", on_delete=models.CASCADE,)
  # recipient = models.ForeignKey(User2, related_name="recipient_messages", on_delete=models.CASCADE, default=get_admin_user_id,)
  content = models.TextField()
  timestamp = models.DateTimeField(auto_now_add=True)
  chatroom = models.CharField(max_length=20, null=True)
  is_read = models.BooleanField(default=False)

  def __str__(self):
    return self.author.username

  @classmethod
  def all_messages(cls, chatroom_name, page_number=1):
    page_size = 10
    start = (page_number - 1) * page_size
    end = start + page_size
    messages = cls.objects.filter(chatroom=chatroom_name).order_by("-timestamp").all()[start:end]
    # return reversed(messages)
    return messages

  @classmethod
  def latest_messages(cls):
    latest_content = cls.objects.filter(
      chatroom=OuterRef("chatroom")).order_by("-timestamp")

    latest_is_read = cls.objects.filter(
      chatroom=OuterRef("chatroom")).order_by("-timestamp").values("is_read")[:1]
    

    return cls.objects.values("chatroom").annotate(
      recent_timestamp = Max("timestamp"),
      recent_content = Subquery(latest_content.values("content")[:1]),
      recent_is_read = Subquery(latest_is_read)).order_by("-recent_timestamp")

  @classmethod
  def unread_messages(cls, chatroom_name):
    latest_read_message = cls.objects.filter(
      chatroom = chatroom_name,
      author__is_superuser = False,
      is_read = True,
    ).order_by("-timestamp").first()

    if latest_read_message is None:
      return cls.objects.filter(
        chatroom = chatroom_name,
        author__is_superuser = False,
      ).count()

    return cls.objects.filter(
      chatroom = chatroom_name,
      author__is_superuser = False,
      timestamp__gt = latest_read_message.timestamp
    ).count()

  
  def read_message(self):
    self.is_read = True
    self.save()