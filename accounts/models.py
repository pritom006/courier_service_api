from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with email as the unique identifier"""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_role', User.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model that uses email as the unique identifier"""
    # User roles
    CUSTOMER = 'customer'
    COURIER = 'courier'
    ADMIN = 'admin'
    
    ROLE_CHOICES = (
        (CUSTOMER, 'Customer'),
        (COURIER, 'Courier Staff'),
        (ADMIN, 'Admin/Manager'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    @property
    def is_customer(self):
        return self.user_role == self.CUSTOMER
    
    @property
    def is_courier(self):
        return self.user_role == self.COURIER
    
    @property
    def is_admin(self):
        return self.user_role == self.ADMIN