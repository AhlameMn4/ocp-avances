#!/usr/bin/env bash
set -o errexit

echo "==> Installation des dépendances..."
pip install -r requirements.txt

echo "==> Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

echo "==> Application des migrations..."
python manage.py migrate

echo "==> Création admin (si inexistant)..."
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
        must_change_password=False,
    )
    print('Admin créé')
else:
    print('Admin existe déjà')
"

echo "==> Chargement des agents mock..."
python manage.py shell -c "
from agents.models import Agent
if Agent.objects.count() == 0:
    from django.core.management import call_command
    call_command('loaddata', 'agents/fixtures/agents_mock.json')
    print('Agents chargés')
else:
    print(f'{Agent.objects.count()} agents déjà présents')
"