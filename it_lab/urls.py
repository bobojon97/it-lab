"""
URL configuration for it_lab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import include, path, reverse
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

schema_view = get_schema_view(
    openapi.Info(
        title="Документация API",
        default_version="v1",
        description="Документация для всех доступных API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "message": "Добро пожаловать в API",
            "endpoints": {
                "register": request.build_absolute_uri(reverse("register")),
                "login": request.build_absolute_uri(reverse("login")),
                "verify_otp": request.build_absolute_uri(reverse("verify_otp")),
            },
            "documentation": {
                "swagger": request.build_absolute_uri(reverse("schema-swagger-ui")),
                "redoc": request.build_absolute_uri(reverse("schema-redoc")),
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api_root"),
    path("api/", include("api.urls")),
    # Документация
    path(
        "api/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]
