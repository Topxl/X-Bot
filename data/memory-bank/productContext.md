# Product Context - Bot Twitter Automatisé

## Pourquoi ce projet existe

### Problèmes résolus
1. **Automatisation intelligente** : Publier du contenu viral de qualité sans intervention manuelle
2. **Engagement optimisé** : Répondre instantanément aux interactions (likes sur replies)
3. **Analytics centralisées** : Collecter toutes les métriques en un endroit avec historique
4. **Respect des quotas** : Gérer automatiquement les limites selon le plan X API
5. **Scalabilité** : Architecture prête pour multi-comptes et plans enterprise

### Expérience utilisateur cible
- **Configuration simple** : Un seul fichier JSON + interface Supabase
- **Monitoring temps réel** : Dashboard live des performances
- **Rapports automatiques** : Statistiques quotidiennes par email/CSV
- **Contrôle granulaire** : Activation/désactivation par fonctionnalité
- **Transparence** : Logs détaillés de toutes les actions

## Comment ça doit fonctionner

### Workflow principal
1. **Analyse virale** : Scanner les trends Twitter pour inspiration
2. **Génération IA** : Prompt GPT-4 pour créer tweets optimisés
3. **Post automatique** : Publication selon planning + quota
4. **Engagement temps réel** : Like automatique des replies via Supabase realtime
5. **Collecte métriques** : Tracking continu des performances
6. **Reporting** : Synthèse quotidienne des résultats

### Cas d'usage
- **Content creators** : Maintenir présence Twitter automatiquement
- **Marques** : Engagement constant avec communauté
- **Agences** : Gestion multi-clients avec quotas différenciés
- **Recherche** : Analytics approfondies sur performance contenu

### Contraintes respectées
- **Rate limits X API** : Jamais dépasser les quotas selon plan
- **Qualité contenu** : Pas de spam, génération contextuelle
- **Éthique** : Transparence sur automation, respect communauté
- **Performance** : Réactivité < 5s pour likes, posts en temps réel 