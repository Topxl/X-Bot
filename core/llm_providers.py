#!/usr/bin/env python3
"""
Système modulaire de providers LLM
Support: OpenAI, LM Studio, et extensible pour d'autres providers
"""

import os
import requests
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from openai import OpenAI
from loguru import logger

class BaseLLMProvider(ABC):
    """Interface abstraite pour tous les providers LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.is_available = False
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialise le provider"""
        pass
    
    @abstractmethod
    def generate_reply(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        """Génère une réponse"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test la connexion au provider"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles"""
        pass

class OpenAIProvider(BaseLLMProvider):
    """Provider pour OpenAI GPT models"""
    
    def initialize(self) -> bool:
        """Initialise le client OpenAI"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found")
                return False
            
            self.client = OpenAI(api_key=api_key)
            self.is_available = self.test_connection()
            
            if self.is_available:
                logger.info("OpenAI provider initialized successfully")
            else:
                logger.warning("OpenAI provider connection test failed")
                
            return self.is_available
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test la connexion OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.debug(f"OpenAI connection test failed: {e}")
            return False
    
    def generate_reply(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        """Génère une réponse via OpenAI"""
        try:
            model = kwargs.get('model', 'gpt-4o-mini')
            max_tokens = kwargs.get('max_tokens', 60)
            temperature = kwargs.get('temperature', 0.9)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response.choices:
                return response.choices[0].message.content.strip().strip('"').strip("'").strip()
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Retourne les modèles OpenAI disponibles"""
        return [
            "gpt-4o-mini",
            "gpt-4o", 
            "gpt-4",
            "gpt-3.5-turbo"
        ]

class LMStudioProvider(BaseLLMProvider):
    """Provider pour LM Studio"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_urls = []
        self.active_url = None
        self._configured_model = None  # Auto-détecté
        self._available_models = []
        
    def initialize(self) -> bool:
        """Initialise le client LM Studio avec auto-détection du modèle"""
        try:
            # URL principale (priorité localhost)
            primary_url = os.getenv("LM_API_URL", "http://localhost:1234")
            self.base_urls = [primary_url]
            
            # Tester d'abord l'URL principale (généralement localhost)
            logger.info(f"Testing primary LM Studio URL: {primary_url}")
            if self._test_url_and_detect_model(primary_url):
                return True
            
            # Seulement si l'URL principale échoue, essayer les alternatives
            alternative_ips = os.getenv("LM_ALTERNATIVE_IPS", "").strip()
            if alternative_ips:
                logger.info(f"Primary URL failed, trying alternatives...")
                
                for ip in alternative_ips.split(","):
                    ip = ip.strip()
                    if ip and ip not in ["localhost", "127.0.0.1"]:
                        # Extraire le port de l'URL principale
                        port = primary_url.split(":")[-1] if ":" in primary_url else "1234"
                        alt_url = f"http://{ip}:{port}"
                        
                        if alt_url not in self.base_urls:
                            self.base_urls.append(alt_url)
                            logger.debug(f"Testing alternative URL: {alt_url}")
                            
                            if self._test_url_and_detect_model(alt_url):
                                return True
            
            logger.warning("No LM Studio instance found - tried primary + alternatives")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize LM Studio provider: {e}")
            return False
    
    def _test_url(self, url: str) -> bool:
        """Test si une URL LM Studio est accessible"""
        try:
            response = requests.get(f"{url}/v1/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _test_url_and_detect_model(self, url: str) -> bool:
        """Test l'URL et auto-détecte le modèle disponible"""
        try:
            # Test de connectivité et récupération des modèles
            response = requests.get(f"{url}/v1/models", timeout=5)
            if response.status_code != 200:
                return False
            
            # Parser la réponse pour récupérer les modèles
            models_data = response.json()
            available_models = []
            
            if 'data' in models_data and isinstance(models_data['data'], list):
                available_models = [model.get('id', '') for model in models_data['data'] if model.get('id')]
            
            if not available_models:
                logger.warning(f"No models found at {url}")
                return False
            
            # Sélectionner le premier modèle disponible
            selected_model = available_models[0]
            
            # Vérifier si un modèle spécifique est demandé
            preferred_model = os.getenv("LM_MODEL_NAME", "").strip()
            if preferred_model and preferred_model in available_models:
                selected_model = preferred_model
                logger.info(f"Using preferred model: {selected_model}")
            else:
                logger.info(f"Auto-selected model: {selected_model}")
            
            # Configurer le client
            self.active_url = url
            self.client = OpenAI(base_url=f"{url}/v1", api_key="not-needed")
            self.is_available = True
            
            # Stocker les infos des modèles pour le manager
            self._configured_model = selected_model
            self._available_models = available_models
            
            logger.info(f"✅ LM Studio connected at {url}")
            logger.info(f"🤖 Model: {selected_model}")
            logger.info(f"📋 Available models: {len(available_models)} ({', '.join(available_models[:3])}{'...' if len(available_models) > 3 else ''})")
            
            return True
            
        except Exception as e:
            logger.debug(f"Failed to connect to {url}: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test la connexion LM Studio"""
        if not self.active_url:
            return False
        return self._test_url(self.active_url)
    
    def generate_reply(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        """Génère une réponse via LM Studio"""
        try:
            if not self.client or not self.is_available or not self._configured_model:
                logger.warning("LM Studio client not available or no model detected")
                return None
            
            # Utiliser le modèle auto-détecté ou spécifique
            model_to_use = kwargs.get('model') or self._configured_model
            
            # Vérifier que le modèle est disponible
            if self._available_models and model_to_use not in self._available_models:
                logger.warning(f"Model {model_to_use} not available, using {self._configured_model}")
                model_to_use = self._configured_model
            
            max_tokens = kwargs.get('max_tokens', 60)
            temperature = kwargs.get('temperature', 0.9)
            
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response.choices:
                return response.choices[0].message.content.strip().strip('"').strip("'").strip()
            
            return None
            
        except Exception as e:
            logger.error(f"LM Studio generation failed: {e}")
            # Essayer de reconnecter sur une autre URL
            self._try_reconnect()
            return None
    
    def _try_reconnect(self):
        """Essaie de se reconnecter sur une autre URL"""
        logger.info("Trying to reconnect to LM Studio...")
        for url in self.base_urls:
            if url != self.active_url and self._test_url(url):
                self.active_url = url
                self.client = OpenAI(base_url=f"{url}/v1", api_key="not-needed")
                logger.info(f"Reconnected to LM Studio at {url}")
                return True
        return False
    
    def get_available_models(self) -> List[str]:
        """Retourne les modèles LM Studio disponibles"""
        if not self.is_available:
            return []
        
        return self._available_models.copy() if self._available_models else []

class LLMProviderManager:
    """Gestionnaire des providers LLM avec fallback automatique"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.active_provider: Optional[str] = None
        self.provider_priority = []
        
    def initialize_providers(self) -> bool:
        """Initialise tous les providers disponibles"""
        success = False
        
        # Initialiser OpenAI
        openai_provider = OpenAIProvider({})
        if openai_provider.initialize():
            self.providers["openai"] = openai_provider
            success = True
            logger.info("✅ OpenAI provider ready")
        
        # Initialiser LM Studio
        lm_provider = LMStudioProvider({})
        if lm_provider.initialize():
            self.providers["lmstudio"] = lm_provider
            success = True
            logger.info("✅ LM Studio provider ready")
        
        # Déterminer la priorité basée sur la config
        preferred_provider = os.getenv("LLM_PROVIDER", "auto").lower()
        
        if preferred_provider == "lmstudio" and "lmstudio" in self.providers:
            self.provider_priority = ["lmstudio", "openai"]
            self.active_provider = "lmstudio"
        elif preferred_provider == "openai" and "openai" in self.providers:
            self.provider_priority = ["openai", "lmstudio"]
            self.active_provider = "openai"
        else:
            # Auto: priorité LM Studio > OpenAI
            available = list(self.providers.keys())
            if "lmstudio" in available:
                self.provider_priority = ["lmstudio"] + [p for p in available if p != "lmstudio"]
                self.active_provider = "lmstudio"
            elif "openai" in available:
                self.provider_priority = ["openai"] + [p for p in available if p != "openai"]
                self.active_provider = "openai"
        
        if self.active_provider:
            logger.info(f"🎯 Active LLM provider: {self.active_provider}")
            logger.info(f"🔄 Fallback order: {' → '.join(self.provider_priority)}")
        
        return success
    
    def generate_reply(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        """Génère une réponse avec fallback automatique"""
        for provider_name in self.provider_priority:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                
                try:
                    logger.debug(f"Trying {provider_name} for reply generation")
                    response = provider.generate_reply(system_prompt, user_prompt, **kwargs)
                    
                    if response:
                        logger.info(f"Reply generated successfully with {provider_name}")
                        return response
                        
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
        
        logger.error("All LLM providers failed to generate reply")
        return None
    
    def has_available_providers(self) -> bool:
        """Vérifie si au moins un provider est disponible"""
        return len(self.providers) > 0 and any(
            provider.is_available for provider in self.providers.values()
        )
    
    def get_active_provider_info(self) -> Dict[str, Any]:
        """Retourne les infos du provider actif"""
        if not self.active_provider or self.active_provider not in self.providers:
            return {"provider": "none", "available": False}
        
        provider = self.providers[self.active_provider]
        info = {
            "provider": self.active_provider,
            "available": provider.is_available,
            "models": provider.get_available_models()
        }
        
        # Ajouter des infos spécifiques
        if self.active_provider == "lmstudio":
            info["active_url"] = getattr(provider, 'active_url', None)
            info["configured_model"] = os.getenv("LM_MODEL_NAME", "default")
        
        return info
    
    def switch_provider(self, provider_name: str) -> bool:
        """Change le provider actif"""
        if provider_name in self.providers:
            old_provider = self.active_provider
            self.active_provider = provider_name
            
            # Réorganiser la priorité
            self.provider_priority = [provider_name] + [p for p in self.provider_priority if p != provider_name]
            
            logger.info(f"Switched LLM provider: {old_provider} → {provider_name}")
            return True
        
        logger.warning(f"Provider {provider_name} not available")
        return False

# Instance globale
_llm_manager = None

def get_llm_manager() -> LLMProviderManager:
    """Retourne l'instance globale du LLM manager"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMProviderManager()
        _llm_manager.initialize_providers()
    return _llm_manager 