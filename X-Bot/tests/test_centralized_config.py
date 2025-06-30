#!/usr/bin/env python3
"""
Test de Centralisation Configuration Complète

Vérifie que toute la configuration est centralisée dans config.json
sans redondance entre les fichiers.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompt_manager import PromptManager


def test_configuration_centralization():
    """Test principal de centralisation"""
    print("\n🎯 TEST CENTRALISATION CONFIGURATION")
    print("=" * 50)
    
    success = True
    
    # 1. Vérifier que config.json contient TOUS les settings LLM
    print("\n1️⃣ Configuration centralisée dans config.json")
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        content_gen = config_data.get("content_generation", {})
        
        # Vérifier auto_reply settings
        auto_reply = content_gen.get("auto_reply", {})
        required_auto_reply = ["provider", "model", "max_tokens", "temperature", "force_llm"]
        
        print("   📋 Auto-reply settings:")
        for key in required_auto_reply:
            if key in auto_reply:
                print(f"      ✅ {key}: {auto_reply[key]}")
            else:
                print(f"      ❌ {key}: MANQUANT")
                success = False
        
        # Vérifier tweet_generation settings  
        tweet_gen = content_gen.get("tweet_generation", {})
        required_tweet = ["provider", "model", "max_tokens", "temperature"]
        
        print("   🐦 Tweet generation settings:")
        for key in required_tweet:
            if key in tweet_gen:
                print(f"      ✅ {key}: {tweet_gen[key]}")
            else:
                print(f"      ❌ {key}: MANQUANT")
                success = False
                
    except Exception as e:
        print(f"   ❌ Erreur lecture config.json: {e}")
        success = False
    
    # 2. Vérifier que prompts.json ne contient PLUS de settings
    print("\n2️⃣ Élimination redondance dans prompts.json")
    try:
        with open("config/prompts.json", 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        if "settings" in prompts_data:
            print("   ❌ ERREUR: Section 'settings' encore présente dans prompts.json")
            print(f"      → Settings trouvés: {list(prompts_data['settings'].keys())}")
            success = False
        else:
            print("   ✅ Section 'settings' supprimée de prompts.json")
        
        # Vérifier que les prompts sont toujours là
        required_sections = ["system_prompts", "user_prompts", "templates"]
        for section in required_sections:
            if section in prompts_data:
                print(f"   ✅ {section}: {len(prompts_data[section])} éléments")
            else:
                print(f"   ❌ {section}: MANQUANT")
                success = False
                
    except Exception as e:
        print(f"   ❌ Erreur lecture prompts.json: {e}")
        success = False
    
    # 3. Tester PromptManager avec la nouvelle architecture
    print("\n3️⃣ Test PromptManager centralisé")
    try:
        pm = PromptManager()
        
        # Test lecture settings depuis config.json
        auto_reply_settings = pm.get_setting("auto_reply")
        if auto_reply_settings and "force_llm" in auto_reply_settings:
            print(f"   ✅ Auto-reply settings: {auto_reply_settings}")
        else:
            print(f"   ❌ Échec lecture auto_reply settings")
            success = False
        
        # Test lecture prompts depuis prompts.json
        system_prompt = pm.get_system_prompt("auto_reply")
        if system_prompt and "content" in system_prompt:
            print(f"   ✅ System prompts: OK")
        else:
            print(f"   ❌ Échec lecture system prompts")
            success = False
        
        # Test templates
        templates = pm.get_template("crypto_topics")
        if templates and len(templates) > 0:
            print(f"   ✅ Templates: {len(templates)} crypto topics")
        else:
            print(f"   ❌ Échec lecture templates")
            success = False
            
    except Exception as e:
        print(f"   ❌ Erreur PromptManager: {e}")
        success = False
    
    # 4. Vérifier cohérence des paramètres
    print("\n4️⃣ Cohérence des paramètres")
    try:
        # Vérifier que les modèles sont cohérents
        auto_reply_model = pm.get_setting("auto_reply", "model")
        tweet_model = pm.get_setting("tweet_generation", "model")
        
        if auto_reply_model == tweet_model:
            print(f"   ✅ Modèles cohérents: {auto_reply_model}")
        else:
            print(f"   ⚠️ Modèles différents: auto_reply={auto_reply_model}, tweet={tweet_model}")
        
        # Vérifier provider
        auto_reply_provider = pm.get_setting("auto_reply", "provider")
        tweet_provider = pm.get_setting("tweet_generation", "provider")
        
        if auto_reply_provider == tweet_provider:
            print(f"   ✅ Providers cohérents: {auto_reply_provider}")
        else:
            print(f"   ⚠️ Providers différents: auto_reply={auto_reply_provider}, tweet={tweet_provider}")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification cohérence: {e}")
        success = False
    
    # 5. Test intégration complète
    print("\n5️⃣ Test intégration complète")
    try:
        # Simuler utilisation réelle
        system_prompt = pm.get_system_prompt("auto_reply")
        user_prompt = pm.get_user_prompt("auto_reply", username="TestUser", reply_content="Great tweet!")
        settings = pm.get_setting("auto_reply")
        
        print(f"   ✅ System prompt: {len(system_prompt['content'])} caractères")
        print(f"   ✅ User prompt: {len(user_prompt)} caractères")
        print(f"   ✅ Settings: {len(settings)} paramètres")
        
        # Vérifier force_llm
        if settings.get("force_llm") is True:
            print(f"   ✅ force_llm activé pour GPT/LLM")
        else:
            print(f"   ❌ force_llm non configuré")
            success = False
            
    except Exception as e:
        print(f"   ❌ Erreur test intégration: {e}")
        success = False
    
    # Résultat final
    print(f"\n{'='*50}")
    if success:
        print("🎉 CENTRALISATION RÉUSSIE!")
        print("✅ Configuration unifiée dans config.json")
        print("✅ Prompts isolés dans prompts.json")
        print("✅ Aucune redondance détectée")
        print("✅ PromptManager fonctionnel")
        return True
    else:
        print("❌ CENTRALISATION ÉCHOUÉE!")
        print("⚠️ Vérifier les erreurs ci-dessus")
        return False


def test_performance():
    """Test performance après centralisation"""
    print("\n⚡ TEST PERFORMANCE")
    print("=" * 30)
    
    import time
    
    start_time = time.time()
    pm = PromptManager()
    init_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(100):
        settings = pm.get_setting("auto_reply")
        prompt = pm.get_system_prompt("auto_reply")
    access_time = time.time() - start_time
    
    print(f"⚡ Init time: {init_time:.3f}s")
    print(f"⚡ 100 accès: {access_time:.3f}s")
    print(f"⚡ Moyenne: {access_time/100*1000:.2f}ms par accès")
    
    if init_time < 0.1 and access_time < 0.1:
        print("✅ Performance excellente")
        return True
    else:
        print("⚠️ Performance dégradée")
        return False


def show_final_structure():
    """Affiche la structure finale centralisée"""
    print("\n📁 STRUCTURE FINALE CENTRALISÉE")
    print("=" * 40)
    
    print("\n📄 config/config.json (CONFIGURATION):")
    print("   ├── content_generation/")
    print("   │   ├── provider: auto")
    print("   │   ├── model: gpt-4o-mini")
    print("   │   ├── auto_reply/")
    print("   │   │   ├── force_llm: true")
    print("   │   │   ├── temperature: 0.9")
    print("   │   │   └── max_tokens: 60")
    print("   │   └── tweet_generation/")
    print("   │       ├── temperature: 0.7")
    print("   │       └── max_tokens: 150")
    print("   ├── engagement/")
    print("   ├── monitoring/")
    print("   └── storage/")
    
    print("\n📄 config/prompts.json (PROMPTS SEULEMENT):")
    print("   ├── system_prompts/")
    print("   │   ├── tweet_generation")
    print("   │   └── auto_reply")
    print("   ├── user_prompts/")
    print("   │   ├── tweet_generation")
    print("   │   └── auto_reply")
    print("   └── templates/")
    print("       ├── crypto_topics")
    print("       ├── simple_replies")
    print("       └── image_themes")
    
    print("\n🎯 AVANTAGES:")
    print("   ✅ Configuration centralisée")
    print("   ✅ Aucune duplication")
    print("   ✅ Maintenance simplifiée")
    print("   ✅ Source unique de vérité")


if __name__ == "__main__":
    print("🔧 TEST CENTRALISATION CONFIGURATION COMPLÈTE")
    print("="*60)
    
    # Tests principaux
    config_ok = test_configuration_centralization()
    perf_ok = test_performance()
    
    # Affichage structure
    show_final_structure()
    
    # Résultat global
    print(f"\n{'='*60}")
    if config_ok and perf_ok:
        print("🎉 CENTRALISATION COMPLÈTE RÉUSSIE!")
        print("🚀 Le système est prêt avec configuration unifiée!")
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        print("⚠️ Vérifier les erreurs ci-dessus") 