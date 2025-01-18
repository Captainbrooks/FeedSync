from django.shortcuts import render, redirect,get_object_or_404, HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import Posts, Profile,Like,Comment, Friendship,Messages,Notification
import base64
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



# Create your views here.



#  Converting the image into base64 string url in order to save into the database.
def image_to_base64(image_path):
    return base64.b64encode(image_path.read()).decode('utf-8')


# To convert the base64 string into the actual image so that we can display the real image in the UI

def base64_to_image(base64_string):
    return f"data:image/png;base64,{base64_string}"



    
    

@login_required(login_url="/login")
def index(request):
    user = request.user
    
    #getting the friends of the current logged in user where friendship exists no matter if the req was sent by user or received by user
    friends_with = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True)
    
    # Extract the users who are friends
    friend_users = set(friends_with.values_list('receiver', flat=True)) | set(friends_with.values_list('sender', flat=True))
    
    # Include the current user in the list of users
    friend_users.add(user)
    
    # Query posts from the current user and friends
    all_posts = Posts.objects.filter(user__in=friend_users).order_by('-created_at')
    
    # Get liked posts for the current user
    liked_posts = Like.objects.filter(user=user).values_list('post_id', flat=True)
    liked_posts_set = set(liked_posts)
    
    # # Retrieve profile images for all users who have posts
    users_with_posts = set(all_posts.values_list('user', flat=True))
    profiles = Profile.objects.filter(user__in=users_with_posts)
    profile_images = {profile.user.id: base64_to_image(profile.profile_picture) for profile in profiles if profile.profile_picture}
    
    for post in all_posts:
    #     # Convert post image to base64 if it exists
        if post.image:
            post.image_url = f"data:image/png;base64,{post.image}"
        
    #     # Check if the current user has liked this post
        post.user_has_liked = post.id in liked_posts_set
        
    #     # Retrieve comments for the post
        post.comments = Comment.objects.filter(post=post)
        
    #     # Retrieve like and comment counts for the post
        post.like_count = post.get_like_count()
        post.comment_count = post.get_comment_count()
        
        # Set the profile image URL of the user who made the post
        post.user_profile_image_url = profile_images.get(post.user.id, None)
    
    # Retrieve the profile image URL for the current user
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else ""
    
    all_friends = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True
    )
    
 
    my_friends=[]
    
    for f in all_friends:
        friend = f.sender if f.sender != user else f.receiver
        profile = Profile.objects.filter(user=friend).first()
        my_friends.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })
        
        
    
    
    # Context for the template
    context = {
        'posts': all_posts,
        'profile_image_url': profile_image_url,
        'my_friends':my_friends
    }
    
    
    
    if request.method == "POST":
      
        caption = request.POST.get('caption', '').strip()
        
        

        if not caption:
            caption=""
            


        file = request.FILES.get('image')
        image_string = None
        
        if file:
            try:
                image_string = image_to_base64(file)
            except Exception as e:
                messages.error(request, "There was an error uploading the image.",extra_tags="no_picture")
                return redirect("/index")
            
        if not caption and not file:
            messages.error(request, "You must provide a caption or upload an image.", extra_tags="no_content")
            return redirect("/index")
            
            
        

        new_post=Posts.objects.create(
            user=request.user,
            caption=caption,
            image=image_string
        )
        

            

        messages.success(request, "Post created successfully!",extra_tags="post_success")
        
        return redirect("/")
    
    return render(request,"index.html",context)





                
        


def login_page(request):
    
    if request.method=="POST":
        data=request.POST
        username=data.get('username')
        password=data.get('password')
        
        #checking if user exists or not
        
        if not User.objects.filter(username=username):
            messages.error(request, "Invalid Username")
            return redirect("/login")
        
        
        # if the username matches then we have to check if the password with the username matches or not
        
        user=authenticate(request, username=username, password=password)
        
        if user is None:
            messages.error(request, "Incorrect Password")
            return redirect("/login")
        
       
                
        # if both of them is successfull only then redirection to the main page
        login(request, user)
        return redirect('/index')
            
        
    
    return render(request, "login.html")


def register_page(request):
    
    if request.method=="POST":
        data=request.POST
        
        username=data.get('username')
        email=data.get('email')
        password=data.get('password')
        
        
        user=User.objects.filter(username=username)
        
        if user.exists():
            messages.info(request, "Username already Exists")
            return redirect('/register')
        
        
        user=User.objects.create(
            username=username,
            email=email,
            password=password
        )
        
        
        # creating a profile instance when user register for the first time
        profile=Profile.objects.create(user=user)
     
        
        user.set_password(password)
        user.save()
        
        messages.info(request, "Account created Successfully. Please login to continue")
        
        login(request, user)
        return redirect('/index')
            
    return render(request,"register.html")



def unread_message_count(user, friend):
    """Count the number of unread messages from `friend` to `user`."""
    return Messages.objects.filter(
        sender=friend,
        receiver=user,
        is_read=False  # Assuming there's a field to mark messages as read
    ).count()



@login_required(login_url="/login")
def messenger(request):
    
    user=request.user
    # Retrieve the profile image URL for the current user
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    
    friends_with = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True)
    
    
    my_friends=[]
    
    for f in friends_with:
        friend = f.sender if f.sender != user else f.receiver
        profile = Profile.objects.filter(user=friend).first()

        
        
        unread_count = unread_message_count(user, friend)
        my_friends.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None,
            'unread_count':unread_count
            
        })
        
        
    list_friends=list(my_friends)
        
        

        
        
     
        
    
    
    
    
    context={
        'profile_image_url': profile_image_url,
        'my_friends':my_friends,
        'user':user
    }
    return render(request, "messenger.html",context)







@login_required(login_url="/login")
def friends(request):
    user = request.user
    
    
  
    all_friends = Friendship.objects.filter(
   
         Q(sender=user) | Q(receiver=user), 
        accepted=True)
    
    friends_with=[]
    
    for f in all_friends:

   
        friend = f.sender if f.sender != user else f.receiver
        profile = Profile.objects.filter(user=friend).first()
        friends_with.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })
        
    total_friends = len(friends_with)
    

    receivedRequests = Friendship.objects.filter(receiver=user,accepted=False)
    
    sentRequests = Friendship.objects.filter(sender=user,accepted=False)
    
    received_reqs = []
    sent_reqs = []
    
    # Process received requests
    for req in receivedRequests:
        profile = Profile.objects.filter(user=req.sender).first()  
        if profile:
            received_reqs.append({
                'sender': profile.user.username,
                'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
            })
    
    # Process sent requests
    for req in sentRequests:
        profile = Profile.objects.filter(user=req.receiver).first()  
        if profile:
            sent_reqs.append({
                'receiver': profile.user.username,
                'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
            })
            
            
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
            
 
    
    
    
    
    

            
  
            
   
    
    # Always ensure context is defined before returning the response
    context = {
        'received_reqs': received_reqs,
        'sent_reqs': sent_reqs,
        'friends_with':friends_with,
        'profile_image_url':profile_image_url,
        'total_friends':total_friends
        
        
    }
    
    return render(request, "friends.html", context)
 



@login_required(login_url="/login")
def profile(request):
    user=request.user
    

    
    all_posts=Posts.objects.filter(user=user).order_by('-created_at')
    

    
    liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)
    liked_posts_set = set(liked_posts)
    
    
    for post in all_posts:
        if post.image:
            post.image_url = f"data:image/png;base64,{post.image}"
        post.user_has_liked = post.id in liked_posts_set  
        
        
        post.comments=Comment.objects.filter(post=post)
        
        post.like_count = post.get_like_count()
        post.comment_count = post.get_comment_count()
          
        post.like_count=post.get_like_count()
        
        post.comment_count=post.get_comment_count() 
            
            
            
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None  
    
    
    
    # Add friend or Unfrend logic at UI.. checking if friendship exists..
    all_friends = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True
    )
    
 
    my_friends=[]
    
    for f in all_friends:
        friend = f.sender if f.sender != user else f.receiver
        profile = Profile.objects.filter(user=friend).first()
        my_friends.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })
        

    if request.method == "POST":
        
      

        file = request.FILES.get('profilepic')
        if file:
            profile_string = image_to_base64(file)
            
            profile, created = Profile.objects.get_or_create(user=user)
            profile.profile_picture = profile_string
            profile.save()
            messages.success(request,"Profile picture changed successfully")
        
            return redirect("/profile")

    
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    
    
    
    if request.method == "POST":
      
        data=request.POST
        
        caption = data.get('caption', '').strip()
        
        if not caption:
            messages.error(request, "Caption cannot be spaces only. Please enter a caption.")
            return redirect("/index")  
        
       
        
       
        
        file = request.FILES.get('image')
        image_string = None
        if file:
            try:
                image_string = image_to_base64(file)
            except Exception as e:
                messages.error(request, "There was an error uploading the image.")
                return redirect("/index")
        
       
        
  
        Posts.objects.create(
            user=request.user,
            caption=caption,
            image=image_string    
        )
        
        messages.success(request, "Post created successfully!")
    
    context = {'profile_image_url': profile_image_url,'posts':all_posts,'profile_image_url': profile_image_url,'my_friends':my_friends}
    return render(request, "profile.html", context)


@login_required(login_url="/login")
def like_post(request,post_id):
    user=request.user
    
    

    
    

        
        
    profile = Profile.objects.filter(user=user).first()
    profile_picture = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    

    
    

    
    
    

    
    post=get_object_or_404(Posts, id=post_id)

    
    post_author=post.user
    
    
    
    like,created=Like.objects.get_or_create(user=request.user,post=post)
    
    
    message=f"{user.username} liked your post:{post.caption}"
    

        
    if not created:
        # If the like already exists, delete it (unlike)
        like.delete()
        liked = False
    else:
        liked = True
        print("liked created")
        
        if user != post_author:
            print("user is not author")
            
            new_notification=Notification.objects.create(
               
                sender=user,
                profile_picture=profile_picture,
                receiver=post_author,
                notification=message
            )
            
            print("new notification:" , new_notification)
            
            
            
            
            
            
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{post_author.id}_notifications",
                    {
                    "type": "send_notification",
                    "notification": message,
                    "profile_picture":profile_picture
                  
                    }
            )
            
            
            
        

    like_count = post.get_like_count()

    return JsonResponse({
        'liked': liked,
        'like_count': like_count
    })
    

@login_required(login_url="/login")
def add_comment(request,post_id):
    user=request.user
    

    
    
    profile = Profile.objects.filter(user=user).first()
    profile_picture = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    


    post=get_object_or_404(Posts , id=post_id)
    
    post_author=post.user
    
    
    if request.method=="POST":
        
        

        data = json.loads(request.body)
        comment_text = data.get('comment_text')
        
        
        trim_comments=comment_text.strip()

        
        if not trim_comments:
            
            return JsonResponse({'status': 'error', 'message': "Caption cannot be spaces only. Please enter a comment"}, status=400)
            
        
        
      
        
        comment_data={}

        if comment_text:
            new_comment=Comment.objects.create(user=request.user, post=post, content=trim_comments)
            
           
            
            comment_data = {
                'id': new_comment.id,
                'user': new_comment.user.username,
                'content': new_comment.content,
                'profile_picture':new_comment.user.profile.profile_picture,
                'post_id':post.id
                
            }
            
            sendingUser=comment_data['user']
            

            
            authenticatedUser=get_object_or_404(User,username=sendingUser)


            
        if user != post_author:
            
            message=f"{new_comment.user.username} commented on your post {new_comment.content}"
            
            Notification.objects.create(
                sender=user,
                profile_picture=profile_picture,
                receiver=post_author,
                notification=message
            )
        
        
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{post_author.id}_notifications",
                {
                    "type": "send_notification",
                    "notification": message,
                    "profile_picture":profile_picture
                }
            )
            
        
    else:
          
        return JsonResponse({'status': 'error', 'message': "Couldn't add a comment"}, status=400)
            
            
           
            
    comment_count=post.get_comment_count()
    
    
            
            
            
    return JsonResponse({'status':'success','comments':comment_data,'comment_count':comment_count})




@login_required(login_url="/login")
def delete_comment(request, post_id, comment_id):
    

    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    
    

    
    
        


    
    

    if request.method == "DELETE":
        comment.delete()
        
        comment_count = Comment.objects.filter(post_id=post_id).count()
        
        return JsonResponse({'status': 'success', 'message': 'Comment deleted successfully.','comment_count': comment_count})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)



@login_required(login_url="/login")
def search_friends(request):

    user=request.user
    query=request.GET.get('search','').strip()

    
    if not query:
        return JsonResponse({'status': 'error', 'message': f"Couldn't find any people with '{query}'"})


    
    
    
    matching_profiles = Profile.objects.filter(user__username__icontains=query)

    
    if not matching_profiles:
            return JsonResponse({'results': [], 'message': f"Couldn't find any people with '{query}'"})
    else:
        results=[]
        
        for profile in matching_profiles:
            profile_data={
                'username':profile.user.username,
                'profile_picture':base64_to_image(profile.profile_picture) if profile.profile_picture else None
            }
            results.append(profile_data)
            
    
    
    return JsonResponse({'results':results})









@login_required(login_url="/login")
def profile_url(request, username):
    
  
    
    
    admin=request.user
    admin_profile=get_object_or_404(Profile,user=admin)
    

    user = get_object_or_404(User, username=username)
    
   
    
    
    profile, created = Profile.objects.get_or_create(user=user)
 
    

    
    
    admin_info={
        'admin_name':admin_profile.user.username,
        'admin_profile_image':base64_to_image(admin_profile.profile_picture) if admin_profile.profile_picture else None
    }
    
    profile_info = {
        'profile_name': profile.user.username,
        'profile_image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
    }
       
    all_posts=Posts.objects.filter(user=user).order_by('-created_at')
    
    
    
    liked_posts=Like.objects.filter(user=request.user).values_list('post_id', flat=True)
    liked_posts_set=set(liked_posts)
    
    my_friends=[]
    pending_reqs=[]
    
    all_friends=Friendship.objects.filter(
        Q(sender=admin) | Q(receiver=admin), 
        Q(accepted=True)| Q(accepted=False))
    
    
    for f in all_friends:
            friend = f.sender if f.sender != admin else f.receiver
            
            if f.accepted:
                my_friends.append(friend.username)
            else:
                if friend.username not in pending_reqs:
                    pending_reqs.append(friend.username)
                    
                    
                    
                
            
            
            
    
    friend_friends=[]
    
    friend_all_friends=Friendship.objects.filter(
        
        Q(sender=user)| Q(receiver=user),
        accepted=True)
    

    
    for fri in friend_all_friends:
        friend_friend=fri.sender if fri.sender != user else fri.receiver
        friend_profile = Profile.objects.filter(user=friend_friend).first()
        
        friend_friends.append({
            'name': friend_friend.username,
            'image': base64_to_image(friend_profile.profile_picture) if friend_profile.profile_picture else None
        })
        
        
    
    
    
    
    for post in all_posts:
        
        if post.image:
            post.image_url=f"data:image/png;base64,{post.image}"
            
        post.user_has_liked=post.id in liked_posts_set
        
        post.comments=Comment.objects.filter(post=post)
    
            
        post.like_count = post.get_like_count()
        post.comment_count = post.get_comment_count()
        
          
            
                  

    pprofile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None

    
    context={'profile_info':profile_info,'pprofile_image_url': pprofile_image_url,'posts':all_posts,'admin_info':admin_info,'my_friends':my_friends,'friend_friends':friend_friends,'pending_reqs':pending_reqs}
    
    return render(request, "profile_url.html",context)


@login_required(login_url="/login")
def send_request(request,username):

    user=request.user
    
    profile = Profile.objects.filter(user=user).first()
    profile_picture = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    
    current_page = request.META.get('HTTP_REFERER', '/')

    
    friend_req_receiver=get_object_or_404(User,username=username)
    
    existingfriendship=Friendship.objects.filter(
     
        Q(sender=user, receiver=friend_req_receiver) |
        Q(sender=friend_req_receiver, receiver=user)).exists()
    if not existingfriendship:
        
        Friendship.objects.create(
            sender=user,
            receiver=friend_req_receiver,
            accepted=False
        )
         
        messages.success(request,f"Friend request sent to {friend_req_receiver}" )
        
    message=f"You have received a friend request from {user.username}"
        
        
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{friend_req_receiver.id}_notifications",
        {
            "type": "send_notification",
            "notification": message,
            "profile_picture":profile_picture
        }
    )
    
    
        
    return redirect(current_page)


@login_required(login_url="/login")
def accept_request(request):
    
    current_page = request.META.get('HTTP_REFERER', '/')

    if request.method=="POST":
        
        
        sender_name=request.POST.get('sender')
        sender_user=User.objects.get(username=sender_name)
        
        
        
        print("sender_user: ", sender_user)

        user=request.user
        profile = Profile.objects.get(user=sender_user)
        profile_picture = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
        
        
        if sender_name:
            friend_requests=Friendship.objects.filter(sender__username=sender_name,receiver=user)
            
            for req in friend_requests:
                if not req.accepted:
                    req.accepted = True
                    req.save()
                    
        message=f"{sender_user.username} has accepted your friend request."
        
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{sender_user.id}_notifications",
                {
                "type": "send_notification",
                "notification": message,
                "profile_picture":profile_picture
                }
        )

    
    return redirect(current_page)
        

@login_required(login_url="/login")    
def reject_request(request):
    
    current_page = request.META.get('HTTP_REFERER', '/') 
   
    if request.method=="POST":

        sender_name=request.POST.get('sender')
 
        user=request.user
        
        
        if sender_name:
            friend_requests=Friendship.objects.filter(sender__username=sender_name,receiver=user)
            friend_requests.delete()
                             
    return redirect(current_page)


@login_required(login_url="/login")
def cancel_request(request):
    
    current_page = request.META.get('HTTP_REFERER', '/')

    if request.method=="POST":
        data=request.POST
        
        sent_to=request.POST.get('send_to')
        
       
       
        user=request.user
        

        
        if sent_to:
            friend_req=Friendship.objects.filter(receiver__username=sent_to,sender=user)
            friend_req.delete()
            messages.success(request, f"Your Friend Request to {sent_to} Cancelled")
            
            
    return redirect(current_page)


@login_required(login_url="/login")
def unfriend(request):
    user = request.user
    
    current_page = request.META.get('HTTP_REFERER', '/')
    
    if request.method == "POST":

        data = request.POST
        
        unfriend_username = data.get('unfriend')
     
        # Get the User instance for the user to unfriend
   
        unfriend_user = User.objects.get(username=unfriend_username)
            
        
        
        # Find and delete the friendship records involving the current user and the unfriend_user
        friendships_to_delete = Friendship.objects.filter(
            (Q(sender=user) & Q(receiver=unfriend_user)) | 
            (Q(sender=unfriend_user) & Q(receiver=user)),
            accepted=True
        )
        
        friendships_to_delete.delete()
        messages.success(request, f"You are no longer friend with {unfriend_user}")
    return redirect(current_page)
        
        
    
def updatePost(request,post_id):
    user=request.user
    
    profile=Profile.objects.get(user=user)
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    
    
    update_post=Posts.objects.get(user=user,id=post_id)
    
    
    if request.method=="POST":
        data=request.POST
        
        post_caption=data.get('caption')
        
        trim_caption=post_caption
        
        if not trim_caption:
            messages.error(request, "Caption cannot be spaces only.Please enter a caption")
            return redirect("/index")
         
        image_string=""
         
        if request.FILES:
            file=request.FILES.get('image')
            if file:
                image_string=image_to_base64(file)
            else:
                None
                  
               

        update_post.caption=post_caption
        
        if image_string:
            update_post.image=image_string
        else:
            update_post.image=None
        
        update_post.save()
        
        messages.success(request, "Post updated successfully")
        
        

        
        return redirect('/index/')
        
    
    
    context={
        'post_caption':update_post.caption,
        'post_image':base64_to_image(update_post.image) if update_post.image else None,
        'profile_image_url':profile_image_url
    }
    
    
    return render(request,"updatePost.html" ,context)   



def deletePost(request,post_id):
    user=request.user
    
    current=request.META.get('HTTP_REFERER')
    
    delete_post=Posts.objects.get(user=user,id=post_id)
    
    if not delete_post:
        messages.error("The post is not found")
        
    else:
        delete_post.delete()
        messages.success(request, "Post deleted successfully")
        
        
    return redirect(current)
        


def logout_page(request):
    logout(request)
    return redirect('/login')





def deleteprofile(request):
    user=request.user
    
    profile = get_object_or_404(Profile, user=user)
    
    if profile.profile_picture:
        profile.profile_picture=None
        profile.save()
        messages.success(request, "Profile picture deleted")
        return redirect("/profile")
        
        


def clear_notification(request):
    print("clear notification reached")
    current = request.META.get('HTTP_REFERER')
    

    prev_notification = Notification.objects.filter(receiver=request.user)

    if prev_notification:
        print("Notification: ", prev_notification)
        prev_notification.delete()
    else:
        print("No notification found for the user.")

    return redirect(current)



def search_messenger_friend(request):
    print("search messenger Friend Reached")
    
    user=request.user
    query=request.GET.get('search', '')
    lowercase_query = query.lower()
    
    
    

    
    results=[]
    
    all_friends=Friendship.objects.filter(
        Q(sender=user,) | Q(receiver=user),accepted=True
        )
    
    for f in all_friends:
        friend = f.sender if f.sender != user else f.receiver
        lowercase_friendname=friend.username.lower()
        
        if lowercase_query in lowercase_friendname:
           
            profile = Profile.objects.filter(user=friend).first()
            results.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })
        
            

        
    
    
  
        
    
    return JsonResponse({'status':'success','results':results})
    
    

    
    
    
    
    
    




  

        
        
    

    
    
    

    
    










    
    
    
    
    
    
    
        
        
 
        
        
        
        
        
        
