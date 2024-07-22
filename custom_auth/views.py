import os

import jwt
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from config import settings
from custom_auth.models import User
from custom_auth.serializers import RegisterUserSerializer, UserSerializer

class AuthAPIView(APIView):
    #유저 정보 확인
    def get(self,request):
        try:
            access = request.COOKIES['access']
            payload = jwt.decode(access, settings.SECRET_KEY, algorithms=['HS256'])
            pk = payload.get('user_id')
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except(jwt.exceptions.ExpiredSignatureError):
            # 토큰 만료시 갱신
            refresh_token = request.COOKIES.get('refresh', None)
            serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
            try:
                if serializer.is_valid(raise_exception=True):
                    access = serializer.validated_data.get('access', None)
                    refresh = serializer.validated_data.get('refresh', None)
                    payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
                    pk = payload.get('user_id')
                    user = get_object_or_404(User, pk=pk)
                    serializer = UserSerializer(instance=user)
                    res = Response(serializer.data, status=status.HTTP_200_OK)
                    res.set_cookie('access', access)
                    res.set_cookie('refresh', refresh)
                    return res
                raise jwt.exceptions.InvalidTokenError
            except(TokenBackendError, TokenError):
                return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        except(jwt.exceptions.InvalidTokenError):
            # 사용 불가능한 토큰
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        user = authenticate(username=request.data.get("username"), password=request.data.get("password"))

        # 이미 회원가입 된 유저
        if user is not None:
            serializer = UserSerializer(user)
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "login success",
                    "token":{
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            res.set_cookie('access', access_token)
            res.set_cookie('refresh', refresh_token)
            return res
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request):
        response = Response(
            {
                "message": "Logout success"
            }, status=status.HTTP_202_ACCEPTED
        )
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

            res.set_cookie('access', access_token, httponly=True)
            res.set_cookie('refresh', refresh_token, httponly=True)

            return res
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)