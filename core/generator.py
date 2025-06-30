"""
Content Generator pour Bot Twitter Automatisé

Gère la génération intelligente de contenu :
- Analyse des trends viraux via Twitter API
- Génération de tweets optimisés avec GPT-4
- Création d'images avec DALL-E
- Templates et prompts configurables

NOUVELLE ARCHITECTURE:
- Error Recovery avec fallbacks créatifs
- Event Bus pour notifications de génération
- Intégration DI Container
- Messages utilisateur informatifs  
"""

import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO

import openai
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity


class ContentGenerator:
    """
    Générateur de contenu intelligent avec nouvelle architecture
    
    Features:
    - Analyse des trends Twitter pour inspiration
    - Prompts GPT-4 optimisés pour viralité
    - Génération d'images DALL-E contextuelles
    - Templates personnalisables
    - Anti-spam et variation de contenu
    - Error Recovery avec fallbacks créatifs
    - Event Bus pour notifications temps réel
    """
    
    def __init__(self, config_manager=None, twitter_manager=None, storage_manager=None, prompt_manager=None, viral_strategies=None):
        # Configuration via DI container ou fallback
        if any(x is None for x in [config_manager, twitter_manager, storage_manager, prompt_manager, viral_strategies]):
            try:
                from container import get_container
                container = get_container()
                self.config_manager = config_manager or container.get('config')
                self.twitter_manager = twitter_manager or container.get('twitter')
                self.storage_manager = storage_manager or container.get('storage')
                self.prompt_manager = prompt_manager or container.get('prompts')
                self.viral_strategies = viral_strategies or container.get('viral_strategies')
            except (ImportError, KeyError):
                logger.warning("⚠️ DI Container not available, using direct access")
                # Fallbacks directs si nécessaire
                if config_manager is None:
                    from core.config import create_config_manager
                    self.config_manager = create_config_manager()
                else:
                    self.config_manager = config_manager
                    
                # Les autres dépendances seront gérées par les fallbacks error recovery
                self.twitter_manager = twitter_manager
                self.storage_manager = storage_manager  
                self.prompt_manager = prompt_manager
                self.viral_strategies = viral_strategies
        else:
            self.config_manager = config_manager
            self.twitter_manager = twitter_manager
            self.storage_manager = storage_manager
            self.prompt_manager = prompt_manager
            self.viral_strategies = viral_strategies
            
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        self.openai_client = None
        self._last_generated_topics = []  # Anti-répétition
        self._tweet_type_index = 0  # Index pour rotation des types
        
        # Initialize components with error recovery
        self._initialize_with_recovery()
    
    @safe_execute(
        user_message_key="content_generation_error",
        severity=ErrorSeverity.LOW,
        fallback_category="content_generation",
        module="ContentGenerator"
    )
    def _initialize_with_recovery(self) -> None:
        """Initialize content generator components with comprehensive error recovery"""
        try:
            # Initialize LLM Provider Manager
            from core.llm_providers import LLMProviderManager
            self.llm_manager = LLMProviderManager()
            self.llm_manager.initialize_providers()
            
            # Initialize OpenAI (for images only)
            self._init_openai()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,
                data={
                    'module': 'content_generator',
                    'status': 'initialized',
                    'openai_available': self.openai_client is not None
                },
                source='ContentGenerator'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Content generator initialization warning: {e}")
            
            # Publier événement d'avertissement
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,
                data={
                    'module': 'content_generator',
                    'error': str(e),
                    'fallback_mode': 'limited_functionality'
                },
                source='ContentGenerator'
            )
    
    @safe_execute(
        user_message_key="image_generation_error",
        severity=ErrorSeverity.LOW,
        module="ContentGenerator"
    )
    def _init_openai(self) -> None:
        """Initialize OpenAI client avec error recovery"""
        try:
            api_key = self.config_manager.get_openai_api_key()
            if not api_key:
                logger.warning("⚠️ OpenAI API key not found - image generation will be disabled")
                self.openai_client = None
                return
            
            # Use new OpenAI client (v1.x)
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            
            # Test API
            try:
                response = self.openai_client.models.list()
                logger.info("✅ OpenAI client initialized successfully")
            except Exception as test_error:
                logger.warning(f"⚠️ OpenAI API test failed but client created: {test_error}")
            
        except Exception as e:
            logger.warning(f"⚠️ OpenAI initialization failed - continuing without image generation: {e}")
            self.openai_client = None
            raise e  # Laisse l'error recovery gérer
    
    def get_next_tweet_type(self) -> str:
        """
        Détermine le prochain type de tweet selon la rotation configurée
        
        Returns:
            str: Type de tweet à générer
        """
        try:
            config = self.config_manager.get_config()
            
            # Gérer les deux formats de configuration (dict ou objet)
            content_gen = config.content_generation
            if hasattr(content_gen, 'tweet_types'):
                tweet_types_config = content_gen.tweet_types
            else:
                tweet_types_config = getattr(content_gen, 'tweet_types', {})
            
            # Vérifier si le système de types est activé
            enabled = False
            if isinstance(tweet_types_config, dict):
                enabled = tweet_types_config.get("enabled", False)
            else:
                enabled = getattr(tweet_types_config, 'enabled', False)
                
            if not enabled:
                return "tweet_generation"  # Fallback sur le système classique
            
            # Récupérer le pattern de rotation
            if isinstance(tweet_types_config, dict):
                rotation_pattern = tweet_types_config.get("rotation_pattern", 
                    ["powerful_statement", "educational_post", "personal_story"])
                types_config = tweet_types_config.get("types", {})
                fallback_type = tweet_types_config.get("fallback_type", "powerful_statement")
            else:
                rotation_pattern = getattr(tweet_types_config, 'rotation_pattern', 
                    ["powerful_statement", "educational_post", "personal_story"])
                types_config = getattr(tweet_types_config, 'types', {})
                fallback_type = getattr(tweet_types_config, 'fallback_type', "powerful_statement")
            
            # Filtrer les types activés
            enabled_types = []
            for tweet_type in rotation_pattern:
                if isinstance(types_config, dict):
                    type_enabled = types_config.get(tweet_type, {}).get("enabled", True)
                else:
                    type_config = getattr(types_config, tweet_type, {})
                    if isinstance(type_config, dict):
                        type_enabled = type_config.get("enabled", True)
                    else:
                        type_enabled = getattr(type_config, 'enabled', True)
                        
                if type_enabled:
                    enabled_types.append(tweet_type)
            
            if not enabled_types:
                return fallback_type
            
            # Sélectionner le type suivant dans la rotation
            current_type = enabled_types[self._tweet_type_index % len(enabled_types)]
            self._tweet_type_index += 1
            
            logger.info(f"Next tweet type: {current_type} (index: {self._tweet_type_index})")
            return current_type
            
        except Exception as e:
            logger.error(f"Error determining tweet type: {e}")
            return "powerful_statement"  # Fallback sûr
    
    def get_tweet_type_config(self, tweet_type: str) -> Dict[str, Any]:
        """
        Récupère la configuration pour un type de tweet spécifique
        
        Args:
            tweet_type: Type de tweet
            
        Returns:
            Dict: Configuration du type de tweet
        """
        try:
            config = self.config_manager.get_config()
            
            # Gérer les deux formats de configuration (dict ou objet)
            content_gen = config.content_generation
            if hasattr(content_gen, 'tweet_types'):
                tweet_types_config = content_gen.tweet_types
            else:
                tweet_types_config = getattr(content_gen, 'tweet_types', {})
            
            # Si c'est un dictionnaire
            if isinstance(tweet_types_config, dict):
                types_config = tweet_types_config.get("types", {})
            else:
                # Si c'est un objet avec attributs
                types_config = getattr(tweet_types_config, 'types', {})
            
            # Configuration par défaut
            default_config = {
                "name": "Tweet Standard",
                "description": "Tweet standard",
                "max_tokens": 150,
                "temperature": 0.7,
                "weight": 1,
                "enabled": True
            }
            
            # Fusionner avec la config spécifique
            if isinstance(types_config, dict):
                type_config = types_config.get(tweet_type, {})
            else:
                type_config = getattr(types_config, tweet_type, {})
                
            return {**default_config, **type_config}
            
        except Exception as e:
            logger.error(f"Error getting tweet type config: {e}")
            return {
                "name": "Tweet Standard",
                "max_tokens": 150,
                "temperature": 0.7
            }
    
    def get_viral_inspiration(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère des tweets viraux pour inspiration
        
        Args:
            limit: Nombre maximum de tweets à récupérer
            
        Returns:
            List[Dict]: Liste de tweets viraux avec métadonnées
        """
        try:
            config = self.config_manager.get_config()
            keywords = config.content_generation.viral_keywords
            
            if not keywords:
                keywords = ["trending", "viral", "tech", "AI", "innovation"]
            
            # Rechercher des tweets viraux
            viral_tweets = self.twitter_manager.search_viral_tweets(
                keywords=keywords,
                max_results=limit * 2  # Récupérer plus pour avoir du choix
            )
            
            # Filtrer et préparer l'inspiration
            inspiration = []
            for tweet in viral_tweets[:limit]:
                text = tweet.get('text', '')
                topics = self._extract_topics(text)
                style = self._analyze_style(text)
                
                inspiration.append({
                    'text': text,
                    'metrics': tweet.get('metrics', {}),
                    'virality_score': tweet.get('virality_score', 0),
                    'topics': topics,
                    'style': style,
                    'length': len(text),
                    'word_count': len(text.split()),
                    'has_hashtags': '#' in text,
                    'has_mentions': '@' in text,
                    'has_emoji': any(ord(char) > 127 for char in text),
                    'has_question': '?' in text,
                    'has_exclamation': '!' in text,
                    'sentiment': self._analyze_sentiment(text),
                    'complexity': self._analyze_complexity(text)
                })
            
            logger.info(f"Collected {len(inspiration)} viral tweets for inspiration")
            return inspiration
            
        except Exception as e:
            logger.error(f"Failed to get viral inspiration: {e}")
            return []
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extrait les sujets principaux d'un tweet"""
        # Simple extraction basée sur mots-clés
        # En production, on pourrait utiliser NLP plus sophistiqué
        
        tech_keywords = ["AI", "IA", "intelligence", "technologie", "innovation", "startup", "tech"]
        trend_keywords = ["viral", "trending", "populaire", "buzz", "phénomène"]
        business_keywords = ["entreprise", "business", "succès", "croissance", "stratégie"]
        
        text_lower = text.lower()
        topics = []
        
        if any(keyword.lower() in text_lower for keyword in tech_keywords):
            topics.append("tech")
        if any(keyword.lower() in text_lower for keyword in trend_keywords):
            topics.append("trends")
        if any(keyword.lower() in text_lower for keyword in business_keywords):
            topics.append("business")
        
        return topics if topics else ["general"]
    
    def _analyze_style(self, text: str) -> Dict[str, Any]:
        """Analyse le style d'un tweet"""
        return {
            'length': len(text),
            'has_emoji': any(ord(char) > 127 for char in text),
            'has_hashtags': '#' in text,
            'has_mention': '@' in text,
            'has_question': '?' in text,
            'tone': 'enthusiastic' if '!' in text else 'neutral'
        }
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment d'un tweet (simple)"""
        text_lower = text.lower()
        
        # Mots positifs
        positive_words = [
            'great', 'amazing', 'awesome', 'fantastic', 'excellent', 'love', 'best',
            'incredible', 'wonderful', 'brilliant', 'perfect', 'outstanding',
            'bullish', 'moon', 'pump', 'gains', 'winning', 'success', 'boom'
        ]
        
        # Mots négatifs
        negative_words = [
            'terrible', 'awful', 'horrible', 'worst', 'hate', 'bad', 'fail',
            'disaster', 'crash', 'dump', 'bear', 'rekt', 'loss', 'scam',
            'rug', 'dead', 'broke', 'panic', 'fear'
        ]
        
        # Compter les mots
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _analyze_complexity(self, text: str) -> str:
        """Analyse la complexité d'un tweet"""
        words = text.split()
        
        # Facteurs de complexité
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        has_technical_terms = any(term in text.lower() for term in [
            'blockchain', 'defi', 'nft', 'smart contract', 'liquidity', 'yield',
            'staking', 'dao', 'governance', 'tokenomics', 'consensus', 'validator'
        ])
        has_numbers = any(char.isdigit() for char in text)
        sentence_count = text.count('.') + text.count('!') + text.count('?') + 1
        
        complexity_score = 0
        
        if avg_word_length > 6:
            complexity_score += 1
        if has_technical_terms:
            complexity_score += 1
        if has_numbers:
            complexity_score += 1
        if sentence_count > 2:
            complexity_score += 1
            
        if complexity_score >= 3:
            return 'high'
        elif complexity_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def generate_fallback_crypto_content(self) -> Optional[str]:
        """
        Génère du contenu crypto de base quand OpenAI n'est pas disponible
        
        Returns:
            str: Contenu du tweet généré
        """
        try:
            import random
            from datetime import datetime
            
                         # Dynamic crypto templates with current trends
            crypto_templates = [
                "📈 #Solana developers are shipping faster than ever! The ecosystem momentum is insane 🔥 #SOL",
                "💰 Smart money keeps flowing into #Solana projects. Quality speaks louder than hype 🎯 #SOL",
                "🌊 Another day, another #Solana innovation. Speed meets substance in crypto 2025 ⚡ #SOL",
                "🔥 While others talk, #Solana builds. 400ms block times hitting different 🚀 #SOL #Performance", 
                "💎 #Solana fees under $0.01 while handling millions of txs. This is why we're here 🎪 #SOL",
                "⚡ The #Solana validator network keeps growing stronger. Decentralization in action 🌐 #SOL",
                "📊 #Solana TVL climbing steadily. Real utility drives real growth 📈 #DeFi #SOL",
                "🌟 Weekend building never stops in #Solana land. Developers are the real alphas 👨‍💻 #SOL",
                "🎯 #Solana proving that speed AND decentralization can coexist. Game theory playing out 🧠 #SOL",
                "🔮 2025 prediction: #Solana ecosystem will surprise everyone again. Innovation compounds 🚀 #SOL",
                "💪 #Solana network uptime speaks for itself. When it matters, we deliver 📡 #SOL #Reliability",
                "🌊 New #Solana projects launching weekly. The innovation pipeline is endless 🏗️ #SOL #Building",
                "⚡ Sub-second finality on #Solana hits different when you experience it firsthand 🎮 #SOL",
                "🔥 #Solana mobile integration moving fast. Web3 meets real-world adoption 📱 #SOL #Saga",
                "💰 Institutional capital finally understanding #Solana's technical advantages 🏦 #SOL #Institutional",
                "📈 #Solana DeFi protocols showing mature growth patterns. Sustainable > flashy 📊 #DeFi #SOL",
                "🎪 The #Solana community building culture is unmatched. Vibes plus substance 🌟 #SOL #Community",
                "⚡ Watching #Solana process millions of transactions like it's nothing. Poetry in motion 🎭 #SOL",
                "🚀 #Solana validators distributed globally. True decentralization isn't just a buzzword 🌍 #SOL",
                "💎 Long-term #Solana believers being rewarded for technical conviction. Fundamentals matter 🎯 #SOL"
            ]
            
            # Sélectionner un template aléatoire
            selected_content = random.choice(crypto_templates)
            
            # Ajouter timestamp pour l'unicité
            timestamp = datetime.now().strftime("%H:%M")
            
            # Parfois ajouter le timestamp
            if random.random() < 0.3:  # 30% de chance
                selected_content += f" [{timestamp}]"
            
            logger.info("Generated fallback crypto content")
            return selected_content
            
        except Exception as e:
            logger.error(f"Failed to generate fallback content: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_tweet_content(self, inspiration: Optional[List[Dict]] = None, tweet_type: Optional[str] = None) -> Optional[str]:
        """
        Génère le contenu d'un tweet avec le nouveau système de types
        
        Args:
            inspiration: Liste optionnelle de tweets viraux pour inspiration
            tweet_type: Type de tweet spécifique à générer (optionnel)
            
        Returns:
            str: Contenu du tweet généré, None si échec
        """
        try:
            # Utiliser le LLM Provider Manager au lieu d'OpenAI direct
            if not self.llm_manager.has_available_providers():
                logger.info("No LLM providers available - using fallback crypto content")
                return self.generate_fallback_crypto_content()
                
            config = self.config_manager.get_config()
            
            # Déterminer le type de tweet à générer
            if not tweet_type:
                tweet_type = self.get_next_tweet_type()
            
            # Obtenir la configuration du type de tweet
            type_config = self.get_tweet_type_config(tweet_type)
            
            # Obtenir inspiration si pas fournie
            if not inspiration:
                inspiration = self.get_viral_inspiration()
            
            # Construire les prompts selon le type
            system_prompt = self._get_system_prompt_for_type(tweet_type)
            user_prompt = self._build_tweet_prompt_for_type(tweet_type, inspiration)
            
            # Utiliser les paramètres spécifiques au type
            max_tokens = type_config.get('max_tokens', 150)
            temperature = type_config.get('temperature', 0.7)
            
            logger.info(f"Generating {tweet_type} tweet (max_tokens: {max_tokens}, temp: {temperature})")
            
            # Utiliser LLM Provider Manager pour générer
            generated_content = self.llm_manager.generate_reply(
                system_prompt=system_prompt['content'],
                user_prompt=user_prompt,
                model=config.content_generation.model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if generated_content:
                # Enlever les guillemets au début et à la fin
                generated_content = generated_content.strip('"').strip("'").strip()
                
                # Validation du contenu
                if self._validate_tweet_content(generated_content, tweet_type):
                    logger.info(f"{type_config.get('name', tweet_type)} generated successfully")
                    return generated_content
                else:
                    logger.warning("Generated content failed validation - using fallback")
                    return self.generate_fallback_crypto_content()
            else:
                logger.warning("LLM generation returned empty content - using fallback")
                return self.generate_fallback_crypto_content()
            
        except Exception as e:
            logger.error(f"Failed to generate tweet content: {e}")
            raise
        
        return None
    
    def _get_system_prompt(self) -> Dict[str, str]:
        """System prompt for GPT-4 from centralized prompts (legacy)"""
        return self.prompt_manager.get_system_prompt("tweet_generation")
    
    def _get_system_prompt_for_type(self, tweet_type: str) -> Dict[str, str]:
        """System prompt for specific tweet type"""
        try:
            return self.prompt_manager.get_system_prompt(tweet_type)
        except Exception as e:
            logger.warning(f"Failed to get system prompt for {tweet_type}, using default: {e}")
            return self.prompt_manager.get_system_prompt("tweet_generation")
    
    def _build_tweet_prompt(self, inspiration: List[Dict]) -> str:
        """Builds user prompt from centralized prompts (legacy)"""
        return self.prompt_manager.get_user_prompt(
            "tweet_generation",
            inspiration=self._format_inspiration(inspiration),
            recent_topics=", ".join(self._last_generated_topics[-5:])
        )
    
    def _build_tweet_prompt_for_type(self, tweet_type: str, inspiration: List[Dict]) -> str:
        """Builds user prompt for specific tweet type"""
        try:
            # Sélectionner un sujet aléatoire
            topics = []
            if inspiration:
                for tweet_data in inspiration:
                    topics.extend(tweet_data.get('topics', []))
            
            if not topics:
                # Utiliser les mots-clés viraux de la config
                config = self.config_manager.get_config()
                topics = config.content_generation.viral_keywords
            
            # Sélectionner un sujet aléatoire
            topic = random.choice(topics) if topics else "crypto innovation"
            
            # Utiliser le template du type de tweet
            return self.prompt_manager.get_user_prompt(
                tweet_type,
                topic=topic
            )
        except Exception as e:
            logger.warning(f"Failed to build prompt for {tweet_type}, using default: {e}")
            return self._build_tweet_prompt(inspiration)
    
    def _format_inspiration(self, inspiration: List[Dict]) -> str:
        """Format inspiration data for prompt template"""
        formatted_parts = []
        for i, tweet_data in enumerate(inspiration[:3], 1):
            topics = ", ".join(tweet_data.get('topics', []))
            formatted_parts.append(f"{i}. Topic: {topics}")
            formatted_parts.append(f"   Style: {tweet_data.get('style', {}).get('tone', 'neutral')}")
            formatted_parts.append(f"   Virality: {tweet_data.get('virality_score', 0)} points\n")
        return "\n".join(formatted_parts)
    
    def _validate_tweet_content(self, content: str, tweet_type: str = "tweet_generation") -> bool:
        """Valide le contenu généré selon le type de tweet"""
        if not content:
            return False
        
        # Obtenir les limites spécifiques au type
        type_config = self.get_tweet_type_config(tweet_type)
        max_length = min(280, type_config.get('max_tokens', 280) * 4)  # Approximation caractères/tokens
        
        # Vérifier la longueur
        if len(content) > 280:  # Limite Twitter absolue
            logger.warning(f"Tweet too long: {len(content)} characters")
            return False
        
        # Longueur minimale adaptée au type
        min_length = 20 if tweet_type == "educational_post" else 10
        if len(content) < min_length:
            logger.warning(f"Tweet too short for {tweet_type}: {len(content)} characters")
            return False
        
        # Vérifications spécifiques par type
        if tweet_type == "powerful_statement":
            # Les statements doivent être concis
            if len(content) > 150:
                logger.warning(f"Powerful statement too long: {len(content)} characters")
                return False
        elif tweet_type == "educational_post":
            # Les posts éducatifs doivent avoir du contenu structuré
            if "•" not in content and ":" not in content and "1." not in content:
                logger.warning("Educational post lacks structure")
                # Ne pas rejeter, mais noter
        elif tweet_type == "personal_story":
            # Les histoires personnelles devraient avoir des marqueurs émotionnels
            emotional_words = ["i", "me", "my", "felt", "learned", "remember", "experience"]
            content_lower = content.lower()
            if not any(word in content_lower for word in emotional_words):
                logger.warning("Personal story lacks personal touch")
                # Ne pas rejeter, mais noter
        
        # Vérifier qu'il ne répète pas un sujet récent
        content_lower = content.lower()
        for recent_topic in self._last_generated_topics[-10:]:
            if recent_topic.lower() in content_lower:
                logger.warning(f"Content repeats recent topic: {recent_topic}")
                return False
        
        # Ajouter à l'historique avec le type
        main_topic = self._extract_topics(content)
        if main_topic:
            topic_with_type = f"{main_topic[0]}_{tweet_type}"
            self._last_generated_topics.append(topic_with_type)
            if len(self._last_generated_topics) > 20:
                self._last_generated_topics = self._last_generated_topics[-20:]
        
        return True
    
    @safe_execute(
        user_message_key="viral_generation_error",
        severity=ErrorSeverity.MEDIUM,
        fallback_category="content_generation",
        module="ContentGenerator"
    )
    def generate_viral_tweet(self, topic: Optional[str] = None, content_type: Optional[str] = None, 
                           strategy: Optional[str] = None) -> Optional[str]:
        """
        Génère un tweet viral en utilisant les stratégies de Nick Huber
        
        Args:
            topic: Sujet spécifique (optionnel)
            content_type: Type de contenu viral (optionnel)
            strategy: Stratégie d'engagement (optionnel)
            
        Returns:
            str: Contenu du tweet viral généré
        """
        try:
            if not self.viral_strategies:
                logger.warning("Viral strategies not available, falling back to standard generation")
                return self.generate_tweet_content()
            
            # Import des enums depuis viral_strategies
            from viral_strategies import ContentType, EngagementStrategy
            
            # Sélectionner un sujet viral si non spécifié
            if not topic:
                viral_topics = self.viral_strategies.get_viral_topic_suggestions("crypto")
                topic = random.choice(viral_topics)
            
            # Sélectionner le type de contenu
            if content_type:
                try:
                    content_type_enum = ContentType(content_type)
                except ValueError:
                    content_type_enum = ContentType.CONTROVERSIAL_STANCE
            else:
                content_type_enum = random.choice(list(ContentType))
            
            # Sélectionner la stratégie d'engagement
            if strategy:
                try:
                    strategy_enum = EngagementStrategy(strategy)
                except ValueError:
                    strategy_enum = EngagementStrategy.PROVOCATION
            else:
                strategy_enum = random.choice(list(EngagementStrategy))
            
            # Générer la structure virale
            viral_structure = self.viral_strategies.generate_viral_structure(
                topic=topic,
                content_type=content_type_enum,
                strategy=strategy_enum
            )
            
            # Formater en tweet
            viral_tweet = self.viral_strategies.format_viral_tweet(viral_structure)
            
            # Valider avec l'analyseur de potentiel viral
            viral_scores = self.viral_strategies.analyze_viral_potential(viral_tweet)
            
            logger.info(f"Generated viral tweet with {viral_scores['overall']:.2f} viral score")
            logger.debug(f"Viral breakdown: Hook={viral_scores['hook_strength']:.2f}, "
                        f"Stance={viral_scores['stance_clarity']:.2f}, "
                        f"Controversy={viral_scores['controversy']:.2f}")
            
            # Vérifier si le score viral minimum est atteint
            config = self.config_manager.get_config()
            min_viral_score = getattr(config.content_generation, 'min_viral_score', 0.15)  # Seuil plus réaliste
            
            # Limiter les régénérations pour éviter les boucles infinies
            if viral_scores['overall'] < min_viral_score and not hasattr(self, '_viral_retry_count'):
                self._viral_retry_count = getattr(self, '_viral_retry_count', 0) + 1
                if self._viral_retry_count < 3:  # Maximum 3 tentatives
                    logger.warning(f"Viral score {viral_scores['overall']:.2f} below threshold {min_viral_score}, regenerating... (attempt {self._viral_retry_count})")
                    # Retry avec une stratégie plus agressive
                    return self.generate_viral_tweet(topic, "controversial_stance", "provocation")
                else:
                    logger.info(f"Max retries reached, accepting viral score {viral_scores['overall']:.2f}")
                    self._viral_retry_count = 0  # Reset pour la prochaine fois
            
            # Publier événement de succès  
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,  # Utiliser un event type existant
                data={
                    'type': 'viral_tweet_generated',
                    'topic': topic,
                    'content_type': content_type_enum.value,
                    'strategy': strategy_enum.value,
                    'viral_score': viral_scores['overall'],
                    'length': len(viral_tweet)
                },
                source='ContentGenerator'
            )
            
            return viral_tweet
            
        except Exception as e:
            logger.error(f"Failed to generate viral tweet: {e}")
            # Fallback vers génération standard
            return self.generate_tweet_content()
    
    def get_viral_analysis(self, text: str) -> Dict[str, Any]:
        """
        Analyse le potentiel viral d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dict: Analyse complète du potentiel viral
        """
        try:
            if not self.viral_strategies:
                return {"error": "Viral strategies not available"}
            
            scores = self.viral_strategies.analyze_viral_potential(text)
            
            # Ajouter des recommandations basées sur les scores
            recommendations = []
            
            if scores['hook_strength'] < 0.3:
                recommendations.append("Hook trop faible - commencer par 'If you...', 'Most people...', ou 'Unpopular opinion:'")
            
            if scores['stance_clarity'] < 0.3:
                recommendations.append("Position pas assez claire - prendre une position ferme, éviter la nuance")
            
            if scores['specificity'] < 0.3:
                recommendations.append("Manque de spécificité - ajouter des chiffres précis et des exemples concrets")
            
            if scores['controversy'] < 0.2:
                recommendations.append("Potentiel de controverse faible - être plus audacieux, challenger les croyances communes")
            
            if scores['pattern_interrupt'] < 0.3:
                recommendations.append("Faible capacité à arrêter le scroll - utiliser des mots choc comme 'wrong', 'lying', 'truth'")
            
            return {
                'scores': scores,
                'grade': self._get_viral_grade(scores['overall']),
                'recommendations': recommendations,
                'overall_assessment': self._get_viral_assessment(scores['overall'])
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze viral potential: {e}")
            return {"error": str(e)}
    
    def _get_viral_grade(self, score: float) -> str:
        """Convertit le score viral en note"""
        if score >= 0.8:
            return "A+ (Très viral)"
        elif score >= 0.6:
            return "A (Viral)"
        elif score >= 0.4:
            return "B (Bon potentiel)"
        elif score >= 0.2:
            return "C (Potentiel moyen)"
        else:
            return "D (Faible potentiel)"
    
    def _get_viral_assessment(self, score: float) -> str:
        """Donne une évaluation textuelle du potentiel viral"""
        if score >= 0.8:
            return "Excellent! Ce tweet a un très fort potentiel viral avec tous les éléments de Nick Huber."
        elif score >= 0.6:
            return "Très bien! Ce tweet devrait bien performer avec quelques ajustements mineurs."
        elif score >= 0.4:
            return "Correct. Ce tweet a du potentiel mais peut être amélioré pour plus de viralité."
        elif score >= 0.2:
            return "Moyen. Ce tweet nécessite des améliorations significatives pour devenir viral."
        else:
            return "Faible. Ce tweet doit être réécrit en suivant la structure de Nick Huber."
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_image(self, tweet_content: str) -> Optional[str]:
        """
        Génère une image avec DALL-E basée sur le contenu du tweet
        
        Args:
            tweet_content: Contenu du tweet pour contexte
            
        Returns:
            str: URL de l'image générée, None si échec
        """
        try:
            if not self.openai_client:
                logger.info("OpenAI client not available - skipping image generation")
                return None
                
            config = self.config_manager.get_config()
            
            if not config.content_generation.enable_images:
                logger.info("Image generation disabled in config")
                return None
            
            # Construire le prompt pour l'image
            image_prompt = self._build_image_prompt(tweet_content)
            
            # Générer l'image avec DALL-E
            response = self.openai_client.images.generate(
                model=config.content_generation.image_model,
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            if response.data:
                image_url = response.data[0].url
                
                # Télécharger et sauvegarder l'image
                saved_url = self._download_and_save_image(image_url, tweet_content)
                
                if saved_url:
                    logger.info("Image generated and saved successfully")
                    return saved_url
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            # Ne pas lever l'exception, l'image est optionnelle
        
        return None
    
    def _build_image_prompt(self, tweet_content: str) -> str:
        """Builds image prompt from centralized prompts"""
        # Analyser le contenu pour extraire le thème
        topics = self._extract_topics(tweet_content)
        
        # Déterminer le thème principal
        if any(topic in ["tech", "crypto"] for topic in topics):
            theme = "crypto"
        elif "business" in topics:
            theme = "business"
        elif "trends" in topics:
            theme = "trends"
        else:
            theme = "default"
        
        return self.prompt_manager.get_image_prompt(tweet_content, theme)
    
    def _download_and_save_image(self, image_url: str, context: str) -> Optional[str]:
        """Télécharge et sauvegarde l'image dans Supabase Storage"""
        try:
            # Télécharger l'image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Générer nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            
            # Uploader vers Supabase
            public_url = self.storage_manager.upload_image(
                image_data=response.content,
                filename=filename
            )
            
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to download and save image: {e}")
            return None
    
    def generate_complete_post(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Génère un post complet : texte + image
        
        Returns:
            Tuple[str, str]: (contenu_tweet, url_image) ou (None, None) si échec
        """
        try:
            # Obtenir inspiration
            inspiration = self.get_viral_inspiration()
            
            # Générer contenu
            tweet_content = self.generate_tweet_content(inspiration)
            if not tweet_content:
                logger.error("Failed to generate tweet content")
                return None, None
            
            # Générer image si activé
            image_url = None
            config = self.config_manager.get_config()
            if config.content_generation.enable_images:
                image_url = self.generate_image(tweet_content)
            
            logger.info("Complete post generated successfully")
            return tweet_content, image_url
            
        except Exception as e:
            logger.error(f"Failed to generate complete post: {e}")
            return None, None
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de génération"""
        return {
            'recent_topics': self._last_generated_topics[-10:],
            'total_topics_generated': len(self._last_generated_topics),
            'openai_available': self.openai_client is not None,
            'images_enabled': self.config_manager.get_config().content_generation.enable_images
        }


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION  
# =============================================================================

def create_content_generator(config_manager=None, twitter_manager=None, storage_manager=None, prompt_manager=None, viral_strategies=None) -> ContentGenerator:
    """
    Factory function pour DI Container
    
    Crée une instance ContentGenerator avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return ContentGenerator(config_manager, twitter_manager, storage_manager, prompt_manager, viral_strategies)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_content_generator() -> ContentGenerator:
    """
    DEPRECATED: Utiliser container.get('content') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_content_generator() is deprecated. Use container.get('content') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('content')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_content_generator()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - Fine-tuning de modèles GPT pour styles spécifiques
# - A/B testing automatique de différents prompts
# - Analyse sentiment des tweets générés
# - Templates personnalisables par industrie/niche
# - Génération de threads Twitter multi-tweets
# - Integration avec trends Google/Reddit pour inspiration
# - Machine learning pour optimiser viralité basée sur historique
# - Support pour génération video courtes (via APIs tierces)
# - Event-driven content adaptation based on performance
# - Multi-language content generation
# - AI-powered hashtag optimization
# - Content personalization based on audience analytics 