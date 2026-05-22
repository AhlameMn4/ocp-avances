# Plateforme Avances Sociales – OCP Group

## Installation rapide (Windows)

### 1. Prérequis
- Python 3.11+
- MySQL 8.0+
- VS Code

### 2. Installation
```bash
cd Desktop
mkdir ocp_avances && cd ocp_avances
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Base de données MySQL
Ouvre MySQL Workbench ou la console MySQL et crée la base :
```sql
CREATE DATABASE ocp_avances_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Ensuite configure ton mot de passe dans `core/settings.py` :
```python
'PASSWORD': 'ton_mot_de_passe_mysql',
```

### 4. Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Charger les agents mock
```bash
python manage.py loaddata agents/fixtures/agents_mock.json
```

### 6. Créer le compte admin
```bash
python manage.py shell
from accounts.models import CustomUser
# Créer le compte admin directement
u = CustomUser.objects.create_superuser(
    username='***',
    email='***@ocp.ma',
    password='***',
    first_name='***',
    last_name='***',
    role='admin',
    actif=True,
    must_change_password=False,
)
print("✅ Compte créé :", u.username, "| rôle :", u.role)
```
Identifiants gestionnaire : `Ahlam` / `Ahlamlove9`

### 7. Lancer le serveur
```bash
python manage.py runserver
```
Accède à : http://localhost:8000

---

## Comptes de test
| Rôle          | Username | Mot de passe   |
|---------------|----------|----------------|
| Admin RH      | admin    | Admin@OCP2025  |
| Gestionnaire  | (créé via l'interface admin) | |

---

## Structure du projet
```
ocp_avances/
├── core/               # Config Django (settings, urls)
├── accounts/           # Auth, rôles, gestionnaires, audit trail
├── agents/             # Modèle Agent (read-only) + API matricule
├── events/             # Gestion des campagnes
├── demandes/           # Saisie, services métier, export Excel
├── dashboard/          # Tableaux de bord admin & gestionnaire
└── templates/          # Tous les templates HTML
```


## Matricules de test
OCP001 → OCP025 (25 agents, 8 services)

## Tâches planifiées (Windows Task Scheduler)

```bash
# Alertes email J-3 avant clôture (quotidien 8h)
python manage.py send_alertes_email

# Fermeture automatique des événements expirés (quotidien minuit)
python manage.py fermer_events_expires
```

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| Saisie standard | Recherche matricule + confirmation en 2 étapes |
| Saisie rapide | Mode clavier uniquement, Enter pour tout, compteurs live |
| Export Excel | Données filtrées, formaté OCP |
| Export PDF | Récapitulatif officiel avec en-tête OCP |
| Pagination | 25 éléments par page dans toutes les listes |
| Statistiques | Page dédiée : évolution mensuelle, comparaisons inter-éditions |
| Historique agent | Toutes les participations d'un agent depuis la création |
| Audit Trail | Journal immuable de toutes les actions |
| Notifications | Alertes en temps réel dans la sidebar |
| Alertes email | J-3 avant clôture par management command |
| Session warning | Avertissement 10 min avant expiration |
| Mode impression | `@media print` optimisé sans sidebar |