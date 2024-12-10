from django.contrib.auth import get_user_model
from django.contrib.auth.models import (AbstractUser, BaseUserManager, Group,
                                        Permission)
from django.db import models
from django.utils.timezone import now


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен для создания пользователя")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    patronymic = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Отчество"
    )
    phone = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    gender_choices = [("M", "Мужской"), ("F", "Женский")]
    gender = models.CharField(max_length=1, choices=gender_choices, verbose_name="Пол")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    email = models.EmailField(unique=True, verbose_name="Email")

    groups = models.ManyToManyField(
        Group, related_name="customuser_groups", blank=True, verbose_name="Группы"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",
        blank=True,
        verbose_name="Разрешения",
    )

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "patronymic",
        "phone",
        "gender",
        "birth_date",
        "address",
    ]
    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    def __str__(self):
        return self.email


User = get_user_model()


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)

    def is_valid(self):
        return now() < self.expires_at
