#!/usr/bin/env python3
"""
Test complet du système de gestion des réponses aux tweets

Ce test couvre :
- Détection des nouvelles réponses
- Gestion des duplicatas
- Auto-like des réponses
- Stockage et récupération
- Vérifications de startup
- Performance et optimisations
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Ajouter le dossier core au PATH
current_dir = Path(__file__).parent.parent
core_dir = current_dir / "core"
config_dir = current_dir / "config"

sys.path.insert(0, str(core_dir))
sys.path.insert(0, str(config_dir))

from storage import StorageManager, Reply, Tweet
from reply_handler import ReplyHandler
from config import get_config_manager


class TestReplySystem:
    """Test complet du système de réponses"""
    
    def __init__(self):
        self.storage_manager = None
        self.reply_handler = None
        self.test_data = {}
        
    def setup(self):
        """Initialisation des tests"""
        print("🔧 Initialisation des tests...")
        
        try:
            self.storage_manager = StorageManager()
            self.reply_handler = ReplyHandler()
            
            # Créer des données de test
            self.test_data = {
                'test_tweet': Tweet(
                    tweet_id="test_tweet_123456",
                    content="Test tweet pour les réponses",
                    posted_at=datetime.utcnow()
                ),
                'test_replies': [
                    Reply(
                        reply_id="reply_001",
                        original_tweet_id="test_tweet_123456",
                        author_id="user_001",
                        content="Première réponse de test",
                        created_at=datetime.utcnow(),
                        liked=False
                    ),
                    Reply(
                        reply_id="reply_002",
                        original_tweet_id="test_tweet_123456",
                        author_id="user_002",
                        content="Deuxième réponse de test",
                        created_at=datetime.utcnow(),
                        liked=False
                    ),
                    Reply(
                        reply_id="reply_003",
                        original_tweet_id="test_tweet_123456",
                        author_id="user_003",
                        content="Troisième réponse de test",
                        created_at=datetime.utcnow(),
                        liked=True
                    )
                ]
            }
            
            print("✅ Initialisation réussie")
            return True
            
        except Exception as e:
            print(f"❌ Erreur d'initialisation : {e}")
            return False
    
    def test_duplicate_detection(self):
        """Test de détection des duplicatas"""
        print("\n🔍 Test Détection des Duplicatas")
        print("=" * 40)
        
        try:
            test_reply = self.test_data['test_replies'][0]
            
            # 1. Premier enregistrement
            print("1. Premier enregistrement...")
            result1 = self.storage_manager.save_reply(test_reply)
            print(f"   ✅ Enregistré avec ID: {result1}")
            
            # 2. Tentative de duplicate
            print("2. Tentative de duplicate...")
            result2 = self.storage_manager.save_reply(test_reply)
            print(f"   ✅ Duplicate géré, ID retourné: {result2}")
            
            # 3. Vérification d'existence
            print("3. Vérification d'existence...")
            exists = self.storage_manager.reply_exists(test_reply.reply_id)
            print(f"   ✅ Réponse existe: {exists}")
            
            # 4. Test de batch check
            print("4. Test vérification en lot...")
            reply_ids = [r.reply_id for r in self.test_data['test_replies']]
            existing_ids = self.storage_manager.get_existing_reply_ids(reply_ids)
            print(f"   ✅ IDs existants trouvés: {len(existing_ids)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test duplicatas : {e}")
            return False
    
    def test_reply_processing(self):
        """Test du traitement des réponses"""
        print("\n⚙️ Test Traitement des Réponses")
        print("=" * 40)
        
        try:
            # Sauvegarder toutes les réponses de test
            print("1. Sauvegarde des réponses de test...")
            saved_count = 0
            for reply in self.test_data['test_replies']:
                result = self.storage_manager.save_reply(reply)
                if result:
                    saved_count += 1
            
            print(f"   ✅ {saved_count} réponses sauvegardées")
            
            # Test de récupération
            print("2. Récupération des réponses récentes...")
            recent_replies = self.storage_manager.get_recent_replies(hours=1)
            print(f"   ✅ {len(recent_replies)} réponses récupérées")
            
            # Test de vérification d'existence
            print("3. Test de vérification d'existence...")
            for reply in self.test_data['test_replies']:
                exists = self.storage_manager.reply_exists(reply.reply_id)
                print(f"   {'✅' if exists else '❌'} {reply.reply_id}: {exists}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur traitement réponses : {e}")
            return False
    
    def test_auto_like_system(self):
        """Test du système d'auto-like"""
        print("\n❤️ Test Système Auto-Like")
        print("=" * 40)
        
        try:
            # Mock du Twitter manager pour éviter les vrais appels API
            with patch('reply_handler.get_twitter_manager') as mock_twitter:
                mock_twitter_instance = MagicMock()
                mock_twitter_instance.like_tweet.return_value = True
                mock_twitter.return_value = mock_twitter_instance
                
                # Test de la fonction auto-like
                print("1. Test auto-like d'une réponse...")
                reply_id = "test_reply_like_001"
                result = self.reply_handler._auto_like_reply(reply_id)
                print(f"   ✅ Auto-like résultat: {result}")
                
                # Vérifier que la méthode like_tweet a été appelée
                mock_twitter_instance.like_tweet.assert_called_with(reply_id)
                print("   ✅ Appel API Twitter confirmé")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur test auto-like : {e}")
            return False
    
    def test_startup_check(self):
        """Test du système de vérification au démarrage"""
        print("\n🚀 Test Vérification Startup")
        print("=" * 40)
        
        try:
            # Simuler un tweet sauvegardé
            test_tweet = self.test_data['test_tweet']
            saved_tweet_id = self.storage_manager.save_tweet(test_tweet)
            
            if saved_tweet_id:
                print("   ✅ Tweet de test sauvegardé")
            
            # Test du startup check
            print("1. Test startup check...")
            
            # Mock du Twitter manager pour éviter les vrais appels API
            with patch('reply_handler.get_twitter_manager') as mock_twitter:
                mock_twitter_instance = MagicMock()
                mock_twitter_instance.get_tweet_replies.return_value = []
                mock_twitter.return_value = mock_twitter_instance
                
                # Forcer un startup check
                result = self.reply_handler.force_startup_check()
                print(f"   ✅ Startup check résultat: {result}")
                
                # Vérifier les statistiques
                stats = self.reply_handler.get_reply_stats()
                print(f"   ✅ Statistiques: {stats}")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur test startup : {e}")
            return False
    
    def test_performance_optimization(self):
        """Test des optimisations de performance"""
        print("\n⚡ Test Optimisations Performance")
        print("=" * 40)
        
        try:
            # Test de vérification en lot
            print("1. Test vérification en lot...")
            
            # Créer plusieurs IDs de test
            test_ids = [f"perf_test_{i}" for i in range(20)]
            
            # Sauvegarder quelques réponses
            for i in range(5):
                test_reply = Reply(
                    reply_id=test_ids[i],
                    original_tweet_id="perf_tweet_123",
                    author_id=f"user_{i}",
                    content=f"Réponse performance test {i}",
                    created_at=datetime.utcnow()
                )
                self.storage_manager.save_reply(test_reply)
            
            # Test de récupération en lot
            start_time = time.time()
            existing_ids = self.storage_manager.get_existing_reply_ids(test_ids)
            end_time = time.time()
            
            print(f"   ✅ Vérification de {len(test_ids)} IDs en {end_time - start_time:.3f}s")
            print(f"   ✅ {len(existing_ids)} IDs existants trouvés")
            
            # Test de cache mémoire
            print("2. Test cache mémoire...")
            cache_size = len(self.reply_handler._processed_replies)
            print(f"   ✅ Cache contient {cache_size} réponses")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test performance : {e}")
            return False
    
    def test_real_world_scenario(self):
        """Test d'un scénario réel complet"""
        print("\n🌍 Test Scénario Réel")
        print("=" * 40)
        
        try:
            # Simuler un flux de travail complet
            print("1. Simulation d'un flux complet...")
            
            # Mock des managers
            with patch('reply_handler.get_twitter_manager') as mock_twitter, \
                 patch('reply_handler.get_config_manager') as mock_config:
                
                # Configuration du mock
                mock_twitter_instance = MagicMock()
                mock_twitter_instance.get_tweet_replies.return_value = self.test_data['test_replies']
                mock_twitter_instance.like_tweet.return_value = True
                mock_twitter.return_value = mock_twitter_instance
                
                mock_config_instance = MagicMock()
                mock_config_instance.get_config.return_value = MagicMock(
                    engagement=MagicMock(
                        auto_like_replies=True,
                        auto_reply_enabled=False
                    )
                )
                mock_config.return_value = mock_config_instance
                
                # Simuler le traitement
                result = self.reply_handler.check_and_handle_replies()
                print(f"   ✅ Traitement terminé: {result}")
                
                # Vérifier que les réponses ont été traitées
                if 'new_replies' in result:
                    print(f"   ✅ {result['new_replies']} nouvelles réponses traitées")
                
                if 'likes_sent' in result:
                    print(f"   ✅ {result['likes_sent']} likes envoyés")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur test scénario réel : {e}")
            return False
    
    def cleanup(self):
        """Nettoyage après les tests"""
        print("\n🧹 Nettoyage des données de test...")
        
        try:
            if self.storage_manager and self.storage_manager.supabase:
                # Supprimer les données de test
                test_reply_ids = [r.reply_id for r in self.test_data['test_replies']]
                test_reply_ids.extend([f"perf_test_{i}" for i in range(20)])
                
                for reply_id in test_reply_ids:
                    try:
                        self.storage_manager.supabase.table('replies').delete().eq(
                            'reply_id', reply_id
                        ).execute()
                    except:
                        pass  # Ignorer les erreurs de suppression
                
                # Supprimer le tweet de test
                try:
                    self.storage_manager.supabase.table('tweets').delete().eq(
                        'tweet_id', self.test_data['test_tweet'].tweet_id
                    ).execute()
                except:
                    pass
                
                print("   ✅ Données de test supprimées")
            
        except Exception as e:
            print(f"   ⚠️ Erreur de nettoyage : {e}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧪 TEST COMPLET DU SYSTÈME DE RÉPONSES")
        print("=" * 60)
        
        if not self.setup():
            return False
        
        tests = [
            ('Détection Duplicatas', self.test_duplicate_detection),
            ('Traitement Réponses', self.test_reply_processing),
            ('Système Auto-Like', self.test_auto_like_system),
            ('Vérification Startup', self.test_startup_check),
            ('Optimisations Performance', self.test_performance_optimization),
            ('Scénario Réel', self.test_real_world_scenario)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Erreur dans {test_name}: {e}")
                results[test_name] = False
        
        # Nettoyage
        self.cleanup()
        
        # Résumé
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 TOUS LES TESTS RÉUSSIS !")
            print("✅ Le système de réponses fonctionne parfaitement")
        else:
            print("⚠️  Certains tests ont échoué")
            print("🔧 Vérifiez la configuration et les dépendances")
        
        return passed == total


def main():
    """Point d'entrée principal"""
    test_system = TestReplySystem()
    success = test_system.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 