# Active Context - Bot Twitter Automatisé

## Focus Actuel
**Phase d'implémentation initiale** - Création du bot complet depuis zéro selon les spécifications utilisateur.

## Travail Récent
- ✅ **Memory Bank créé** : Documentation complète du projet
- ✅ **Architecture définie** : Patterns et composants identifiés
- ✅ **Stack technique validé** : Technologies et dépendances confirmées
- 🔄 **En cours** : Implémentation des modules core

## Prochaines Étapes (Ordre Prioritaire)

### 1. Configuration et Storage (Priorité Haute)
- [ ] `config.py` - Lecture JSON + sync Supabase
- [ ] `storage.py` - Init Supabase + tables + realtime
- [ ] `config.json` - Template avec plans Basic/Pro/Enterprise

### 2. Twitter API Integration (Priorité Haute)  
- [ ] `twitter_api.py` - Client Tweepy + rate limiting
- [ ] Fonctions : post_tweet, like_reply, get_replies, get_metrics
- [ ] Testing : Validation auth et quotas

### 3. Génération de Contenu (Priorité Moyenne)
- [ ] `generator.py` - OpenAI GPT-4 + DALL-E
- [ ] Fonction get_viral() pour analyse trends
- [ ] Templates de prompts optimisés

### 4. Automation et Monitoring (Priorité Moyenne)
- [ ] `scheduler.py` - APScheduler avec quotas adaptatifs
- [ ] `stats.py` - Collecte métriques + rapports
- [ ] Real-time reply listener

### 5. Orchestration et Deployment (Priorité Basse)
- [ ] `main.py` - Point d'entrée principal
- [ ] `requirements.txt` et `Dockerfile`
- [ ] Documentation d'installation

## Décisions Actives

### Architecture
- **Supabase realtime** pour les likes automatiques de replies
- **wait_on_rate_limit=True** dans Tweepy pour gestion automatique
- **APScheduler** plutôt que cron pour flexibilité cross-platform
- **Pydantic** pour validation configs et données

### Configuration Strategy
- **JSON local** comme source principale (versionnable)
- **Supabase** pour sync et hot reload
- **Variables d'env** pour secrets seulement

### Error Handling
- **Tenacity** pour retry logic
- **Loguru** pour logs structurés
- **Graceful degradation** si services externes indisponibles

## Considerations Importantes

### Rate Limiting
- Respecter absolument les quotas selon plan X API
- Tracker utilisation en temps réel dans Supabase
- Alertes proactives avant dépassement

### Quality Control  
- Validation contenu généré avant publication
- Fallback si OpenAI indisponible
- Éviter spam et contenu répétitif

### Extensibilité
- Architecture modulaire pour ajout facile nouvelles features
- Interface plugin pour strategies de génération custom
- Prêt pour multi-comptes et scaling 