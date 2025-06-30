"""
Optimiseur de logs pour réduire le spam répétitif
"""

import time
from typing import Dict, Set
from collections import defaultdict
from datetime import datetime, timedelta
from loguru import logger


class LogOptimizer:
    """Optimise les logs pour éviter les répétitions excessives"""
    
    def __init__(self):
        self._message_counts: Dict[str, int] = defaultdict(int)
        self._last_logged: Dict[str, float] = {}
        self._suppressed_messages: Set[str] = set()
        self._reset_interval = 3600  # Reset toutes les heures
        self._last_reset = time.time()
        
        # Configuration par type de message
        self._rules = {
            'rate_limit': {'max_per_hour': 5, 'min_interval': 300},  # Max 5 par heure, min 5 min
            'reply_check': {'max_per_hour': 12, 'min_interval': 60},  # Max 12 par heure, min 1 min
            'dashboard_request': {'max_per_hour': 0, 'min_interval': 0},  # Complètement supprimé
            'found_replies': {'max_per_hour': 20, 'min_interval': 30},  # Max 20 par heure, min 30 sec
            'quota_check': {'max_per_hour': 10, 'min_interval': 120},  # Max 10 par heure, min 2 min
        }
    
    def should_log(self, message_type: str, message: str) -> bool:
        """
        Détermine si un message doit être logué
        
        Args:
            message_type: Type de message ('rate_limit', 'reply_check', etc.)
            message: Contenu du message
            
        Returns:
            bool: True si le message doit être logué
        """
        current_time = time.time()
        
        # Reset périodique des compteurs
        if current_time - self._last_reset > self._reset_interval:
            self._reset_counters()
        
        # Vérifier les règles pour ce type de message
        if message_type not in self._rules:
            return True  # Pas de règle = toujours logger
        
        rule = self._rules[message_type]
        message_key = f"{message_type}:{hash(message) % 1000}"
        
        # Complètement supprimé
        if rule['max_per_hour'] == 0:
            return False
        
        # Vérifier l'intervalle minimum
        if message_key in self._last_logged:
            time_since_last = current_time - self._last_logged[message_key]
            if time_since_last < rule['min_interval']:
                return False
        
        # Vérifier le maximum par heure
        if self._message_counts[message_key] >= rule['max_per_hour']:
            if message_key not in self._suppressed_messages:
                self._suppressed_messages.add(message_key)
                logger.debug(f"Log suppressed for {message_type} (max {rule['max_per_hour']}/h reached)")
            return False
        
        # Autoriser le log
        self._message_counts[message_key] += 1
        self._last_logged[message_key] = current_time
        
        # Retirer de la liste des supprimés si c'était le cas
        if message_key in self._suppressed_messages:
            self._suppressed_messages.remove(message_key)
        
        return True
    
    def _reset_counters(self):
        """Reset les compteurs périodiquement"""
        self._message_counts.clear()
        self._suppressed_messages.clear()
        self._last_reset = time.time()
        logger.debug("Log optimizer counters reset")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de suppression"""
        return {
            'suppressed_types': len(self._suppressed_messages),
            'total_messages_tracked': len(self._message_counts),
            'last_reset': datetime.fromtimestamp(self._last_reset).isoformat()
        }


# Instance globale
_log_optimizer = LogOptimizer()


def should_log(message_type: str, message: str) -> bool:
    """Interface simple pour vérifier si un message doit être logué"""
    return _log_optimizer.should_log(message_type, message)


def log_with_optimization(level: str, message_type: str, message: str):
    """Log un message avec optimisation automatique"""
    if should_log(message_type, message):
        getattr(logger, level.lower())(message)


def get_log_stats() -> Dict:
    """Obtient les statistiques de l'optimiseur de logs"""
    return _log_optimizer.get_stats() 