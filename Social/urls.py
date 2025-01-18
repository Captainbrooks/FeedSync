"""
URL configuration for Social project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from FeedSync.views import *


urlpatterns = [
    
     path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('index/', index , name="index"),
   
    path('login/',login_page,name="login_page"),
    path('register/',register_page,name="register_page"),
    

    
    path('messenger/', messenger, name="messenger"),
  
    
    path('profile/',profile,name="profile"),
    path('friends/',friends,name="friends"),
    path('like/<int:post_id>/', like_post, name='like_post'),
  
    path('post/<int:post_id>/add_comment/',add_comment, name='add_comment'),
    path('post/<int:post_id>/<int:comment_id>/delete_comment/',delete_comment, name='delete_comment'),
    path('updatePost/<int:post_id>',updatePost,name="updatePost"),
    path('deletePost/<int:post_id>',deletePost,name="deletePost"),
    path('search_friends/',search_friends,name="search_friends"),
    path('profile/<str:username>/',profile_url,name="profile_url"),
    path('send_request/<str:username>/', send_request, name='send_request'),
    path('accept_request/', accept_request, name='accept_request'),
    path('reject_request/', reject_request, name='reject_request'),
    path('cancel_request/', cancel_request, name='cancel_request'),
    path('unfriend/', unfriend, name='unfriend'),
    path('logout/',logout_page,name="logout_page"),
    path("deleteprofile/", deleteprofile, name="deleteprofile"),
    path("clear_notification/",clear_notification,name="clear_notification"),
    path("search_messenger_friend",search_messenger_friend,name="search_messenger_friend"),
    path("__reload__/", include("django_browser_reload.urls")),

   
]
