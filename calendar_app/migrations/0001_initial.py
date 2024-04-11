# Generated by Django 4.2.3 on 2023-07-31 19:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('store_name', models.CharField(max_length=20)),
                ('address', models.CharField(max_length=50)),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('mdate', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': '업체등록',
                'ordering': ('-mdate',),
            },
        ),
        migrations.CreateModel(
            name='Store_times',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_time', models.CharField(max_length=10, null=True)),
                ('times_cdate', models.DateTimeField(auto_now_add=True)),
                ('times_mdate', models.DateTimeField(auto_now=True)),
                ('store_id', models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, to='calendar_app.store')),
            ],
        ),
        migrations.CreateModel(
            name='Reservation_user',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_name', models.CharField(max_length=20, null=True)),
                ('reservation_date', models.CharField(max_length=20, null=True)),
                ('user_time', models.CharField(max_length=20, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('store_id', models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, to='calendar_app.store')),
            ],
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('manager_name', models.CharField(max_length=20, null=True)),
                ('manager_phone', models.CharField(max_length=20, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
