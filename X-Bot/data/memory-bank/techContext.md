# Tech Context - Bot Twitter Automatisé

## Stack Technique

### Technologies Principales
- **Python 3.11+** : Runtime principal
- **Tweepy 4.14+** : Client officiel X API v2
- **OpenAI 1.3+** : GPT-4 + DALL-E intégration
- **Supabase-py 2.0+** : Database + Storage + Realtime
- **APScheduler 3.10+** : Task scheduling
- **Pydantic 2.0+** : Validation et sérialisation

### Dépendances Complètes
```python
# requirements.txt
tweepy>=4.14.0
openai>=1.3.0
supabase>=2.0.0
apscheduler>=3.10.0
pydantic>=2.0.0
python-dotenv>=1.0.0
loguru>=0.7.0
tenacity>=8.2.0
requests>=2.31.0
Pillow>=10.0.0
pandas>=2.0.0
```

### Configuration Environnement

#### Variables d'environnement (.env)
```bash
# X API Credentials
X_API_KEY="your_api_key"
X_API_SECRET="your_api_secret"
X_ACCESS_TOKEN="your_access_token"
X_ACCESS_TOKEN_SECRET="your_access_token_secret"
X_BEARER_TOKEN="your_bearer_token"

# OpenAI
OPENAI_API_KEY="your_openai_key"

# Supabase
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_anon_key"

# Optional
LOG_LEVEL="INFO"
ENVIRONMENT="production"
```

#### Structure Supabase

##### Tables
```sql
-- configs table
CREATE TABLE configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR UNIQUE NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- tweets table
CREATE TABLE tweets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tweet_id VARCHAR UNIQUE NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    engagement JSONB DEFAULT '{}'::jsonb
);

-- replies table  
CREATE TABLE replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_id VARCHAR UNIQUE NOT NULL,
    original_tweet_id VARCHAR NOT NULL,
    author_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    liked BOOLEAN DEFAULT FALSE
);

-- stats table
CREATE TABLE stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tweet_id VARCHAR NOT NULL,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### Storage Buckets
```sql
-- Images générées par DALL-E
INSERT INTO storage.buckets (id, name, public) 
VALUES ('generated-images', 'generated-images', true);
```

## Setup Développement

### Installation locale
```bash
# Clone et setup
git clone <repo>
cd bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés

# Test
python -m pytest tests/
```

### Docker Setup
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Contraintes Techniques

### Rate Limits X API
- **Basic Plan** : 1,500 posts/mois, 50,000 lectures/mois
- **Pro Plan** : 50,000 posts/mois, 2M lectures/mois  
- **Enterprise** : Négocié, généralement illimité

### Performance Targets
- **Latence likes** : < 5 secondes après détection reply
- **Génération tweet** : < 30 secondes (avec image)
- **Collecte stats** : Batch toutes les heures
- **Uptime** : 99.5% (tolérance redémarrages)

### Monitoring
- **Logs structurés** : JSON avec contexte complet
- **Métriques** : Quotas utilisés, erreurs, latences
- **Alertes** : Rate limit proche, erreurs critiques
- **Health checks** : Endpoint /health pour monitoring externe 