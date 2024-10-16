from django.shortcuts import render, redirect,get_object_or_404, HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import Posts, Profile,Like,Comment, Friendship
import base64
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q



# Create your views here.



#  Converting the image into base64 string url in order to save into the database.
def image_to_base64(image_path):
    return base64.b64encode(image_path.read()).decode('utf-8')


# To convert the base64 string into the actual image so that we can display the real image in the UI

def base64_to_image(base64_string):
    return f"data:image/png;base64,{base64_string}"


def base(admin):
    admin_profile=get_object_or_404(Profile,user=admin)
    
    admin_info={
        'admin_name':admin_profile.user.username,
        'admin_profile_image':base64_to_image(admin_profile.profile_picture) if admin_profile.profile_picture else None
    }
    
    
    return admin_info
    
    

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
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
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
      
        data=request.POST
        
        caption=data.get('caption')
        
       
        
        trim_caption=caption.strip()
        
        if not trim_caption:
            messages.error(request, "Caption cannot be spaces only.Please enter a caption")
            return redirect("/index")
               
        file=request.FILES.get('image')
        if file:
            image_string=image_to_base64(file)
        else:
            pass  
        
       
        
  
        Posts.objects.create(
            user=user,
            caption=caption,
            image=image_string    
        )
        
        return redirect('/index')
    
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
        
        user.set_password(password)
        user.save()
        
        messages.info(request, "Account created Successfully. Please login to continue")
        
        login(request, user)
        return redirect('/index')
            
    return render(request,"register.html")

@login_required(login_url="/login")
def feed(request):
    return render("feed.html")

@login_required(login_url="/login")
def messenger(request,username=None):
    
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
        my_friends.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })
    
    
    
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
        print(f"Sender: {f.sender}")
        print(f"Receiver: {f.receiver}")
   
        friend = f.sender if f.sender != user else f.receiver
        profile = Profile.objects.filter(user=friend).first()
        friends_with.append({
            'name': friend.username,
            'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
        })

    receivedRequests = Friendship.objects.filter(receiver=user,accepted=False)
    
    sentRequests = Friendship.objects.filter(sender=user,accepted=False)
    
    received_reqs = []
    sent_reqs = []
    
    # Process received requests
    for req in receivedRequests:
        profile = Profile.objects.filter(user=req.sender).first()  # Use .first() to avoid multiple results
        if profile:
            received_reqs.append({
                'sender': profile.user.username,
                'image': base64_to_image(profile.profile_picture) if profile.profile_picture else None
            })
    
    # Process sent requests
    for req in sentRequests:
        profile = Profile.objects.filter(user=req.receiver).first()  # Use .first() to avoid multiple results
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
        'profile_image_url':profile_image_url
        
        
    }
    
    return render(request, "friends.html", context)
 
    return render(request, "friends.html",context)


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
        
        profile = Profile.objects.filter(user=user).first()
        profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
        
        post.like_count=post.get_like_count()
        
        post.comment_count=post.get_comment_count() 
            
            
            
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None  
    
    
    
    # Add friend or Unfrend logic at UI.. checking if friendship exists..
    all_friends=Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True)
    
    print(f"My friends : {all_friends}")
    
    my_friends=[]
    
    for f in all_friends:
        friend = f.sender if f.sender != user else f.receiver
        my_friends.append(friend.username)
        

    if request.method == "POST":

        file = request.FILES.get('profilepic')
        if file:
            profile_string = image_to_base64(file)
            
            profile, created = Profile.objects.get_or_create(user=user)
            profile.profile_picture = profile_string
            profile.save()
        
            return redirect("/profile")
    
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    context = {'profile_image_url': profile_image_url,'posts':all_posts,'profile_image_url': profile_image_url,'my_friends':my_friends}
    return render(request, "profile.html", context)


@login_required(login_url="/login")
def like_post(request,post_id):
    
    
    post=get_object_or_404(Posts, id=post_id)
    
    current_page = request.META.get('HTTP_REFERER', '/')
    

    
    existing_like = Like.objects.filter(user=request.user, post=post).first()
    
    if existing_like:
        # If like exists, remove it (unlike the post)
        existing_like.delete()
        
    else:
        # Otherwise, create a new like
        Like.objects.create(user=request.user, post=post)
    
    # Redirect to the post's detail page or another appropriate page
    return redirect(current_page, post_id=post_id)
    

@login_required(login_url="/login")
def add_comment(request,post_id):

    post=get_object_or_404(Posts , id=post_id)
    
    current_page = request.META.get('HTTP_REFERER', '/')
    
    if request.method=="POST":

        comment_text = request.POST.get('comment_text')

        if comment_text:
            Comment.objects.create(user=request.user, post=post, content=comment_text)
            messages.success(request, "Comment Added successfully.", extra_tags="add_comment")
            return redirect(current_page)
        
        else:
            messages.error(request,"COuldn't add a comment")
            
            
            
            
            
    return redirect(current_page)




@login_required(login_url="/login")
def delete_comment(request,post_id,comment_id):
    comment=get_object_or_404(Comment,id=comment_id,post_id=post_id,user=request.user)
    
    current_page = request.META.get('HTTP_REFERER', '/')
    
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.", extra_tags="delete_comment")
    else:
        messages.error(request, "Invalid request method.")

    return redirect(current_page)



@login_required(login_url="/login")
def search_friends(request):
    user=request.user
    query=request.GET.get('search','').strip()
    
    if not query:
        messages.error(request, "Search query is empty.",extra_tags="search_friends_empty")
    
    
    
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
    
    print(f"admin:{admin_profile.user.username}")
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    

    
    
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
    
    
    for post in all_posts:
        
        if post.image:
            post.image_url=f"data:image/png;base64,{post.image}"
            
        post.user_has_liked=post.id in liked_posts_set
        
        post.comments=Comment.objects.filter(post=post)
    
            
        post.like_count = post.get_like_count()
        post.comment_count = post.get_comment_count()
        
        
        all_friends=Friendship.objects.filter(
        Q(sender=admin) | Q(receiver=admin), 
        accepted=True)
        
        my_friends=[]
    
        for f in all_friends:
            friend = f.sender if f.sender != admin else f.receiver
            my_friends.append(friend.username)
                  

    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None

    
    context={'profile_info':profile_info,'posts':all_posts,'profile_image_url': profile_image_url, 'admin_info':admin_info,'my_friends':my_friends}
    
    return render(request, "profile_url.html",context)


@login_required(login_url="/login")
def send_request(request,username):

    user=request.user

    
    friend_req_receiver=get_object_or_404(User,username=username)
    print(friend_req_receiver)
    
    existingfriendship=Friendship.objects.filter(
     
        Q(sender=user, receiver=friend_req_receiver) |
        Q(sender=friend_req_receiver, receiver=user)).exists()
    if not existingfriendship:
        
        Friendship.objects.create(
            sender=user,
            receiver=friend_req_receiver,
            accepted=False
        )
        
        messages.info(request, "Friend Req Sent", extra_tags="req_sent")
        
    return redirect('/')


@login_required(login_url="/login")
def accept_request(request):

    if request.method=="POST":
        
        
        sender_name=request.POST.get('sender')

        user=request.user
        
        
        if sender_name:
            friend_requests=Friendship.objects.filter(sender__username=sender_name,receiver=user)

            
            
            for req in friend_requests:
                if not req.accepted:
                    req.accepted = True
                    req.save()

    
    return redirect('/friends')
        

@login_required(login_url="/login")    
def reject_request(request):
   
    if request.method=="POST":

        sender_name=request.POST.get('sender')
 
        user=request.user
        
        
        if sender_name:
            friend_requests=Friendship.objects.filter(sender__username=sender_name,receiver=user)
            friend_requests.delete()
            

            
            
            
            
            
            

                    
                    
    return redirect('/friends')


@login_required(login_url="/login")
def cancel_request(request):
    

    if request.method=="POST":
        data=request.POST
        
        sent_to=request.POST.get('send_to')
        
       
       
        user=request.user
        

        
        if sent_to:
            friend_req=Friendship.objects.filter(receiver__username=sent_to,sender=user)
            friend_req.delete()
            
            
    return redirect("/friends")


@login_required(login_url="/login")
def unfriend(request):
    user = request.user
    print(user)
    
    current_page = request.META.get('HTTP_REFERER', '/')
    
    if request.method == "POST":

        data = request.POST
        
        unfriend_username = data.get('unfriend')
        print(unfriend_username)
     
        # Get the User instance for the user to unfriend
   
        unfriend_user = User.objects.get(username=unfriend_username)
            
        print(unfriend_user)
        
        
        # Find and delete the friendship records involving the current user and the unfriend_user
        friendships_to_delete = Friendship.objects.filter(
            (Q(sender=user) & Q(receiver=unfriend_user)) | 
            (Q(sender=unfriend_user) & Q(receiver=user)),
            accepted=True
        )
        
        friendships_to_delete.delete()
    return redirect(current_page)
        
        
    
def updatePost(request,post_id):
    user=request.user
    
    update_post=Posts.objects.get(user=user,id=post_id)
    
    print(f"Updating Post:{update_post.caption}")
    
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
        
        return redirect('/index/')
        
    
    
    context={
        'post_caption':update_post.caption,
        'post_image':base64_to_image(update_post.image) if update_post.image else None
    }
    
    
    return render(request,"updatePost.html" ,context)   



def deletePost(request,post_id):
    user=request.user
    
    delete_post=Posts.objects.get(user=user,id=post_id)
    
    if not delete_post:
        messages.error("The post is not found")
        
    else:
        delete_post.delete()
        
        
    return redirect('/index')
        


def logout_page(request):
    logout(request)
    return redirect('/login')



  

        
        
    

    
    
    

    
    










    
    
    
    
    
    
    
        
        
 
        
        
        
        
        
        
