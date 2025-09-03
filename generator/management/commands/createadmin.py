from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create admin user'
    
    def handle(self, *args, **options):
        username = 'dourvas'
        email = 'dourvas@gmail.com'
        password = 'Lorenjo7!'  # Άλλαξε αυτό με δικό σου κωδικό!
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created!'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user "{username}" already exists.'))