from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

CustomUser = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "patronymic",
            "phone",
            "email",
            "password",
            "confirm_password",
            "gender",
            "birth_date",
            "address",
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise AuthenticationFailed("Неверный email или пароль.")
        if not user.is_active:
            raise AuthenticationFailed("Пользователь неактивен.")

        attrs["user"] = user
        return attrs
