from django.core.management.base import BaseCommand
from base.models import Badge

class Command(BaseCommand):
    help = "Seed default badges"

    def handle(self, *args, **options):
        badges = [
            {"name": "Beginner"},
            {"name": "Intermediate"},
            {"name": "Expert"},
            {"name": "Champion"},
            {"name": "Legend"}
        ]
        created = 0
        for b in badges:
            if not Badge.objects.filter(name=b["name"]).exists():
                Badge.objects.create(**b)
                created += 1
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ {created} badge(s) created successfully."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ All badges already exist."))
