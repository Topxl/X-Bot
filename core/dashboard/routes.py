"""
Routes API du Dashboard
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

try:
    from fastapi import FastAPI, Request
except ImportError:
    FastAPI = None
    Request = None

from loguru import logger
from .config import DashboardConfig


@dataclass
class BotMetrics:
    """Métriques du bot"""
    status: str
    uptime: str
    tweets_today: int
    likes_today: int
    replies_today: int
    quota_usage: Dict[str, Any]
    last_tweet: Dict[str, Any] = None
    errors_count: int = 0


def setup_routes(app: FastAPI, bot_managers: dict, start_time: datetime, config: DashboardConfig):
    """Configure toutes les routes API"""
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds(),
            "version": "2.0.0"
        }
    
    @app.get("/api/metrics")
    async def get_metrics():
        """Collecte des métriques du bot"""
        try:
            metrics = await collect_bot_metrics(bot_managers, start_time)
            return {"success": True, "data": asdict(metrics)}
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/logs")
    async def get_recent_logs(limit: int = None):
        """Récupération des logs récents"""
        try:
            limit = limit or config.log_lines_limit
            logs = get_recent_log_entries(limit)
            return {"success": True, "data": logs}
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/config")
    async def get_config():
        """Récupération de la configuration bot"""
        try:
            # Charger config.json
            config_data = get_config_fallback()
            
            # Charger prompts.json
            prompts_data = get_prompts_fallback()
            
            return {
                "success": True, 
                "data": {
                    "config": config_data,
                    "prompts": prompts_data
                }
            }
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/config/auto-reply")
    async def update_auto_reply_config(request: Request):
        """Mise à jour configuration auto-reply"""
        try:
            config_manager = bot_managers.get("config_manager")
            request_data = await request.json()
            result = update_bot_config_section("engagement", request_data, config_manager)
            return result
            
        except Exception as e:
            logger.error(f"Error updating auto-reply config: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/config/posting")
    async def update_posting_config(request: Request):
        """Mise à jour configuration posting"""
        try:
            config_manager = bot_managers.get("config_manager")
            request_data = await request.json()
            result = update_bot_config_section("posting", request_data, config_manager)
            return result
            
        except Exception as e:
            logger.error(f"Error updating posting config: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/config/llm")
    async def update_llm_config(request: Request):
        """Mise à jour configuration LLM"""
        try:
            config_manager = bot_managers.get("config_manager")
            request_data = await request.json()
            result = update_bot_config_section("content_generation", request_data, config_manager)
            return result
            
        except Exception as e:
            logger.error(f"Error updating LLM config: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/config/save")
    async def save_full_config(request: Request):
        """Sauvegarde la configuration complète"""
        try:
            request_data = await request.json()
            
            # Sauvegarder config.json
            if "config" in request_data:
                config_paths = [
                    Path("../../config/config.json"),
                    Path("../config/config.json"),
                    Path("config/config.json"),
                ]
                
                saved = False
                for config_path in config_paths:
                    try:
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(request_data["config"], f, indent=2, ensure_ascii=False)
                        saved = True
                        break
                    except Exception as e:
                        logger.debug(f"Failed to save to {config_path}: {e}")
                
                if not saved:
                    return {"success": False, "error": "Could not save config.json"}
            
            # Sauvegarder prompts.json
            if "prompts" in request_data:
                prompts_paths = [
                    Path("../../config/prompts.json"),
                    Path("../config/prompts.json"),
                    Path("config/prompts.json"),
                ]
                
                saved = False
                for prompts_path in prompts_paths:
                    try:
                        prompts_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(prompts_path, 'w', encoding='utf-8') as f:
                            json.dump(request_data["prompts"], f, indent=2, ensure_ascii=False)
                        saved = True
                        break
                    except Exception as e:
                        logger.debug(f"Failed to save to {prompts_path}: {e}")
                
                if not saved:
                    return {"success": False, "error": "Could not save prompts.json"}
            
            return {"success": True, "message": "Configuration sauvegardée avec succès"}
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/stats/top-tweets")
    async def get_top_tweets(limit: int = 10, days: int = 30):
        """Récupération des tweets les plus performants"""
        try:
            storage_manager = bot_managers.get("storage_manager")
            if not storage_manager:
                return {"success": False, "error": "Storage manager not available"}
            
            top_tweets = storage_manager.get_top_performing_tweets(limit=limit, days=days)
            return {"success": True, "data": top_tweets}
            
        except Exception as e:
            logger.error(f"Error getting top tweets: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/stats/performance-overview")
    async def get_performance_overview(days: int = 7):
        """Récupération de l'aperçu des performances"""
        try:
            storage_manager = bot_managers.get("storage_manager")
            if not storage_manager:
                return {"success": False, "error": "Storage manager not available"}
            
            overview = storage_manager.get_tweet_performance_overview(days=days)
            return {"success": True, "data": overview}
            
        except Exception as e:
            logger.error(f"Error getting performance overview: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/stats/collect-now")
    async def trigger_stats_collection():
        """Déclencher manuellement la collecte de stats"""
        try:
            scheduler = bot_managers.get("scheduler")
            if not scheduler:
                return {"success": False, "error": "Scheduler not available"}
            
            # Déclencher le job de collecte de stats
            success = scheduler.run_job_now("collect_stats")
            
            if success:
                return {"success": True, "message": "Collecte de stats déclenchée avec succès"}
            else:
                return {"success": False, "error": "Échec du déclenchement de la collecte"}
                
        except Exception as e:
            logger.error(f"Error triggering stats collection: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/test/generate-tweet")
    async def test_tweet_generation(request: Request):
        """Teste la génération de tweets par type"""
        try:
            data = await request.json()
            tweet_type = data.get("type", "powerful_statement")
            
            # Obtenir le générateur de contenu
            from core.generator import get_content_generator
            generator = get_content_generator()
            
            # Générer un tweet de test
            content = generator.generate_tweet_content(tweet_type=tweet_type)
            
            if content:
                # Obtenir les informations du type
                type_config = generator.get_tweet_type_config(tweet_type)
                
                return {
                    "success": True,
                    "data": {
                        "content": content,
                        "type": tweet_type,
                        "type_name": type_config.get("name", tweet_type),
                        "type_description": type_config.get("description", ""),
                        "length": len(content),
                        "max_tokens": type_config.get("max_tokens", 150),
                        "temperature": type_config.get("temperature", 0.7)
                    }
                }
            else:
                return {"success": False, "error": "Échec de la génération de contenu"}
                
        except Exception as e:
            logger.error(f"Error testing tweet generation: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/test/tweet-types")
    async def get_tweet_types_info():
        """Récupère les informations sur les types de tweets configurés"""
        try:
            from core.generator import get_content_generator
            generator = get_content_generator()
            
            # Obtenir la configuration actuelle
            config_manager = bot_managers.get("config_manager")
            if not config_manager:
                return {"success": False, "error": "Configuration non disponible"}
            
            config = config_manager.get_config()
            
            # Gérer les deux formats de configuration (dict ou objet)
            content_gen = config.content_generation
            if hasattr(content_gen, 'tweet_types'):
                tweet_types_config = content_gen.tweet_types
            else:
                tweet_types_config = getattr(content_gen, 'tweet_types', {})
            
            types_info = []
            for type_key in ["powerful_statement", "educational_post", "personal_story"]:
                type_config = generator.get_tweet_type_config(type_key)
                types_info.append({
                    "key": type_key,
                    "name": type_config.get("name", type_key),
                    "description": type_config.get("description", ""),
                    "max_tokens": type_config.get("max_tokens", 150),
                    "temperature": type_config.get("temperature", 0.7),
                    "enabled": type_config.get("enabled", True)
                })
            
            # Extraire les valeurs selon le format
            if isinstance(tweet_types_config, dict):
                enabled = tweet_types_config.get("enabled", False)
                rotation_pattern = tweet_types_config.get("rotation_pattern", [])
                fallback_type = tweet_types_config.get("fallback_type", "powerful_statement")
            else:
                enabled = getattr(tweet_types_config, 'enabled', False)
                rotation_pattern = getattr(tweet_types_config, 'rotation_pattern', [])
                fallback_type = getattr(tweet_types_config, 'fallback_type', "powerful_statement")
            
            return {
                "success": True,
                "data": {
                    "enabled": enabled,
                    "rotation_pattern": rotation_pattern,
                    "fallback_type": fallback_type,
                    "types": types_info
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tweet types info: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/viral-tweets")
    async def get_viral_tweets(limit: int = 10):
        """Récupère les tweets viraux pour inspiration"""
        try:
            from core.generator import get_content_generator
            generator = get_content_generator()
            
            # Obtenir les tweets viraux
            viral_tweets = generator.get_viral_inspiration(limit=limit)
            
            if viral_tweets:
                # Enrichir avec des métadonnées utiles
                enriched_tweets = []
                for tweet in viral_tweets:
                    enriched_tweet = {
                        "text": tweet.get("text", ""),
                        "metrics": tweet.get("metrics", {}),
                        "virality_score": tweet.get("virality_score", 0),
                        "topics": tweet.get("topics", []),
                        "style": tweet.get("style", {}),
                        "length": len(tweet.get("text", "")),
                        "has_hashtags": "#" in tweet.get("text", ""),
                        "has_mentions": "@" in tweet.get("text", ""),
                        "has_emoji": any(ord(char) > 127 for char in tweet.get("text", "")),
                        "estimated_engagement": tweet.get("metrics", {}).get("engagement_rate", 0),
                        "collection_time": datetime.utcnow().isoformat()
                    }
                    enriched_tweets.append(enriched_tweet)
                
                return {
                    "success": True,
                    "data": {
                        "tweets": enriched_tweets,
                        "total_found": len(enriched_tweets),
                        "collection_time": datetime.utcnow().isoformat(),
                        "analysis": {
                            "avg_length": sum(t["length"] for t in enriched_tweets) / len(enriched_tweets) if enriched_tweets else 0,
                            "with_hashtags": sum(1 for t in enriched_tweets if t["has_hashtags"]),
                            "with_mentions": sum(1 for t in enriched_tweets if t["has_mentions"]),
                            "with_emoji": sum(1 for t in enriched_tweets if t["has_emoji"]),
                            "avg_virality": sum(t["virality_score"] for t in enriched_tweets) / len(enriched_tweets) if enriched_tweets else 0
                        }
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "tweets": [],
                        "total_found": 0,
                        "message": "Aucun tweet viral trouvé pour le moment"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting viral tweets: {e}")
            return {"success": False, "error": str(e)}


def get_config_fallback() -> dict:
    """Lecture directe du fichier de configuration"""
    try:
        # Chercher le fichier config depuis core/dashboard
        config_paths = [
            Path("../../config/config.json"),  # Depuis core/dashboard vers config
            Path("../config/config.json"),     # Depuis core vers config
            Path("config/config.json"),        # Depuis racine
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Configuration par défaut si aucun fichier trouvé
        return {
            "engagement": {
                "auto_reply_enabled": False,
                "max_replies_per_day": 20,
                "max_replies_per_conversation": 1,
                "reply_check_interval_minutes": 1
            },
            "posting": {
                "enabled": True,
                "frequency_per_day": 3,
                "time_range": {"start": "09:00", "end": "21:00"},
                "timezone": "Asia/Bangkok"
            },
            "content_generation": {
                "provider": "auto",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 150,
                "auto_reply": {
                    "temperature": 0.9,
                    "max_tokens": 60
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        return {}


def get_prompts_fallback() -> dict:
    """Lecture directe du fichier de prompts"""
    try:
        prompts_paths = [
            Path("../../config/prompts.json"),  # Depuis core/dashboard vers config
            Path("../config/prompts.json"),     # Depuis core vers config
            Path("config/prompts.json"),        # Depuis racine
        ]
        
        for prompts_path in prompts_paths:
            if prompts_path.exists():
                with open(prompts_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Configuration par défaut si aucun fichier trouvé
        return {
            "system_prompts": {
                "tweet_generation": {
                    "role": "system",
                    "content": "You are a crypto and blockchain expert who generates engaging tweets."
                },
                "auto_reply": {
                    "role": "system",
                    "content": "You are a crypto Twitter bot expert who responds to comments."
                }
            },
            "user_prompts": {
                "tweet_generation": {
                    "template": "Generate an engaging tweet about: {topic}",
                    "variables": ["topic"]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error reading prompts file: {e}")
        return {}


async def collect_bot_metrics(bot_managers: dict, start_time: datetime) -> BotMetrics:
    """Collecte les métriques du bot"""
    try:
        uptime = str(datetime.utcnow() - start_time).split('.')[0]
        
        # Métriques par défaut
        tweets_today = 0
        likes_today = 0
        replies_today = 0
        
        # Collecte des données si storage disponible
        storage_manager = bot_managers.get("storage_manager")
        if storage_manager:
            try:
                today = datetime.utcnow().date()
                recent_tweets = storage_manager.get_tweets(limit=50)
                for tweet in recent_tweets:
                    if tweet.posted_at and tweet.posted_at.date() == today:
                        tweets_today += 1
            except Exception as e:
                logger.debug(f"Error getting tweet metrics: {e}")
            
            try:
                # Simuler les métriques de replies pour l'instant
                likes_today = 5  # Placeholder
                replies_today = 8  # Placeholder
            except Exception as e:
                logger.debug(f"Error getting reply metrics: {e}")
        
        # Statut basé sur la disponibilité des managers
        config_manager = bot_managers.get("config_manager")
        status = "running" if config_manager else "limited"
        
        return BotMetrics(
            status=status,
            uptime=uptime,
            tweets_today=tweets_today,
            likes_today=likes_today,
            replies_today=replies_today,
            quota_usage={"posts": "5/50", "reads": "100/1667"},
            last_tweet=None,
            errors_count=0
        )
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return BotMetrics(
            status="error",
            uptime="unknown",
            tweets_today=0,
            likes_today=0,
            replies_today=0,
            quota_usage={},
            last_tweet=None,
            errors_count=1
        )


def get_recent_log_entries(limit: int = 20) -> List[Dict[str, Any]]:
    """Récupération des logs récents"""
    log_entries = []
    
    try:
        # Chercher les logs depuis core/dashboard
        possible_log_dirs = [
            Path("../../logs"),     # Depuis core/dashboard vers logs
            Path("../logs"),        # Depuis core vers logs
            Path("logs"),           # Depuis racine
        ]
        
        logs_dir = None
        for log_dir in possible_log_dirs:
            if log_dir.exists():
                logs_dir = log_dir
                break
        
        if logs_dir and logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in recent_lines:
                    if line.strip():
                        # Parse basique du log
                        timestamp = datetime.utcnow().isoformat()
                        level = "INFO"
                        
                        # Essayer d'extraire timestamp et level si possible
                        if " | " in line:
                            parts = line.split(" | ")
                            if len(parts) >= 3:
                                timestamp = parts[0].strip()
                                level = parts[1].strip()
                        
                        log_entries.append({
                            "timestamp": timestamp,
                            "level": level,
                            "message": line.strip()
                        })
        else:
            log_entries.append({
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO", 
                "message": "No log files found"
            })
                
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        log_entries.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": f"Error reading logs: {str(e)}"
        })
    
    return log_entries


def update_bot_config_section(section: str, request_data: dict, config_manager) -> dict:
    """Met à jour une section de la configuration bot"""
    try:
        # Chercher le fichier config
        config_paths = [
            Path("../../config/config.json"),  # Depuis core/dashboard vers config
            Path("../config/config.json"),     # Depuis core vers config
            Path("config/config.json"),        # Depuis racine
        ]
        
        config_file = None
        for config_path in config_paths:
            if config_path.exists():
                config_file = config_path
                break
        
        if not config_file:
            return {"success": False, "error": "Configuration file not found"}
        
        # Lire la config actuelle
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Mettre à jour la section appropriée
        if section == "engagement":
            engagement = config_data.get("engagement", {})
            
            if "auto_reply_enabled" in request_data:
                engagement["auto_reply_enabled"] = bool(request_data["auto_reply_enabled"])
            if "max_replies_per_day" in request_data:
                engagement["max_replies_per_day"] = int(request_data["max_replies_per_day"])
            if "max_replies_per_conversation" in request_data:
                engagement["max_replies_per_conversation"] = int(request_data["max_replies_per_conversation"])
            if "reply_check_interval_minutes" in request_data:
                engagement["reply_check_interval_minutes"] = int(request_data["reply_check_interval_minutes"])
            
            config_data["engagement"] = engagement
            
        elif section == "posting":
            posting = config_data.get("posting", {})
            
            if "enabled" in request_data:
                posting["enabled"] = bool(request_data["enabled"])
            if "frequency_per_day" in request_data:
                posting["frequency_per_day"] = int(request_data["frequency_per_day"])
            if "start_time" in request_data:
                posting["time_range"]["start"] = str(request_data["start_time"])
            if "end_time" in request_data:
                posting["time_range"]["end"] = str(request_data["end_time"])
            if "timezone" in request_data:
                posting["timezone"] = str(request_data["timezone"])
            
            config_data["posting"] = posting
            
        elif section == "content_generation":
            content_gen = config_data.get("content_generation", {})
            
            if "provider" in request_data:
                content_gen["provider"] = str(request_data["provider"])
            if "model" in request_data:
                content_gen["model"] = str(request_data["model"])
            if "temperature" in request_data:
                content_gen["temperature"] = float(request_data["temperature"])
            if "max_tokens" in request_data:
                content_gen["max_tokens"] = int(request_data["max_tokens"])
            
            # Mettre à jour auto_reply dans content_generation
            auto_reply = content_gen.get("auto_reply", {})
            if "reply_temperature" in request_data:
                auto_reply["temperature"] = float(request_data["reply_temperature"])
            if "reply_max_tokens" in request_data:
                auto_reply["max_tokens"] = int(request_data["reply_max_tokens"])
            
            content_gen["auto_reply"] = auto_reply
            config_data["content_generation"] = content_gen
        
        # Sauvegarder
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        # Recharger la config si possible
        if config_manager and hasattr(config_manager, 'reload_config'):
            config_manager.reload_config()
        
        return {"success": True, "message": f"Configuration {section} mise à jour"}
        
    except Exception as e:
        logger.error(f"Error updating {section} config: {e}")
        return {"success": False, "error": str(e)} 