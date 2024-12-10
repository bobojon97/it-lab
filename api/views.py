import logging
import random
from datetime import timedelta

from django.core.mail import send_mail
from django.utils.timezone import now
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .serializers import LoginSerializer, RegistrationSerializer

logger = logging.getLogger("login")


class RegistrationView(CreateAPIView):
    serializer_class = RegistrationSerializer

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя.",
        request_body=RegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Пользователь успешно зарегистрирован.",
                examples={
                    "application/json": {
                        "message": "Пользователь успешно зарегистрирован!"
                    }
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации данных.",
                examples={
                    "application/json": {
                        "email": ["Пользователь с таким email уже существует."]
                    }
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Пользователь успешно зарегистрирован!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        operation_description="Авторизация пользователя: принимает email и пароль, возвращает временный JWT токен и отправляет OTP на email.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Успешная авторизация. OTP отправлен на email.",
                examples={
                    "application/json": {
                        "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...",
                        "message": "OTP отправлен на ваш email",
                    }
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации данных.",
                examples={
                    "application/json": {
                        "email": ["Это поле обязательно."],
                        "password": ["Это поле обязательно."],
                    }
                },
            ),
            401: openapi.Response(
                description="Неверный логин или пароль.",
                examples={"application/json": {"detail": "Неверный логин или пароль."}},
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        email = user.email

        temp_token = RefreshToken.for_user(user).access_token
        temp_token.set_exp(lifetime=timedelta(minutes=2))  # Токен действует 2 минуты

        otp_code = random.randint(100000, 999999)
        OTP.objects.create(
            user=user, code=otp_code, expires_at=now() + timedelta(minutes=2)
        )

        logger.info(f"Успешная попытка входа | Email: {email} | Время: {now()}")

        # Отправка OTP на email
        send_mail(
            "Ваш OTP код",
            f"Ваш одноразовый пароль: {otp_code}",
            None,
            [email],
            fail_silently=False,
        )

        return Response(
            {"temp_token": str(temp_token), "message": "OTP отправлен на ваш email"},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    @swagger_auto_schema(
        operation_description="Подтверждение OTP-кода: проверяет временный токен и OTP-код. Возвращает полный JWT токен при успешной верификации.",
        manual_parameters=[
            openapi.Parameter(
                "Authorization",
                openapi.IN_HEADER,
                description="Временный токен в формате Bearer <temp_token>",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "otp": openapi.Schema(
                    type=openapi.TYPE_STRING, description="6-значный OTP-код"
                ),
            },
            required=["otp"],
        ),
        responses={
            200: openapi.Response(
                description="Успешное подтверждение OTP.",
                examples={
                    "application/json": {
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...",
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...",
                        "message": "Авторизация успешна!",
                    }
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации данных.",
                examples={"application/json": {"otp": ["Это поле обязательно."]}},
            ),
            401: openapi.Response(
                description="Ошибка токена или неверный OTP.",
                examples={
                    "application/json": {
                        "detail": "Требуется временный токен в формате: Bearer <token>."
                    }
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        temp_token = request.headers.get("Authorization")
        otp_code = request.data.get("otp")

        if not temp_token or not temp_token.startswith("Bearer "):
            logger.info(
                f"Ошибка подтверждения OTP: отсутствует или некорректный токен | Время: {now()}"
            )
            raise ValidationError(
                "Требуется временный токен в формате: Bearer <token>."
            )

        temp_token = temp_token.split(" ")[1]

        user = request.user
        email = user.email

        try:
            otp = OTP.objects.get(user=user, code=otp_code)
        except OTP.DoesNotExist:
            logger.info(
                f"Ошибка подтверждения OTP: неверный код | Email: {email} | Время: {now()}"
            )
            raise ValidationError("Неверный OTP.")

        if not otp.is_valid():
            otp.delete()
            logger.info(
                f"Ошибка подтверждения OTP: срок действия истек | Email: {email} | Время: {now()}"
            )
            raise ValidationError("OTP истек.")

        if otp.attempts >= 3:
            otp.delete()
            logger.info(
                f"Ошибка подтверждения OTP: превышено количество попыток | Email: {email} | Время: {now()}"
            )
            raise ValidationError("Превышено количество попыток ввода OTP.")

        if otp.code != otp_code:
            otp.attempts += 1
            otp.save()
            logger.info(
                f"Ошибка подтверждения OTP: неверный код | Email: {email} | Время: {now()}"
            )
            raise ValidationError("Неверный OTP.")

        otp.delete()

        logger.info(f"Успешное подтверждение OTP | Email: {email} | Время: {now()}")

        refresh = RefreshToken.for_user(user)
        refresh["email"] = email
        refresh["full_name"] = f"{user.first_name} {user.last_name}"

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Авторизация успешна!",
            },
            status=200,
        )
