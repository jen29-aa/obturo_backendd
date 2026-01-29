"""
Script to make a user a staff member (admin)
Run this with: python make_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obturo_backend.settings')
django.setup()

from django.contrib.auth.models import User

# Get username
username = input("Enter username to make admin: ")

try:
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ {username} is now an admin/staff user!")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    print("\nLog out and log back in to see the Admin Dashboard link in sidebar.")
except User.DoesNotExist:
    print(f"❌ User '{username}' not found!")
    print("\nAvailable users:")
    for u in User.objects.all():
        print(f"  - {u.username} (staff: {u.is_staff})")
