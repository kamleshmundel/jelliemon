from django.core.management.base import BaseCommand
from base.models import AppUser
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = "Seed default admin user"

    def handle(self, *args, **options):
        email = "admin@example.com"
        if not AppUser.objects.filter(email=email).exists():
            AppUser.objects.create(
                name="Admin",
                email=email,
                password=make_password("Admin@123"),
                is_verified=True,
                role=1
            )
            self.stdout.write(self.style.SUCCESS("✅ Default admin user created successfully."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Admin user already exists."))
