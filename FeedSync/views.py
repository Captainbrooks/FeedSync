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

@login_required(login_url="/login")
def index(request):
    user = request.user
    
    # Retrieve all accepted friendships where the user is either the sender or receiver
    friends_with = Friendship.objects.filter(
        Q(sender=user) | Q(receiver=user), 
        accepted=True
    )
    
    # Extract the users who are friends
    friend_users = set(friends_with.values_list('receiver', flat=True)) | set(friends_with.values_list('sender', flat=True))
    
    # Include the current user in the list of users
    friend_users.add(user)
    
    # Query posts from the current user and friends
    all_posts = Posts.objects.filter(user__in=friend_users).order_by('-created_at')
    
    # Get liked posts for the current user
    liked_posts = Like.objects.filter(user=user).values_list('post_id', flat=True)
    liked_posts_set = set(liked_posts)
    
    # Retrieve profile images for all users who have posts
    users_with_posts = set(all_posts.values_list('user', flat=True))
    profiles = Profile.objects.filter(user__in=users_with_posts)
    profile_images = {profile.user.id: base64_to_image(profile.profile_picture) for profile in profiles if profile.profile_picture}
    
    for post in all_posts:
        # Convert post image to base64 if it exists
        if post.image:
            post.image_url = f"data:image/png;base64,{post.image}"
        
        # Check if the current user has liked this post
        post.user_has_liked = post.id in liked_posts_set
        
        # Retrieve comments for the post
        post.comments = Comment.objects.filter(post=post)
        
        # Retrieve like and comment counts for the post
        post.like_count = post.get_like_count()
        post.comment_count = post.get_comment_count()
        
        # Set the profile image URL of the user who made the post
        post.user_profile_image_url = profile_images.get(post.user.id, None)
    
    # Retrieve the profile image URL for the current user
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None
    
    all_friends = Friendship.objects.filter(
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
def messenger(request):
    return render(request, "messenger.html")


@login_required(login_url="/login")
def friends(request):
    user = request.user
    
    
    
    all_friends = Friendship.objects.filter(
       accepted=True
    )
    
 
    friends_with=[]
    
    for f in all_friends:
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
    
    # Always ensure context is defined before returning the response
    context = {
        'received_reqs': received_reqs,
        'sent_reqs': sent_reqs,
        'friends_with':friends_with
    }
    
    return render(request, "friends.html", context)

            
        
        
    
   
    

    
    return render(request, "friends.html",context)


@login_required(login_url="/login")
def profile(request):
    user=request.user
    
    all_posts=Posts.objects.filter(user=user)
    
    all_posts=Posts.objects.filter(user=user)
    

    
    liked_posts = Like.objects.filter(user=user).values_list('post_id', flat=True)
    liked_posts_set = set(liked_posts)
    
    
    
    
    
    
    
    image=Posts.objects.filter(user=user)
    
    for post in all_posts:
        if post.image:
            post.image_url = f"data:image/png;base64,{post.image}"
        post.user_has_liked = post.id in liked_posts_set  
        post.comments = Comment.objects.filter(post=post)
        
        post.like_count=post.get_like_count()
        
        post.comment_count=post.get_comment_count() 
            
            
            
    profile = Profile.objects.filter(user=user).first()
    profile_image_url = base64_to_image(profile.profile_picture) if profile and profile.profile_picture else None  
               
    
   
  
   
    
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
    
    context = {'profile_image_url': profile_image_url,'posts':all_posts,'profile_image_url': profile_image_url}
    return render(request, "profile.html", context)


@login_required(login_url="/login")
def like_post(request,post_id):
    
    
    post=get_object_or_404(Posts, id=post_id)
    

    
    existing_like = Like.objects.filter(user=request.user, post=post).first()
    
    if existing_like:
        # If like exists, remove it (unlike the post)
        existing_like.delete()
    else:
        # Otherwise, create a new like
        Like.objects.create(user=request.user, post=post)
    
    # Redirect to the post's detail page or another appropriate page
    return redirect('/index', post_id=post_id)
    
    
    





@login_required(login_url="/login")
def add_comment(request,post_id):

    post=get_object_or_404(Posts , id=post_id)
    
    if request.method=="POST":

        comment_text = request.POST.get('comment_text')

        if comment_text:
            Comment.objects.create(user=request.user, post=post, content=comment_text)
            messages.success(request, "Comment Added successfully.", extra_tags="add_comment")
            return redirect('/')
        
        else:
            messages.error(request,"COuldn't add a comment")
            
            
            
            
            
    return redirect('/')   




@login_required(login_url="/login")
def delete_comment(request,post_id,comment_id):
    comment=get_object_or_404(Comment,id=comment_id,post_id=post_id,user=request.user)
    
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.", extra_tags="delete_comment")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('/index')





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
def profile_url(request,username):
    user=get_object_or_404(User,username=username)
    
    profile=get_object_or_404(Profile, user=user)
    

    
    
    profile_info={
        'profile_name':profile.user.username,
        'profile_image':base64_to_image(profile.profile_picture) if profile.profile_picture else None
    }
    
    
    context={'profile_info':profile_info}
    

    
    
    return render(request, "profile_url.html",context)







@login_required(login_url="/login")
def send_request(request,username):

    user=request.user
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
    
    if request.method == "POST":

        data = request.POST
        
        unfriend_username = data.get('unfriend')
        

        
        # Get the User instance for the user to unfriend
        try:
            unfriend_user = User.objects.get(username=unfriend_username)
        except User.DoesNotExist:

            return redirect('/friends')
        

        
        # Find and delete the friendship records involving the current user and the unfriend_user
        friendships_to_delete = Friendship.objects.filter(
            (Q(sender=user) & Q(receiver=unfriend_user)) | 
            (Q(sender=unfriend_user) & Q(receiver=user)),
            accepted=True
        )
        

        
        friendships_to_delete.delete()
        

    
    return redirect('/friends')
        
        
            
            
        
        

    

    
    
        
        
    
   
    
    
    
    
    
            
            


    

        
    
    

    
    
        
            
        
        
        
 
    
    

  
    
    
    





def logout_page(request):
    logout(request)
    return redirect('/login')



  

        
        
    

    
    
    
    return redirect('/index')
    
    










    
    
    
    
    
    
    
        
        
 
        
        
        
        
        
        
