from django.urls import path
from visitors.views import UserApi,RegisterApi,LoginApi,LogoutApi,ProfileApi,EducationApi,send_otp
from rankpredictor.views import AnswerSheetAPi,SlotsApi,predictRank,test


urlpatterns = [
    path('user/',UserApi.as_view()),
    path('user/verify/',send_otp),
    path('user/register/',RegisterApi.as_view()),
    path('user/login/',LoginApi.as_view()),
    path('user/logout/',LogoutApi.as_view()),
    path('user/profile/',ProfileApi.as_view()),
    path('user/education/',EducationApi.as_view()),

    path('rankpredictor/slots/',SlotsApi.as_view()),
    path('rankpredictor/answersheet/',AnswerSheetAPi.as_view()),
    path('rankpredictor/getrank/',predictRank),
    path('test/',test),
]
