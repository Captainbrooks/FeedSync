from django.contrib import admin

# Register your models here.

from .models import *



admin.site.register(Messages)
admin.site.register(Posts)
admin.site.register(Profile)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Friendship)
admin.site.register(Notification)

