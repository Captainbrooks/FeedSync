from django.contrib import admin

# Register your models here.

from .models import *



admin.site.register(Messages)
admin.site.register(Posts)
admin.site.register(Profile)
admin.site.register(Like)
admin.site.register(Friendship)

