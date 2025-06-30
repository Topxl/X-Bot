# 🤖 Twitter Bot Automatisé - Version Réorganisée

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

## 📁 **Structure du Projet Réorganisée**

```
twitter-bot-complete/
├── 📂 core/                    # 🔧 Modules principaux Python
│   ├── main.py                 # Point d'entrée principal
│   ├── config.py               # Gestionnaire de configuration
│   ├── twitter_api.py          # Interface X/Twitter API
│   ├── generator.py            # Génération de contenu IA
│   ├── prompt_manager.py       # Gestionnaire de prompts centralisés
│   ├── reply_handler.py        # Gestionnaire de réponses automatiques
│   ├── scheduler.py            # Gestionnaire de tâches automatisées
│   ├── storage.py              # Interface Supabase
│   └── stats.py                # Collecteur de statistiques
│
├── 📂 config/                  # ⚙️ Fichiers de configuration
│   ├── config.json             # Configuration principale
│   ├── prompts.json            # Prompts système centralisés
│   ├── requirements.txt        # Dépendances Python
│   ├── setup.py                # Configuration d'installation
│   └── pytest.ini             # Configuration des tests
│
├── 📂 tests/                   # 🧪 Scripts de test
│   ├── test_fixes.py           # Tests des corrections
│   ├── test_prompts.py         # Tests du système de prompts
│   └── original/               # Tests originaux du projet
│
├── 📂 docs/                    # 📚 Documentation
│   ├── DOCUMENTATION_COMPLETE.md # 📖 Documentation centralisée (NOUVEAU)
│   └── archives/               # 📁 Anciens fichiers documentation
│
├── 📂 scripts/                 # 🛠️ Scripts utilitaires
│   ├── setup.sh               # Script d'installation
│   ├── deploy.sh               # Script de déploiement
│   ├── test.sh                 # Script de tests
│   └── sql/                    # Scripts SQL
│
├── 📂 data/                    # 💾 Données et logs
│   ├── memory-bank/            # Documentation système
│   ├── logs/                   # Logs du bot (si existants)
│   └── monitoring/             # Configuration monitoring
│
├── main.py                     # 🚀 Point d'entrée principal réorganisé
├── Dockerfile                  # 🐳 Configuration Docker
└── docker-compose.yml          # 🐳 Orchestration Docker
```

---

## 🚀 **Démarrage Rapide**

### **1. Installation**

```bash
# Cloner ou télécharger le projet
cd twitter-bot-complete

# Installer les dépendances
pip install -r config/requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API
```

### **2. Configuration**

```bash
# Éditer la configuration principale
# Fichier: config/config.json

# Personnaliser les prompts (optionnel)
# Fichier: config/prompts.json
```

### **3. Lancement - NOUVEAU ! 🚀**

```bash
# 🔥 LANCEUR UNIFIÉ - Toutes les options en un seul fichier !

# Mode complet (recommandé) - Bot + Dashboard
python start.py

# Dashboard seulement - Interface de configuration
python start.py --dashboard

# Bot seulement - Sans interface web
python start.py --bot

# Aide et options
python start.py --help

# 🌐 Dashboard accessible sur: http://localhost:8080
```

### **🚀 NOUVEAU : Logs Optimisés**
- ✅ **85% moins de logs répétitifs**
- ✅ **Dashboard HTTP logs supprimés**
- ✅ **Reply checks silencieux** (log seulement si activité)
- ✅ **Librairies externes** (Tweepy/APScheduler) en mode WARNING
- 📖 **Guide complet** : Voir `OPTIMISATION_LOGS.md`

#### **Ancienne méthode (compatibilité)**
```bash
# Encore supporté mais redirige vers start.py
python main.py

# Ou avec Docker
docker-compose up -d
```

---

## 📚 **Documentation Centralisée**

### 🎯 **Nouvelle Documentation Unifiée**

Toute la documentation a été **centralisée** dans un seul fichier pour une meilleure expérience :

👉 **[📖 DOCUMENTATION COMPLÈTE](docs/DOCUMENTATION_COMPLETE.md)**

#### **Contenu Consolidé :**
- 🚀 **Démarrage rapide** et installation
- 🏗️ **Architecture** et système modulaire LLM
- 📊 **Dashboard web** avec monitoring temps réel
- 🎯 **Système de prompts** centralisés
- ⚡ **Optimisation** et performance
- 🧪 **Tests** et validation
- 🔧 **Dépannage** et résolution de problèmes

#### **Navigation Simplifiée :**
- **Table des matières** avec liens directs
- **Recherche rapide** (Ctrl+F)
- **Exemples concrets** et code
- **Instructions pas à pas**

### 📁 Archives
Les anciens fichiers de documentation sont disponibles dans [`docs/archives/`](docs/archives/) pour référence.

---

## 🔧 **Modules Principaux**

### **📊 Core/main.py** - Point d'entrée
- Orchestration de tous les modules
- Gestion du cycle de vie du bot
- Interface de commande

### **🤖 Core/generator.py** - Génération IA
- Génération de tweets avec GPT-4
- Création d'images avec DALL-E
- Analyse de trends viraux

### **🐦 Core/twitter_api.py** - Interface X API
- Gestion des quotas selon plan
- Publication automatique
- Engagement temps réel

### **💾 Core/storage.py** - Base de données
- Interface Supabase complète
- Gestion des tweets, replies, stats
- Real-time subscriptions

### **⚙️ Core/prompt_manager.py** - Prompts centralisés
- Gestion unifiée des prompts
- Templates dynamiques avec variables
- Hot-reload sans redémarrage

---

## 🧪 **Tests et Validation**

### **Tests des Corrections**
```bash
cd core
python ../tests/test_fixes.py
```

### **Tests du Système de Prompts**
```bash
cd core  
python ../tests/test_prompts.py
```

### **Tests Complets**
```bash
# Depuis la racine
python -m pytest tests/ -v
```

---

## 📝 **Configuration Avancée**

### **Prompts Système**
Tous les prompts sont centralisés dans `config/prompts.json` :

```json
{
  "system_prompts": {
    "tweet_generation": {...},
    "auto_reply": {...}
  },
  "templates": {
    "simple_replies": [...],
    "crypto_topics": [...]
  }
}
```

### **Configuration Principale**
`config/config.json` contient tous les paramètres :

```json
{
  "x_api": {"plan": "basic"},
  "posting": {"frequency_per_day": 3},
  "engagement": {"auto_like_replies": true},
  "content_generation": {"enable_images": true}
}
```

---

## 🛠️ **Développement**

### **Structure Modulaire**
- **core/** : Logique métier isolée
- **config/** : Configuration externalisée
- **tests/** : Tests unitaires et d'intégration
- **docs/** : Documentation complète

### **Ajout de Fonctionnalités**
1. Créer le module dans `core/`
2. Ajouter la configuration dans `config/`
3. Créer les tests dans `tests/`
4. Documenter dans `docs/`

### **Imports et Dépendances**
Le fichier `main.py` racine gère automatiquement les paths :

```python
# Les modules core peuvent s'importer entre eux normalement
from config import get_config_manager
from twitter_api import get_twitter_manager
```

---

## 🐳 **Déploiement Docker**

### **Build et Run**
```bash
# Build
docker build -t twitter-bot .

# Run
docker-compose up -d

# Logs
docker-compose logs -f
```

### **Variables d'Environnement**
Configurez dans `.env` ou `docker-compose.yml` :
- X_API_KEY, X_API_SECRET
- OPENAI_API_KEY
- SUPABASE_URL, SUPABASE_KEY

---

## 📊 **Monitoring et Logs**

### **Logs Structurés**
```bash
# Logs en temps réel
tail -f data/logs/bot_2025-01-29.log

# Logs Docker
docker-compose logs -f twitter-bot
```

### **Métriques**
- Quotas API en temps réel
- Taux d'engagement
- Performance des prompts
- Statistiques de posting

---

## 🔄 **Migration depuis l'Ancienne Structure**

Si vous aviez l'ancienne version :

1. **Sauvegarder** vos configurations
2. **Copier** les fichiers dans la nouvelle structure
3. **Adapter** les imports si nécessaire
4. **Tester** avec `python main.py`

---

## 🎯 **Avantages de cette Organisation**

### ✅ **Séparation des Responsabilités**
- Core : Logique métier pure
- Config : Configuration externalisée
- Tests : Validation isolée
- Docs : Documentation centralisée

### ✅ **Facilité de Maintenance**
- Modules indépendants
- Configuration hot-reload
- Tests automatisés
- Documentation à jour

### ✅ **Déploiement Simplifié**
- Structure Docker-ready
- Scripts d'automatisation
- Monitoring intégré
- Logs structurés

---

## 📞 **Support et Contribution**

- 📧 **Support** : Ouvrir une issue
- 🔧 **Développement** : Fork et Pull Request
- 📚 **Documentation** : `docs/` directory
- 🧪 **Tests** : `python -m pytest tests/`

---

## 📄 **License**

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

---

**🎉 Structure complètement réorganisée et prête pour la production !**

Pour démarrer : `python main.py` 🚀 