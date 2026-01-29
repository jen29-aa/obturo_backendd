#!/usr/bin/env python
"""
Fix the existing penalty for the test user by clearing the blocked_until time
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obturo_backend.settings')
django.setup()

from django.contrib.auth.models import User
from stations.models import UserPenalty

# Find all users with active blocks
penalties = UserPenalty.objects.filter(blocked_until__isnull=False)

print(f"Found {penalties.count()} user(s) with active blocks:")
for pen in penalties:
    print(f"  - {pen.user.username}: blocked until {pen.blocked_until}, penalty_points: {pen.penalty_points}")
    # Clear the block for testing
    pen.blocked_until = None
    pen.save()
    print(f"    ✓ Cleared block for {pen.user.username}")

print("\nDone!")
