# System Patterns - Bot Twitter Automatisé

## Architecture Système

### Composants Principaux
```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                   (Orchestration)                           │
└─────────────────────────────────────────────────────────────┘
           │
           ├─── config.py ──────── Supabase ──────── JSON
           │
           ├─── twitter_api.py ───── X API v2 (Tweepy)
           │
           ├─── generator.py ────── OpenAI GPT-4 + DALL-E
           │
           ├─── storage.py ──────── Supabase (Tables + Realtime)
           │
           ├─── scheduler.py ────── APScheduler
           │
           └─── stats.py ────────── Analytics + Reporting
```

### Patterns de Design

#### 1. Configuration Pattern
- **Source unique de vérité** : JSON local + Supabase sync
- **Validation à l'initialisation** : Schéma strict pour configs
- **Hot reload** : Changements config sans redémarrage
- **Fallback gracieux** : Valeurs par défaut si Supabase indisponible

#### 2. Rate Limiting Pattern
```python
# Pattern implémenté dans twitter_api.py
@retry(max_attempts=3, backoff=exponential)
def api_call_with_limits():
    # wait_on_rate_limit=True dans Tweepy Client
    # Suivi quotas personnalisé selon plan
```

#### 3. Real-time Event Pattern
```python
# Pattern Supabase realtime
supabase.table('replies').on('INSERT', handle_new_reply).subscribe()
# Déclenchement immédiat des likes
```

#### 4. Factory Pattern
```python
# twitter_api.py
def create_client(config):
    return tweepy.Client(
        consumer_key=config['x_api_key'],
        wait_on_rate_limit=True,
        return_type=dict
    )
```

## Relations entre Composants

### Data Flow
1. **Config** → Tous les modules (singleton pattern)
2. **Scheduler** → Generator → Twitter API → Storage
3. **Storage realtime** → Twitter API (likes)
4. **Twitter API** → Stats → Storage
5. **Stats** → Reporting (daily)

### Error Handling Strategy
```python
# Pattern uniforme dans tous modules
try:
    result = api_call()
    log_success(result)
    return result
except RateLimitError:
    wait_and_retry()
except APIError as e:
    log_error(e)
    notify_admin()
    return None
```

### Dependency Injection
- **Config service** injecté dans tous les modules
- **Logger** centralisé avec contexte par module
- **Database connection** poolée et réutilisée

## Évolutivité

### Extensions Futures
- **Multi-comptes** : Factory pattern prêt pour scaling
- **Plugins** : Interface pour strategies de génération custom
- **Monitoring** : Hooks pour alertes externes (Slack, Discord)
- **A/B Testing** : Framework pour tester différents prompts
- **ML Pipeline** : Intégration future pour modèles custom 