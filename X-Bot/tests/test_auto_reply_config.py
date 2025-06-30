#!/usr/bin/env python3
"""
Test des Configurations de Réponses Automatiques

Vérifie les options de désactivation et limites par conversation.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config_manager


def test_auto_reply_disabled():
    """Test que les réponses automatiques sont désactivées"""
    print("\n🚫 TEST DÉSACTIVATION RÉPONSES AUTOMATIQUES")
    print("=" * 50)
    
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        # Vérifier que auto_reply est désactivé
        auto_reply_enabled = config.engagement.auto_reply_enabled
        print(f"📋 auto_reply_enabled: {auto_reply_enabled}")
        
        if not auto_reply_enabled:
            print("✅ Réponses automatiques DÉSACTIVÉES")
            return True
        else:
            print("❌ Réponses automatiques encore ACTIVÉES")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_conversation_limits():
    """Test des limites par conversation"""
    print("\n🔒 TEST LIMITES PAR CONVERSATION")
    print("=" * 40)
    
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        # Vérifier la nouvelle limite
        max_per_conversation = config.engagement.max_replies_per_conversation
        print(f"📋 max_replies_per_conversation: {max_per_conversation}")
        
        # Vérifier autres limites
        max_per_day = config.engagement.max_replies_per_day
        print(f"📋 max_replies_per_day: {max_per_day}")
        
        # Vérifier intervalle
        interval = config.engagement.reply_check_interval_minutes
        print(f"📋 reply_check_interval_minutes: {interval}")
        
        if max_per_conversation >= 0 and max_per_conversation <= 5:
            print("✅ Limite par conversation configurée correctement")
            return True
        else:
            print("❌ Limite par conversation invalide")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_reply_handler_integration():
    """Test que ReplyHandler supporte les nouvelles limites"""
    print("\n🔗 TEST INTÉGRATION REPLY HANDLER")
    print("=" * 40)
    
    try:
        from core.reply_handler import ReplyHandler
        
        # Initialiser le handler
        reply_handler = ReplyHandler()
        
        # Vérifier que le cache des conversations existe
        if hasattr(reply_handler, '_conversation_replies'):
            print("✅ Cache des conversations initialisé")
        else:
            print("❌ Cache des conversations manquant")
            return False
        
        # Vérifier que le cache est vide au départ
        conversation_count = len(reply_handler._conversation_replies)
        print(f"📋 Conversations en cache: {conversation_count}")
        
        if conversation_count == 0:
            print("✅ Cache conversations vide au démarrage")
            return True
        else:
            print("⚠️ Cache conversations non vide au démarrage")
            return True  # Pas forcément une erreur
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def show_configuration_guide():
    """Affiche le guide de configuration"""
    print("\n📖 GUIDE DE CONFIGURATION")
    print("=" * 50)
    
    print("\n🎛️ Fichier: config/config.json")
    print("   Section: engagement")
    print("")
    
    print("🚫 DÉSACTIVER COMPLÈTEMENT:")
    print('   "auto_reply_enabled": false')
    print("")
    
    print("⚙️ CONTRÔLER LES LIMITES:")
    print('   "max_replies_per_day": 20          // Limite quotidienne globale')
    print('   "max_replies_per_conversation": 1  // Limite par discussion')
    print('   "reply_check_interval_minutes": 1  // Fréquence de vérification')
    print("")
    
    print("📝 EXEMPLES D'USAGE:")
    print("   🔇 Silence total:      auto_reply_enabled = false")
    print("   🤐 1 réponse par fil:  max_replies_per_conversation = 1")
    print("   💬 Discussions:       max_replies_per_conversation = 3")
    print("   🚀 Très actif:        max_replies_per_conversation = 5")
    print("")
    
    print("⏰ CONTRÔLER LA FRÉQUENCE:")
    print("   🔄 Très réactif:  reply_check_interval_minutes = 1")
    print("   ⏳ Modéré:       reply_check_interval_minutes = 5")
    print("   🐌 Lent:         reply_check_interval_minutes = 15")


def test_json_structure():
    """Test que la structure JSON est valide"""
    print("\n📄 TEST STRUCTURE JSON")
    print("=" * 30)
    
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Vérifier section engagement
        engagement = config_data.get("engagement", {})
        
        required_fields = [
            "auto_reply_enabled",
            "max_replies_per_day", 
            "max_replies_per_conversation",
            "reply_check_interval_minutes"
        ]
        
        print("📋 Champs requis:")
        all_present = True
        for field in required_fields:
            if field in engagement:
                value = engagement[field]
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ {field}: MANQUANT")
                all_present = False
        
        if all_present:
            print("✅ Structure JSON complète")
            return True
        else:
            print("❌ Structure JSON incomplète")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lecture JSON: {e}")
        return False


if __name__ == "__main__":
    print("🧪 TEST CONFIGURATION RÉPONSES AUTOMATIQUES")
    print("="*60)
    
    # Tests principaux
    test1 = test_json_structure()
    test2 = test_auto_reply_disabled()
    test3 = test_conversation_limits()
    test4 = test_reply_handler_integration()
    
    # Guide
    show_configuration_guide()
    
    # Résultat global
    print(f"\n{'='*60}")
    all_passed = all([test1, test2, test3, test4])
    
    if all_passed:
        print("🎉 CONFIGURATION RÉPONSES AUTOMATIQUES OK!")
        print("✅ Réponses désactivées")
        print("✅ Limites par conversation configurées")
        print("✅ Intégration ReplyHandler fonctionnelle")
        print("✅ Pour réactiver: config.json → auto_reply_enabled = true")
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        print("⚠️ Vérifier les erreurs ci-dessus") 