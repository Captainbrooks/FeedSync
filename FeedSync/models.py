from django.db import models
from django.contrib.auth.models import User

# Create your models here.





 



class Posts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    caption=models.CharField(max_length=1000)
    image=models.TextField(null=False,blank=True)
    
    
    def get_like_count(self):
        return Like.objects.filter(post=self).count()
    
    
    def get_comment_count(self):
        return Comment.objects.filter(post=self).count()
    
    
 

        
    
    
    
    
class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
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
    
    
    
    
    
    
    
    



    
    
    
    



    
    
    
    
    


        
