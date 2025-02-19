from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer,RegisterSerializer,LoginSerializer,ProfileSerializer,EducationSerializer,OtpSerializer
from django.contrib.auth.models import User
from .models import Profile,Education,Otp
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from .emails import send_otp_via_mail
from django.db import transaction

# Create your views here.
class UserApi(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        # print(request.user.email)
        queryset= User.objects.all()
        serializer=UserSerializer(queryset,many=True)
        return Response({
            "status":200,
            "message":"test",
            "success":True,
            "data":serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self,request):
        data=request.data
        serializer=UserSerializer(data=data)

        if not serializer.is_valid():
            return Response({
                "status":400,
                "message":"all data is required",
                "errors":serializer.errors,
                "success":False
            },status=status.HTTP_400_BAD_REQUEST)
        
        print(serializer)
        return Response({
                "status":201,
                "message":"user created successfully",
                "success":True
            },status=status.HTTP_201_CREATED)
    
#register api
class RegisterApi(APIView):

    @transaction.atomic
    def post(self,request):
        data=request.data
        serializer=RegisterSerializer(data=data)

        if not serializer.is_valid():
            return Response({
                "status":400,
                "message":"all data is required",
                "errors":serializer.errors,
                "success":False
            },status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        print(serializer.data)
        user=authenticate(username=serializer.data['username'], password=data['password'])
        token,_=Token.objects.get_or_create(user=user)

        if hasattr(user, 'profile'):
            candidateSerializer=ProfileSerializer(instance=user.profile)
            candidate=candidateSerializer.data
        else:
            candidate=None

        return Response({
            "status":201,
            "message":"user created successfully",
            "success":True,
            "data":{
                "token":str(token),
                "candidate":candidate
            }
        },status=status.HTTP_201_CREATED)

# login api 
class LoginApi(APIView):

    def post(self,request):
        data=request.data
        serializer=LoginSerializer(data=data)

        if not serializer.is_valid():
            return Response({
                "status":400,
                "message":"Enter valid login details",
                "errors":serializer.errors,
                "success":False
            },status=status.HTTP_400_BAD_REQUEST)
        user=authenticate(username=serializer.data['username'],password=serializer.data['password'])
        if not user:
            return Response({
                "status":400,
                "message":"No user found or Invalid Credentials",
                "success":False
            },status=status.HTTP_400_BAD_REQUEST)
        
        token,_=Token.objects.get_or_create(user=user)
        # print("******************")
        # print(token)
        # print("******************")
        # print(request.user) # giving anonymous user as we have not loggedin using login or authenticated using token

        if hasattr(user, 'profile'):
            candidateSerializer=ProfileSerializer(instance=user.profile)
            candidate=candidateSerializer.data
        else:
            candidate=None

        return Response({
            "status":200,
            "message":"Logged in successfull",
            "success":True,
            "data":{
                "token":str(token),
                "candidate":candidate
            }
        },status=status.HTTP_200_OK)
    
# logout api
class LogoutApi(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        try:
            token =Token.objects.get(user=request.user)
            token.delete()
            return Response({
                "status": 200,
                "message": "Logged out successfully",
                "success": True
            }, status=status.HTTP_200_OK)
        except token.DoesNotExist:
            return Response({
                "status": 400,
                "message": "No token found",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

# profile crud api
class ProfileApi(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response({
                "status": 200,
                "message": "Profile found",
                "success": True,
                "data":serializer.data
            }, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Profile not found",
                "success": False,
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self,request):
        try:
            profile=request.user.profile
            serializer=ProfileSerializer(profile,data=request.data)
        except Profile.DoesNotExist:
            serializer=ProfileSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": 400,
                "message": "Invalid profile data",
                "errors": serializer.errors,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save(user=request.user)
        
        return Response({
            "status": 200,
            "message": "Profile created/updated successfully",
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

#education
class EducationApi(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        try:
            profile=request.user.profile
            querySet=Education.objects.filter(profile=profile)
            if not querySet.exists():
                return Response({
                    "status": 404,
                    "message": "No education details found.",
                    "success": False
                }, status=status.HTTP_404_NOT_FOUND)

            serializer=EducationSerializer(querySet,many=True)

            return Response({
                "status": 200,
                "message": "All education data found",
                "success": True,
                "data":serializer.data
            }, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Add profile data first.",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self,request):
        try:
            profile=request.user.profile
            data=request.data
            serializer=EducationSerializer(data=data)

            if not serializer.is_valid():
                return Response({
                    "status": 400,
                    "message": "Invalid education data format.",
                    "success": False,
                    "errors":serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(profile=profile)

            return Response({
                "status": 200,
                "message": "Education details added successfully",
                "success": True,
                "data":serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Profile.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Add profile data first.",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self,request):

        education_id = request.data.get('id')
        if not education_id:
            return Response({
                "status": 400,
                "message": "ID is required",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        prev_education_detail = Education.objects.filter(pk=education_id).first()

        if not prev_education_detail:
            return Response({
                "status": 404,
                "message": "Invalid Id",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)
        print(prev_education_detail)
        print("***********************************")
        serializer=EducationSerializer(prev_education_detail,data=request.data,partial=True)
        if not serializer.is_valid():
            return Response({
                "status": 400,
                "message": "Invalid data format",
                "success": False,
                "errors":serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()

        return Response({
            "status": 200,
            "message": "Education details updated",
            "success": True,
            "data":serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self,request):
        try:
            education_id = request.data.get('id')

            if not education_id:
                return Response({
                    "status": 400,
                    "message": "ID is required",
                    "success": False
                }, status=status.HTTP_400_BAD_REQUEST)

            education_instance = Education.objects.filter(id=education_id).first()

            if not education_instance:
                return Response({
                    "status": 404,
                    "message": "Education record not found",
                    "success": False
                }, status=status.HTTP_404_NOT_FOUND)

            # Delete the education instance
            education_instance.delete()

            return Response({
                "status": 200,
                "message": "Education record deleted successfully",
                "success": True
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": 500,
                "message": "An error occurred while deleting the education record",
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_otp(request):
    try:
        email=request.data.get('email')
        
        if not email:
            return Response({
                "status": 400,
                "message": "Email is required",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        otp_instance,created=Otp.objects.get_or_create(email=email)
        if not created and otp_instance.isActive == True:
            return Response({
                "status": 400,
                "message": "User Alredy Exist Please Log in",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        

        otp=send_otp_via_mail(email)
        # print(otp)

        otp_instance.otp=otp
        otp_instance.save()

        return Response({
            "status": 200,
            "message": "OTP sent successfully",
            "success": True
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": 500,
            "message": "An error occurred while sending the OTP",
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
