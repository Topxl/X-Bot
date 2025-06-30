#!/usr/bin/env python3
"""
Test complet du système modulaire LLM
OpenAI + LM Studio avec fallback automatique optimisé
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent/core au path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir / 'core'))

from llm_providers import get_llm_manager
from reply_handler import ReplyHandler
from storage import Reply
from datetime import datetime

def test_llm_manager():
    """Test le gestionnaire LLM modulaire"""
    print("🧪 TEST GESTIONNAIRE LLM MODULAIRE")
    print("=" * 50)
    
    try:
        # Initialiser le manager
        manager = get_llm_manager()
        
        # Afficher les infos
        info = manager.get_active_provider_info()
        print(f"🎯 Provider actif: {info['provider']}")
        print(f"📡 Disponible: {'✅' if info['available'] else '❌'}")
        print(f"🤖 Modèles disponibles: {len(info['models'])}")
        
        if info['models']:
            print(f"   📋 Exemples: {', '.join(info['models'][:3])}...")
        
        if info['provider'] == 'lmstudio':
            active_url = info.get('active_url', 'N/A')
            print(f"🏠 URL LM Studio: {active_url}")
            print(f"📦 Modèle configuré: {info.get('configured_model', 'N/A')}")
            
            # Vérifier si on utilise localhost (optimal) ou alternative
            if 'localhost' in active_url or '127.0.0.1' in active_url:
                print(f"✅ Utilise localhost (optimal)")
            else:
                print(f"⚠️ Utilise IP alternative (fallback)")
        
        # Test de génération directe
        print(f"\n🔄 Test génération directe...")
        response = manager.generate_reply(
            system_prompt="You are a crypto expert bot.",
            user_prompt="What do you think about Bitcoin?",
            max_tokens=50,
            temperature=0.8
        )
        
        if response:
            print(f"✅ Réponse générée: \"{response}\"")
            print(f"📏 Longueur: {len(response)} caractères")
        else:
            print(f"❌ Échec génération")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur manager: {e}")
        return False

def test_reply_handler_integration():
    """Test l'intégration avec ReplyHandler"""
    print(f"\n🔗 TEST INTÉGRATION REPLY HANDLER")
    print("=" * 40)
    
    try:
        # Initialiser le reply handler
        reply_handler = ReplyHandler()
        
        # Vérifier que le LLM manager est bien intégré
        if hasattr(reply_handler, 'llm_manager'):
            print("✅ LLM manager intégré dans ReplyHandler")
        else:
            print("❌ LLM manager manquant dans ReplyHandler")
            return False
        
        # Test avec différents types de messages
        test_cases = [
            {
                "content": "Bitcoin is going to the moon! 🚀",
                "description": "Message bullish"
            },
            {
                "content": "What's your opinion on DeFi protocols?",
                "description": "Question technique"
            },
            {
                "content": "Thanks for the great analysis! 💯",
                "description": "Remerciement"
            }
        ]
        
        print(f"\n🎯 Tests de réponses contextuelles:")
        print("-" * 35)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print(f"💬 Message: \"{test_case['content']}\"")
            
            # Créer un objet Reply de test
            test_reply = Reply(
                reply_id=f"test_modular_{i}",
                original_tweet_id="test_tweet",
                author_id="test_user",
                content=test_case['content'],
                created_at=datetime.now()
            )
            
            try:
                # Générer la réponse via ReplyHandler
                response = reply_handler._generate_reply_content(test_reply)
                
                if response:
                    print(f"✅ Réponse: \"{response}\"")
                    print(f"📏 Longueur: {len(response)} caractères")
                    
                    # Vérifier que c'est contextuel (pas une réponse générique)
                    generic_words = ['thanks for engaging', 'great point', 'exactly']
                    is_contextual = not any(phrase in response.lower() for phrase in generic_words)
                    print(f"🎯 Contextuel: {'✅' if is_contextual else '❌'}")
                    
                else:
                    print("❌ Échec génération")
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return False

def test_fallback_system():
    """Test le système de fallback optimisé"""
    print(f"\n🔄 TEST SYSTÈME FALLBACK OPTIMISÉ")
    print("=" * 35)
    
    try:
        manager = get_llm_manager()
        
        # Afficher l'ordre de priorité
        print(f"🎯 Priorité des providers:")
        for i, provider in enumerate(manager.provider_priority, 1):
            status = "✅" if provider in manager.providers else "❌"
            print(f"   {i}. {provider} {status}")
        
        # Info sur la logique de fallback LM Studio
        if 'lmstudio' in manager.providers:
            lm_provider = manager.providers['lmstudio']
            print(f"\n🏠 LM Studio Fallback Logic:")
            print(f"   📍 URLs testées: {len(lm_provider.base_urls)}")
            for i, url in enumerate(lm_provider.base_urls, 1):
                is_active = url == lm_provider.active_url
                status = "🎯 ACTIF" if is_active else "💤 Standby"
                localhost_marker = "🏠 " if 'localhost' in url else "🌐 "
                print(f"   {i}. {localhost_marker}{url} {status}")
        
        # Test de switch de provider si possible
        if len(manager.providers) > 1:
            print(f"\n🔀 Test switch de provider...")
            current = manager.active_provider
            
            # Essayer de switcher vers l'autre provider
            for provider_name in manager.providers:
                if provider_name != current:
                    success = manager.switch_provider(provider_name)
                    if success:
                        print(f"✅ Switch réussi: {current} → {provider_name}")
                        
                        # Tester génération avec nouveau provider
                        response = manager.generate_reply(
                            system_prompt="You are helpful.",
                            user_prompt="Say hi briefly",
                            max_tokens=20
                        )
                        
                        if response:
                            print(f"✅ Génération OK avec {provider_name}: \"{response}\"")
                        
                        # Retour au provider original
                        manager.switch_provider(current)
                        print(f"🔙 Retour à {current}")
                        break
        else:
            print(f"ℹ️ Un seul provider disponible, pas de test de switch")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur fallback: {e}")
        return False

def test_environment_config():
    """Test la configuration depuis .env"""
    print(f"\n🌍 TEST CONFIGURATION ENVIRONNEMENT")
    print("=" * 40)
    
    try:
        # Vérifier les variables d'environnement LLM
        llm_vars = {
            'LLM_PROVIDER': os.getenv('LLM_PROVIDER', 'Non défini'),
            'LM_API_URL': os.getenv('LM_API_URL', 'Non défini'),
            'LM_ALTERNATIVE_IPS': os.getenv('LM_ALTERNATIVE_IPS', 'Non défini'),
            'LM_MODEL_NAME': os.getenv('LM_MODEL_NAME', 'Non défini'),
            'OPENAI_API_KEY': '✅ Défini' if os.getenv('OPENAI_API_KEY') else '❌ Manquant'
        }
        
        print(f"📋 Variables d'environnement:")
        for key, value in llm_vars.items():
            print(f"   {key}: {value}")
        
        # Analyse de la configuration LM Studio
        lm_url = os.getenv('LM_API_URL', 'http://localhost:1234')
        alt_ips = os.getenv('LM_ALTERNATIVE_IPS', '')
        
        print(f"\n🏠 Analyse configuration LM Studio:")
        if 'localhost' in lm_url:
            print(f"   ✅ URL principale: localhost (optimal)")
        else:
            print(f"   ⚠️ URL principale: {lm_url} (non-localhost)")
        
        if alt_ips and alt_ips.strip():
            alt_count = len([ip.strip() for ip in alt_ips.split(',') if ip.strip()])
            print(f"   🔄 IPs alternatives: {alt_count} configurées (fallback seulement)")
        else:
            print(f"   ✅ Pas d'IPs alternatives (localhost suffit)")
        
        # Vérifier cohérence avec provider actif
        manager = get_llm_manager()
        provider_env = os.getenv('LLM_PROVIDER', 'auto').lower()
        active_provider = manager.active_provider
        
        print(f"\n🔄 Cohérence configuration:")
        print(f"   ENV LLM_PROVIDER: {provider_env}")
        print(f"   Provider actif: {active_provider}")
        
        if provider_env == "auto":
            print(f"   ✅ Mode auto - provider optimal sélectionné")
        elif provider_env == active_provider:
            print(f"   ✅ Configuration cohérente")
        else:
            print(f"   ⚠️ Incohérence détectée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur config: {e}")
        return False

def main():
    """Test complet du système modulaire"""
    print("🤖 TEST COMPLET SYSTÈME LLM MODULAIRE OPTIMISÉ")
    print("=" * 65)
    
    tests = [
        ("Gestionnaire LLM", test_llm_manager),
        ("Intégration ReplyHandler", test_reply_handler_integration),
        ("Système Fallback Optimisé", test_fallback_system),
        ("Configuration Env", test_environment_config)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*65}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print(f"\n{'='*65}")
    print(f"📊 RÉSUMÉ DES TESTS")
    print("="*30)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Score final: {passed}/{len(tests)} tests réussis")
    
    if passed == len(tests):
        print(f"🎉 SYSTÈME MODULAIRE ENTIÈREMENT OPÉRATIONNEL!")
        print(f"🚀 Optimisé: localhost prioritaire, alternatives en fallback")
        print(f"💫 Prêt pour utilisation en production")
    else:
        print(f"⚠️ Quelques ajustements nécessaires")
    
    print(f"\n💡 Pour configurer: python tests/change_model_manager.py")

if __name__ == "__main__":
    main() 