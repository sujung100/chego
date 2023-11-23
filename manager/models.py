from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

# def get_admin_user_id():
#     return User.objects.get(username='admin').id


User2 = get_user_model()
# Create your models here.
class Message(models.Model):
  author = models.ForeignKey(User2, related_name="author_messages", on_delete=models.CASCADE,)
  recipient = models.ForeignKey(User2, related_name="recipient_messages", on_delete=models.CASCADE, null=True, blank=True,)
  content = models.TextField()
  timestamp = models.DateTimeField(auto_now_add=True)
  chatroom = models.CharField(max_length=20, null=True)

  def __str__(self):
    return self.author.username

  @classmethod
  def all_messages(cls, username):
    return cls.objects.filter(chatroom=username).order_by("-timestamp").all()[:10]