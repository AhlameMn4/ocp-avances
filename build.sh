#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from accounts.models import CustomUser

if not CustomUser.objects.filter(username='admin').exists():
    CustomUser.objects.create_superuser(
        username='admin',
        email='admin@ocp.ma',
        password='Admin@OCP2025',
        first_name='Administrateur',
        last_name='RH',
        role='admin',
        actif=True,
        must_change_password=False
    )
    print('Admin créé')
else:
    print('Admin existe déjà')
"