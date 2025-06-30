#!/usr/bin/env python3
"""
Script de test pour le système de prompts centralisés
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from core.prompt_manager import get_prompt_manager, reload_prompts


def test_prompt_loading():
    """Test du chargement des prompts"""
    
    print("🔧 Test Prompt Loading")
    print("======================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test stats
        stats = prompt_manager.get_stats()
        print(f"✅ Prompts loaded from: {stats['prompts_file']}")
        print(f"   • System prompts: {stats['system_prompts_count']}")
        print(f"   • User prompts: {stats['user_prompts_count']}")
        print(f"   • Templates: {stats['templates_count']}")
        print(f"   • Settings: {stats['settings_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_system_prompts():
    """Test des prompts système"""
    
    print("\n🤖 Test System Prompts")
    print("======================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test tweet generation prompt
        tweet_prompt = prompt_manager.get_system_prompt("tweet_generation")
        print(f"✅ Tweet generation prompt: {tweet_prompt['role']}")
        print(f"   Content length: {len(tweet_prompt['content'])} chars")
        
        # Test auto-reply prompt
        reply_prompt = prompt_manager.get_system_prompt("auto_reply")
        print(f"✅ Auto-reply prompt: {reply_prompt['role']}")
        print(f"   Content length: {len(reply_prompt['content'])} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_user_prompts():
    """Test des prompts utilisateur avec variables"""
    
    print("\n👤 Test User Prompts")
    print("===================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test tweet generation avec variables
        tweet_prompt = prompt_manager.get_user_prompt(
            "tweet_generation",
            inspiration="1. Topic: crypto\n   Style: enthusiastic\n   Virality: 500 points",
            recent_topics="Solana, DeFi, NFT"
        )
        print(f"✅ Tweet generation prompt generated")
        print(f"   Length: {len(tweet_prompt)} chars")
        print(f"   Contains inspiration: {'inspiration' in tweet_prompt.lower()}")
        
        # Test auto-reply avec variables
        reply_prompt = prompt_manager.get_user_prompt(
            "auto_reply",
            reply_content="Great project! Love the innovation."
        )
        print(f"✅ Auto-reply prompt generated")
        print(f"   Length: {len(reply_prompt)} chars")
        print(f"   Contains reply content: {'Great project' in reply_prompt}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_templates():
    """Test des templates"""
    
    print("\n📝 Test Templates")
    print("=================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test simple replies
        simple_replies = prompt_manager.get_simple_replies()
        print(f"✅ Simple replies: {len(simple_replies)} templates")
        for i, reply in enumerate(simple_replies[:3], 1):
            print(f"   {i}. {reply}")
        
        # Test crypto topics
        crypto_topics = prompt_manager.get_crypto_topics()
        print(f"✅ Crypto topics: {len(crypto_topics)} topics")
        print(f"   Examples: {', '.join(crypto_topics[:3])}")
        
        # Test image themes
        image_themes = prompt_manager.get_template("image_themes")
        print(f"✅ Image themes: {len(image_themes)} themes")
        print(f"   Available: {', '.join(image_themes.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_settings():
    """Test des settings"""
    
    print("\n⚙️ Test Settings")
    print("================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test tweet generation settings
        tweet_settings = prompt_manager.get_setting("tweet_generation")
        print(f"✅ Tweet generation settings:")
        print(f"   Model: {tweet_settings['model']}")
        print(f"   Max tokens: {tweet_settings['max_tokens']}")
        print(f"   Temperature: {tweet_settings['temperature']}")
        
        # Test setting individuel
        reply_model = prompt_manager.get_setting("auto_reply", "model")
        print(f"✅ Auto-reply model: {reply_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_image_prompts():
    """Test de génération de prompts d'images"""
    
    print("\n🖼️ Test Image Prompts")
    print("=====================")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test différents thèmes
        themes = ["crypto", "tech", "business", "trends", "default"]
        
        for theme in themes:
            image_prompt = prompt_manager.get_image_prompt(
                "Test crypto content about Solana", 
                theme
            )
            print(f"✅ {theme.capitalize()} theme: {len(image_prompt)} chars")
            print(f"   Preview: {image_prompt[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_hot_reload():
    """Test du hot-reload"""
    
    print("\n🔄 Test Hot Reload")
    print("==================")
    
    try:
        # Test reload
        success = reload_prompts()
        print(f"✅ Hot reload: {'Success' if success else 'Failed'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Test complet du système de prompts"""
    
    print("🎯 TEST SYSTÈME PROMPTS CENTRALISÉS")
    print("===================================")
    
    results = {}
    
    # Test chaque composant
    results['loading'] = test_prompt_loading()
    results['system_prompts'] = test_system_prompts()
    results['user_prompts'] = test_user_prompts()
    results['templates'] = test_templates()
    results['settings'] = test_settings()
    results['image_prompts'] = test_image_prompts()
    results['hot_reload'] = test_hot_reload()
    
    # Résumé
    print("\n📋 RÉSUMÉ DES TESTS")
    print("==================")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component.upper().replace('_', ' ')}: {status}")
    
    print(f"\nRésultat: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Système de prompts centralisés opérationnel !")
    else:
        print("⚠️ Certains tests ont échoué")
    
    # Test intégration avec les composants existants
    print("\n🔗 Test Intégration")
    print("===================")
    
    try:
        from generator import get_content_generator
        from reply_handler import get_reply_handler
        
        print("✅ Generator importé avec prompt_manager")
        print("✅ Reply handler importé avec prompt_manager")
        print("✅ Intégration réussie !")
        
    except Exception as e:
        print(f"❌ Erreur d'intégration: {e}")


if __name__ == "__main__":
    main() 