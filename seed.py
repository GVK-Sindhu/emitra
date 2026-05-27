import os
import django

def seed_db():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from apps.organizations.models import Organization
    
    print("Seeding database...")
    org, created = Organization.objects.get_or_create(
        name="Acme Corporation"
    )
    
    if created:
        print(f"Created tenant Organization: '{org.name}'")
    else:
        print(f"Tenant Organization '{org.name}' already exists.")
        
    print(f"\n==================================================")
    print(f"ORGANIZATION ID: {org.id}")
    print(f"Use this ID in X-Organization-ID request headers.")
    print(f"==================================================\n")

if __name__ == "__main__":
    seed_db()
