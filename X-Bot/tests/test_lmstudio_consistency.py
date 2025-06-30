#!/usr/bin/env python3
"""
Test pour vérifier la cohérence de la configuration LM Studio
Vérifie que tous les fichiers de config sont synchronisés
"""

import json
import os

class TestLMStudioConsistency:
    def __init__(self):
        print("🔧 Test Cohérence Configuration LM Studio")
        print("=" * 60)
        
    def test_config_files_consistency(self):
        """Test la cohérence entre config.json et prompts.json"""
        print("\n1. 🔍 Test Cohérence Config Files")
        print("-" * 40)
        
        try:
            # Charger config.json
            with open('config/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Charger prompts.json
            with open('config/prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            print("📄 Configuration actuelle:")
            
            # Vérifier config.json
            content_gen = config['content_generation']
            print(f"   config.json - Provider: {content_gen['provider']}")
            print(f"   config.json - Model: {content_gen['model']}")
            
            # Vérifier prompts.json  
            tweet_settings = prompts['settings']['tweet_generation']
            reply_settings = prompts['settings']['auto_reply']
            print(f"   prompts.json Tweet - Provider: {tweet_settings['provider']}")
            print(f"   prompts.json Tweet - Model: {tweet_settings['model']}")
            print(f"   prompts.json Reply - Provider: {reply_settings['provider']}")
            print(f"   prompts.json Reply - Model: {reply_settings['model']}")
            
            # Vérifications de cohérence
            consistency_checks = [
                ("config.json utilise 'auto'", content_gen['provider'] == 'auto'),
                ("config.json utilise gpt-4o-mini", content_gen['model'] == 'gpt-4o-mini'),
                ("prompts.json tweet utilise 'auto'", tweet_settings['provider'] == 'auto'),
                ("prompts.json tweet utilise gpt-4o-mini", tweet_settings['model'] == 'gpt-4o-mini'),
                ("prompts.json reply utilise 'auto'", reply_settings['provider'] == 'auto'),
                ("prompts.json reply utilise gpt-4o-mini", reply_settings['model'] == 'gpt-4o-mini'),
                ("Force LLM activé", reply_settings.get('force_llm', False))
            ]
            
            print("\n🔍 Vérifications cohérence:")
            all_consistent = True
            for check_name, check_result in consistency_checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
                if not check_result:
                    all_consistent = False
            
            return all_consistent
            
        except Exception as e:
            print(f"❌ Erreur test cohérence: {e}")
            return False
    
    def test_lmstudio_optimization(self):
        """Test des optimisations spécifiques à LM Studio"""
        print("\n2. ⚡ Test Optimisations LM Studio")
        print("-" * 40)
        
        try:
            with open('config/prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            reply_settings = prompts['settings']['auto_reply']
            
            # Vérifications optimisations LM Studio
            optimizations = [
                ("Température élevée (créativité)", reply_settings['temperature'] >= 0.8),
                ("Max tokens limités (rapidité)", reply_settings['max_tokens'] <= 100),
                ("Force LLM activé", reply_settings.get('force_llm', False)),
                ("Modèles alternatifs définis", len(reply_settings.get('alternative_models', [])) > 0)
            ]
            
            print("⚡ Optimisations LM Studio:")
            all_optimized = True
            for opt_name, opt_result in optimizations:
                status = "✅" if opt_result else "❌"
                print(f"   {status} {opt_name}")
                if not opt_result:
                    all_optimized = False
            
            return all_optimized
            
        except Exception as e:
            print(f"❌ Erreur test optimisations: {e}")
            return False
    
    def test_fallback_configuration(self):
        """Test de la configuration fallback"""
        print("\n3. 🔄 Test Configuration Fallback")
        print("-" * 40)
        
        try:
            with open('config/prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            reply_settings = prompts['settings']['auto_reply']
            alternative_models = reply_settings.get('alternative_models', [])
            
            print(f"📋 Modèles alternatifs: {alternative_models}")
            
            # Vérifications fallback
            fallback_checks = [
                ("gpt-4o-mini dans fallback", "gpt-4o-mini" in alternative_models),
                ("gpt-4o dans fallback", "gpt-4o" in alternative_models),
                ("Au moins 3 modèles fallback", len(alternative_models) >= 3),
                ("Provider 'auto' pour fallback", prompts['settings']['tweet_generation']['provider'] == 'auto')
            ]
            
            print("🔄 Configuration fallback:")
            all_fallback_ok = True
            for check_name, check_result in fallback_checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
                if not check_result:
                    all_fallback_ok = False
            
            return all_fallback_ok
            
        except Exception as e:
            print(f"❌ Erreur test fallback: {e}")
            return False
    
    def run_all_tests(self):
        """Lance tous les tests de cohérence"""
        tests = [
            ("Cohérence Config Files", self.test_config_files_consistency),
            ("Optimisations LM Studio", self.test_lmstudio_optimization),
            ("Configuration Fallback", self.test_fallback_configuration)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
                status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                results.append((test_name, False))
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ COHÉRENCE LM STUDIO")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Score: {passed}/{total} tests passés")
        
        if passed == total:
            print("🎉 CONFIGURATION PARFAITEMENT HARMONISÉE !")
            print("\n🔧 Configuration LM Studio complète:")
            print("   1. ✅ Provider 'auto' partout (détection LM Studio)")
            print("   2. ✅ Modèle gpt-4o-mini cohérent")
            print("   3. ✅ Fallback automatique configuré")
            print("   4. ✅ Optimisations LM Studio actives")
            print("   5. ✅ Force LLM pour les réponses")
        else:
            print("⚠️ Des incohérences persistent.")
        
        return passed == total

if __name__ == "__main__":
    # Vérifier que les fichiers existent
    if not os.path.exists('config/config.json') or not os.path.exists('config/prompts.json'):
        print("❌ Erreur: Fichiers de configuration manquants")
        exit(1)
    
    tester = TestLMStudioConsistency()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Votre configuration est optimale pour LM Studio !")
        print("💡 Le bot utilisera LM Studio en priorité avec fallback OpenAI.")
    else:
        print("\n❌ Configuration incomplète.")
    
    exit(0 if success else 1) 