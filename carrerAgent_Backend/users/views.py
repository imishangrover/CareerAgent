from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "message": "You are authenticated!"
        })

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=400)

        user.set_password(new_password)
        user.save()

        # Keep the user logged in
        update_session_auth_hash(request, user)

        return Response({"message": "Password changed successfully"})
    
class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "User deleted successfully"})

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        new_username = request.data.get("username")
        new_email = request.data.get("email")

        # Check username uniqueness
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                return Response({"error": "Username already taken"}, status=400)
            user.username = new_username

        # Check email uniqueness
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exists():
                return Response({"error": "Email already taken"}, status=400)
            user.email = new_email

        user.save()

        return Response({"message": "Profile updated successfully"})