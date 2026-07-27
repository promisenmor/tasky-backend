from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """custom manager for the user model."""

    use_in_migrations = True

    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        **extra_fields,
    ):
        """create and save a regular user."""

        if not email:
            raise ValueError(_("users must have an email address."))

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        **extra_fields,
    ):
        """create and save a superuser"""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )
