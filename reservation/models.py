from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
# Create your models here.


class Store(models.Model):
    id = models.AutoField(primary_key=True)
    store_name = models.CharField(max_length=20)
    address = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True)
    
    cdate = models.DateTimeField(auto_now_add = True)
    mdate = models.DateTimeField(auto_now = True)
    


    class Meta:
        # pass
        verbose_name_plural = "업체등록"
        ordering = ("-mdate",)

    def __str__(self):
        return f"{self.store_name}{self.owner}{self.cdate}"
    
    def get_absolute_url(self):
        return reverse("reservation:detail", args=(self.id,))
    
class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager_name = models.CharField(max_length=20, null=True)
    manager_phone = models.CharField(max_length=20, null=True)
    

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'manager'):
        Manager.objects.create(user=instance)
    # if created:
    #     Manager.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'manager'):
        instance.manager.save()


class Reservation_user(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=20, null=True)
    user_phone = models.CharField(max_length=20, null=True)
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE, db_column="store_id")
    reservation_date = models.CharField(max_length=20, null=True)
    user_time = models.CharField(max_length=20, null=True)
    date = models.DateTimeField(auto_now_add = True)
    visitor_num = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], null=True)
    pwhash = models.CharField(max_length=200, null=True)
    reservation_check = models.BooleanField(default=False)

class Store_times(models.Model):
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE, db_column="store_id")
    reservation_time = models.CharField(max_length=10, null=True)
    
    times_cdate = models.DateTimeField(auto_now_add = True)
    times_mdate = models.DateTimeField(auto_now = True)

class Login_try(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(Reservation_user, on_delete=models.CASCADE, db_column="user_id")
    retry_login = models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(5)])
    last_login_date = models.DateTimeField(auto_now = True)
    is_block = models.CharField(max_length=1, default="N")
    block_count = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(3)])
