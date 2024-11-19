from django.contrib.auth.models import User
from FeedSync.models import Friendship,Notification

def friend_requests_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Friendship.objects.filter(receiver=request.user, accepted=False).count()
        
    return {'pending_requests_count': count}



def notifications(request):
    if request.user.is_authenticated:
        previous_notifications = Notification.objects.filter(receiver=request.user).order_by('-created_at')
    else:
        previous_notifications = []
    return {'previous_notifications': previous_notifications}




