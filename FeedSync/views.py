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
    
    user=request.user
    all_posts=Posts.objects.filter(user=user)
    
    print(all_posts)
    
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
               
    context={'posts':all_posts,'profile_image_url': profile_image_url}
    
    
    
    
    
    
   
    
    if request.method == "POST":
        print("Form is submiited ")
        data=request.POST
        
        caption=data.get('caption')
        
        print(caption)
        
        trim_caption=caption.strip()
        
        if not trim_caption:
             messages.error(request, "Caption cannot be spaces only.Please enter a caption")
             return redirect("/index")
               
        file=request.FILES.get('image')
        if file:
            image_string=image_to_base64(file)
        else:
            pass  
        
        print(image_string)
        
        
        
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
        
        print("success")
                
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


def feed(request):
    return render("feed.html")


def messenger(request):
    return render(request, "messenger.html")

def friends(request):
    user = request.user
    
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
        'sent_reqs': sent_reqs
    }
    
    return render(request, "friends.html", context)

            
        
        
    
   
    

    
    return render(request, "friends.html",context)


def profile(request):
    user=request.user
    
    all_posts=Posts.objects.filter(user=user)
    
    all_posts=Posts.objects.filter(user=user)
    
    print(all_posts)
    
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
        print("reached..")
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



def like_post(request,post_id):
    
    
    post=get_object_or_404(Posts, id=post_id)
    
    print(post_id)
    
    existing_like = Like.objects.filter(user=request.user, post=post).first()
    
    if existing_like:
        # If like exists, remove it (unlike the post)
        existing_like.delete()
    else:
        # Otherwise, create a new like
        Like.objects.create(user=request.user, post=post)
    
    # Redirect to the post's detail page or another appropriate page
    return redirect('/index', post_id=post_id)
    
    
    






def add_comment(request,post_id):
    print("add comment")
    post=get_object_or_404(Posts , id=post_id)
    
    if request.method=="POST":
        print("reached")
        comment_text = request.POST.get('comment_text')
        print(comment_text)
        if comment_text:
            Comment.objects.create(user=request.user, post=post, content=comment_text)
            messages.success(request, "Comment Added successfully.", extra_tags="add_comment")
            return redirect('/')
        
        else:
            messages.error(request,"COuldn't add a comment")
            
            
            
            
            
    return redirect('/')   





def delete_comment(request,post_id,comment_id):
    comment=get_object_or_404(Comment,id=comment_id,post_id=post_id,user=request.user)
    
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.", extra_tags="delete_comment")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('/index')






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





def profile_url(request,username):
    user=get_object_or_404(User,username=username)
    
    profile=get_object_or_404(Profile, user=user)
    

    
    
    profile_info={
        'profile_name':profile.user.username,
        'profile_image':base64_to_image(profile.profile_picture) if profile.profile_picture else None
    }
    
    
    context={'profile_info':profile_info}
    

    
    
    return render(request, "profile_url.html",context)








def send_request(request,username):
    print("send request reached..")
    print(username)
    user=request.user
    friend_req_receiver=get_object_or_404(User,username=username)
    
    print(user)
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



def accept_request(request):
    
    print("accept request reached..")
    
    if request.method=="POST":
        
        
        sender_name=request.POST.get('sender')
        print(f"Sender:{sender_name}")
        user=request.user
        
        
        if sender_name:
            friend_requests=Friendship.objects.filter(sender__username=sender_name,receiver=user)
            print(friend_requests)
            
            
            for req in friend_requests:
                if not req.accepted:
                    req.accepted = True
                    req.save()
            
    

  
    
    
    # friend_requests = Friendship.objects.filter(receiver=user,sender=sender)
    # print(friend_requests)
    
    # for r in friend_requests:
    #     print(r.id)
    
    # for req in friend_requests:
    #     print(f"Before: Request from {req.sender} to {req.receiver}, accepted: {req.accepted}")
        
    #     # Check if the request is not already accepted
    #     if not req.accepted:
    #         req.accepted = True
    #         req.save()  # Save the change to the database
    #         print(f"After: Request from {req.sender} to {req.receiver}, accepted: {req.accepted}")
    
    return redirect('/friends')
        
        
    
    
        
        
    return redirect('/friends')




def reject_friend_request(request, request_id):
    friendship_request = get_object_or_404(Friendship, id=request_id, receiver=request.user)
    
    if not friendship_request.accepted:
        friendship_request.delete()
    
    return redirect('friend_requests')
    
    
        
        
    
   
    
    
    
    
    
            
            


    

        
    
    

    
    
        
            
        
        
        
 
    
    

  
    
    
    





def logout_page(request):
    logout(request)
    return redirect('/login')



  

        
        
    

    
    
    
    return redirect('/index')
    
    










    
    
    
    
    
    
    
        
        
 
        
        
        
        
        
        
