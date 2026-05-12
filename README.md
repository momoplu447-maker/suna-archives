# 🏜 Suna Archives — Ousen Zafura

Site de rapports de mission dans l'univers Naruto/Suna.
Backend Python (Flask) + Base de données SQLite.

---

## Installation

### Prérequis
- Python 3.9 ou supérieur

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Lancer le serveur

```bash
python3 server.py
```

Le serveur démarre sur **http://localhost:5000**

---

## Accès

| Page | URL |
|------|-----|
| Site public (lecture) | http://localhost:5000 |
| Administration (écriture) | http://localhost:5000/admin |
| API REST | http://localhost:5000/api/reports |

---

## Structure du projet

```
suna-archives/
├── server.py          ← Serveur Flask + SQLite
├── requirements.txt   ← Dépendances Python
├── suna.db            ← Base de données (créée automatiquement)
├── uploads/           ← Images uploadées
└── public/
    ├── index.html     ← Site public
    └── admin.html     ← Panneau d'administration
```

---

## API REST

### Rapports
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | /api/reports | Liste tous les rapports |
| POST | /api/reports | Créer un rapport |
| GET | /api/reports/:id | Lire un rapport |
| PUT | /api/reports/:id | Modifier un rapport |
| DELETE | /api/reports/:id | Supprimer un rapport |

### Image personnage
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | /api/char-image | Récupérer l'URL de l'image |
| POST | /api/char-image | Uploader une nouvelle image |

### Exemple POST /api/reports
```json
{
  "number": "002",
  "title": "Neutralisation de la cellule Akatsuki",
  "rank": "S",
  "date_mission": "An 15 · 6ème mois",
  "duration": "5 jours",
  "lieu": "Forêt de l'Ouest",
  "statut": "Succès",
  "body": "Corps du rapport..."
}
```

---

## Déploiement (optionnel)

Pour rendre le site accessible depuis internet, utiliser un service comme
**Railway**, **Render**, ou **PythonAnywhere** (gratuits).

Sur Railway :
```bash
# Ajouter un Procfile
echo "web: python server.py" > Procfile
```

Penser à changer `host='0.0.0.0'` et utiliser la variable d'env PORT :
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```
