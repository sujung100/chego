from django.contrib import admin
from . import models

# Register your models here.

class ChatroomFilter(admin.SimpleListFilter):
    title = 'Chatroom' # The title displayed on the admin page
    parameter_name = 'chatroom' # The parameter that will be used in the URL query

    def lookups(self, request, model_admin):
        # This method returns a list of tuples. Each tuple contains a coded value and a human-readable name for an option that the user can select.
        chatrooms = set([c.chatroom for c in models.Message.objects.all()])
        return [(c, c) for c in chatrooms]

    def queryset(self, request, queryset):
        # This method is called when the user selects an option.
        if self.value():
            return queryset.filter(chatroom=self.value())

class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'timestamp', 'chatroom')
    list_filter = (ChatroomFilter,)

admin.site.register(models.Message, MessageAdmin)