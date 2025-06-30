# Project Brief - Bot Twitter Automatisé

## Objectif Principal
Développer un bot Twitter automatisé capable de poster des tweets générés intelligemment avec gestion complète des interactions et statistiques.

## Objectifs Secondaires (priorisés)
1. **Liker automatiquement** tous les replies sous les tweets du bot
2. **Collecter et stocker** les statistiques détaillées (likes, retweets, impressions)
3. **Générer des images** via DALL·E si activé dans la configuration
4. **Respecter les quotas** selon le plan X API (Basic/Pro/Enterprise)
5. **Dashboard temps réel** avec rapports quotidiens

## Architecture Technique
- **Backend**: Python + Tweepy + OpenAI + Supabase
- **Stockage**: Supabase (tables + storage + realtime)
- **Scheduler**: APScheduler pour automation
- **Monitoring**: Real-time tracking + rapports CSV

## Configuration Centralisée
- JSON local + table Supabase configs
- Quotas adaptatifs selon plan X API
- Plages horaires configurables (09:00-21:00)
- Activation/désactivation des images

## Résilience
- Rate limiting automatique (wait_on_rate_limit)
- Retry logic pour tous les calls API
- Logs détaillés et gestion d'erreurs
- Real-time Supabase pour réactivité

## Deliverables
1. Modules Python complets et documentés
2. Configuration example avec tous les plans X API
3. Dockerfile pour deployment
4. Documentation complète d'installation/utilisation 