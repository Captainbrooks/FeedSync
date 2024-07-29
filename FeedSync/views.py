from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import Posts, Profile, Reactions
import base64
from django.contrib import messages
from django.contrib.auth.models import User


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
    
    
    
    image=Posts.objects.filter(user=user)
    
    for post in all_posts:
        if post.image:
            post.image_url = f"data:image/png;base64,{post.image}"
            
            
            
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
    return render(request, "friends.html")


def profile(request):
    user = request.user
    
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
    
    context = {'profile_image_url': profile_image_url}
    return render(request, "profile.html", context)






@login_required(login_url="/login")
def add_comment(request, post_id):
    if request.method == "POST":
        data=request.POST
        print("comment is being added..")
        print(post_id)
        comment_text = data.get('comment_text')
        print(comment_text)
        if comment_text:
            post = Posts.objects.get(id=post_id)
            user = request.user
            Reactions.objects.create(
                user=user,
                post=post,
                reaction_type=Reactions.COMMENT,
                comment_text=comment_text
            )
            print("Comment is added in the database")
            messages.success(request, "Comment added successfully.")
        else:
            messages.error(request, "Comment cannot be empty.")
    return redirect('/index')
    





def logout_page(request):
    logout(request)
    return redirect('/login')









    
    
    
    
    
    
    
        
        
 
        
        
        
        
        
        
