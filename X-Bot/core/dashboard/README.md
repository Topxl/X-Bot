# 📊 Dashboard Twitter Bot v2.0

Dashboard web moderne et modulaire pour la configuration et le monitoring du bot Twitter.

## 🚀 Démarrage Rapide

```bash
# Méthode recommandée
python dashboard/start.py

# Avec options personnalisées
python dashboard/start.py --host 0.0.0.0 --port 9000 --debug

# Ou directement depuis le module
python -m dashboard
```

## 📁 Structure Modulaire

```
dashboard/
├── __init__.py          # Point d'entrée du module
├── config.py            # Configuration du dashboard
├── server.py            # Serveur FastAPI principal
├── routes.py            # Routes API (métriques, configuration)
├── templates.py         # Interface HTML/CSS/JS
├── start.py            # Script de démarrage
└── README.md           # Documentation
```

## ✨ Fonctionnalités

### 🎯 Vue d'ensemble
- **Métriques en temps réel** : Status, uptime, tweets/likes du jour
- **Monitoring continu** : Actualisation automatique toutes les 30s
- **Indicateurs visuels** : Status colorés selon l'état du bot

### ⚙️ Configuration Live
- **Réponses automatiques** : Enable/disable, limites, intervalles
- **Planning de publication** : Horaires, fréquence, fuseau horaire
- **Modèles IA** : Provider, température, tokens, etc.
- **Sauvegarde instantanée** : Changements appliqués sans redémarrage

### 📱 Interface Moderne
- **Design responsive** : Mobile et desktop
- **Thème sombre** : Interface élégante
- **Navigation par onglets** : Organisation claire
- **Notifications** : Feedback utilisateur en temps réel

## 🔌 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Interface web principale |
| `/health` | GET | Health check |
| `/api/metrics` | GET | Métriques du bot |
| `/api/logs` | GET | Logs récents |
| `/api/config` | GET | Configuration actuelle |
| `/api/config/auto-reply` | POST | Mise à jour réponses auto |
| `/api/config/posting` | POST | Mise à jour publication |
| `/api/config/llm` | POST | Mise à jour IA |

## 🛠️ Installation

### Dépendances requises
```bash
pip install fastapi uvicorn loguru
```

### Vérification
```bash
# Test rapide
curl http://localhost:8080/health

# Interface web
curl http://localhost:8080/
```

## 🔧 Configuration

### Options de démarrage
```python
from dashboard import DashboardConfig, start_dashboard

config = DashboardConfig(
    host="0.0.0.0",
    port=8080,
    debug=False,
    title="Mon Bot Dashboard",
    auto_refresh_interval=30  # secondes
)

start_dashboard(host=config.host, port=config.port)
```

### Variables d'environnement
- `DASHBOARD_HOST` : Adresse d'écoute (default: 0.0.0.0)
- `DASHBOARD_PORT` : Port d'écoute (default: 8080)
- `DASHBOARD_DEBUG` : Mode debug (default: False)

## 🎨 Thème

Le dashboard utilise un thème sombre moderne avec :
- **Couleurs** : Palette cohérente bleu/gris
- **Typography** : Segoe UI, sans-serif
- **Layout** : CSS Grid et Flexbox
- **Responsive** : Breakpoints mobiles

## 🔄 Migration depuis l'ancien dashboard

L'ancien `core/dashboard.py` est maintenant **DEPRECATED**. 

### Changements
- ✅ Structure modulaire claire
- ✅ Code plus maintenable
- ✅ Gestion d'erreur améliorée
- ✅ Interface plus moderne
- ✅ Configuration plus flexible

### Script de transition
```bash
# Ancien (deprecated)
python core/start_dashboard.py

# Nouveau (recommandé)  
python dashboard/start.py
```

## 🐛 Debugging

### Mode Debug
```bash
python dashboard/start.py --debug
```

### Logs
```bash
# Dans l'interface web : onglet "Logs"
# Ou directement : /api/logs
curl http://localhost:8080/api/logs
```

### Common Issues

**ImportError FastAPI**
```bash
pip install fastapi uvicorn
```

**Port déjà utilisé**
```bash
python dashboard/start.py --port 8081
```

**Config bot non trouvée**
- Vérifiez que `config/config.json` existe
- Vérifiez les permissions de lecture

## 📈 Performance

- **Démarrage** : < 2 secondes
- **Mémoire** : ~50MB RAM
- **CPU** : Négligeable en idle
- **Réseau** : API REST légère

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Modifier dans `dashboard/`
4. Tester avec `python dashboard/start.py`
5. Submit PR

## 📄 License

Même licence que le projet principal. 