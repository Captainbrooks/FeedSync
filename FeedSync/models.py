from django.db import models
from django.contrib.auth.models import User

# Create your models here.





 



class Posts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    caption=models.CharField(max_length=1000)
    image=models.TextField(null=False,blank=True)
    
    
 

        
    
    
    
    
class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_picture=models.TextField(null=False,blank=True)
    
    
    
    
class Reactions(models.Model):
    LIKE = 'like'
    COMMENT = 'comment'
    SHARE = 'share'
    
    REACTION_CHOICES = [
        (LIKE, 'Like'),
        (COMMENT, 'Comment'),
        (SHARE, 'Share'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES) 
    comment_text = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.reaction_type}d on {self.post.caption}"
    
    
    
    
    


        
