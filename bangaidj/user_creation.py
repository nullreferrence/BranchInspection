import os
import django
import sys
import csv
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password

# Add the project base directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the correct settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# Setup Django
django.setup()

# Corrected import path
from bangaidj.audit_workflow.models import User, Branch

with open('audit_workflow_user.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        email = row['email'].strip().lower()

        if not email:
            continue

        password = get_random_string(length=10)
        hashed_password = make_password(password)

        branch_code = int(row['branch_code'])

        branch, _ = Branch.objects.get_or_create(code=branch_code)

        user, created = User.objects.get_or_create(email=email)
        if created:
            user.password = hashed_password
            user.branch = branch
            user.save()
            print(f"Created user: {email}")
        else:
            print(f"User already exists: {email}")
