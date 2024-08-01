from django.db import models
from django.contrib.auth.models import User

# Create your models here.





 



class Posts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    caption=models.CharField(max_length=1000)
    image=models.TextField(null=False,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def get_like_count(self):
        return Like.objects.filter(post=self).count()
    
    
    def get_comment_count(self):
        return Comment.objects.filter(post=self).count()
    
    
 

        
    
    
    
    
class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    cover_picture=models.TextField(User,null=True, blank=True)
    profile_picture=models.TextField(null=False,blank=True)
    
   
class Like(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    post=models.ForeignKey(Posts,on_delete=models.CASCADE)
    
    
    class Meta:
        unique_together = ('user', 'post')
        
        
    def __str__(self):
        return f"{self.user.username} likes {self.post.caption[:20]}"
    
    
    
    
    
    
class Comment(models.Model):
    user=user=models.ForeignKey(User,on_delete=models.CASCADE)
    post=models.ForeignKey(Posts, on_delete=models.CASCADE)
    content=models.TextField()
    
    
    
    def __str__(self):
        return f"{self.user.username} commented on {self.post.caption[:20]}: {self.content[:20]}"
    
    
    
class Friendship(models.Model):
    sender=models.ForeignKey(User,related_name="sent_requests",on_delete=models.CASCADE)
    receiver=models.ForeignKey(User,related_name="received_requests",on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    accepted=models.BooleanField(default=False)
    
    
    class Meta:
        unique_together = (('sender', 'receiver'), ('receiver', 'sender'))
    
    def __str__(self):
        return f"{self.sender} -> {self.receiver} (Accepted: {self.accepted})"
    
    
    
    
    



    
    
    
    
    


        
