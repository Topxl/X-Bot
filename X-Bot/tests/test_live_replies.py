#!/usr/bin/env python3
"""
Test en direct du système de réponses avec de vraies données Twitter

⚠️  ATTENTION: Ce test utilise de vraies API Twitter
   Utilisez avec modération pour éviter les limites de rate limit
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le dossier core au PATH
current_dir = Path(__file__).parent.parent
core_dir = current_dir / "core"
config_dir = current_dir / "config"

sys.path.insert(0, str(core_dir))
sys.path.insert(0, str(config_dir))

from storage import StorageManager
from reply_handler import ReplyHandler
from twitter_api import get_twitter_manager
from config import get_config_manager


class LiveReplyTester:
    """Testeur en direct du système de réponses"""
    
    def __init__(self):
        self.storage_manager = StorageManager()
        self.reply_handler = ReplyHandler()
        self.twitter_manager = get_twitter_manager()
        self.config_manager = get_config_manager()
    
    def test_recent_tweets_replies(self, hours=2):
        """Test sur les tweets récents (mode sécurisé)"""
        print(f"🔍 Test Réponses - Tweets des {hours}h dernières")
        print("=" * 50)
        
        try:
            # Récupérer nos tweets récents
            our_tweets = self.storage_manager.get_recent_tweets(hours=hours)
            
            if not our_tweets:
                print("❌ Aucun tweet récent trouvé")
                print("💡 Publiez d'abord quelques tweets pour tester les réponses")
                return False
            
            print(f"📊 {len(our_tweets)} tweets trouvés")
            
            total_replies = 0
            
            for i, tweet in enumerate(our_tweets[:3]):  # Limiter à 3 tweets max
                print(f"\n📝 Tweet {i+1}: {tweet.tweet_id}")
                print(f"   Contenu: {tweet.content[:50]}...")
                
                try:
                    # Chercher les réponses (max 5 pour éviter rate limit)
                    replies = self.twitter_manager.get_tweet_replies(
                        tweet.tweet_id, 
                        max_results=5
                    )
                    
                    print(f"   💬 {len(replies)} réponses trouvées")
                    total_replies += len(replies)
                    
                    for j, reply in enumerate(replies):
                        print(f"      {j+1}. @{reply.author_id}: {reply.content[:30]}...")
                        
                        # Vérifier si déjà en base
                        exists = self.storage_manager.reply_exists(reply.reply_id)
                        print(f"         {'✅ Déjà en base' if exists else '🆕 Nouvelle'}")
                    
                except Exception as e:
                    print(f"   ❌ Erreur récupération réponses: {e}")
            
            print(f"\n📈 Total: {total_replies} réponses sur {len(our_tweets)} tweets")
            return True
            
        except Exception as e:
            print(f"❌ Erreur test réponses: {e}")
            return False
    
    def test_duplicate_handling_live(self):
        """Test de la gestion des duplicatas avec vraies données"""
        print("\n🔄 Test Gestion Duplicatas (Données Réelles)")
        print("=" * 50)
        
        try:
            # Récupérer un tweet récent
            recent_tweets = self.storage_manager.get_recent_tweets(hours=24)
            
            if not recent_tweets:
                print("❌ Aucun tweet récent pour tester")
                return False
            
            test_tweet = recent_tweets[0]
            print(f"📝 Test sur tweet: {test_tweet.tweet_id}")
            
            # Récupérer les réponses
            replies = self.twitter_manager.get_tweet_replies(
                test_tweet.tweet_id, 
                max_results=3
            )
            
            if not replies:
                print("❌ Aucune réponse trouvée")
                return False
            
            print(f"💬 {len(replies)} réponses trouvées")
            
            # Test de sauvegarde avec gestion des duplicatas
            for reply in replies:
                print(f"\n🔍 Test réponse: {reply.reply_id}")
                
                # Premier save
                result1 = self.storage_manager.save_reply(reply)
                print(f"   1er save: {'✅' if result1 else '❌'} {result1}")
                
                # Deuxième save (duplicate)
                result2 = self.storage_manager.save_reply(reply)
                print(f"   2ème save: {'✅' if result2 else '❌'} {result2}")
                
                # Vérification
                exists = self.storage_manager.reply_exists(reply.reply_id)
                print(f"   Existe: {'✅' if exists else '❌'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test duplicatas: {e}")
            return False
    
    def test_auto_like_simulation(self):
        """Test simulation d'auto-like (sans vraie action)"""
        print("\n❤️ Test Simulation Auto-Like")
        print("=" * 50)
        
        try:
            config = self.config_manager.get_config()
            
            print(f"⚙️ Auto-like activé: {config.engagement.auto_like_replies}")
            
            # Récupérer quelques réponses récentes
            recent_replies = self.storage_manager.get_recent_replies(hours=24)
            
            if not recent_replies:
                print("❌ Aucune réponse récente trouvée")
                return False
            
            print(f"💬 {len(recent_replies)} réponses récentes")
            
            like_candidates = 0
            
            for reply in recent_replies[:5]:  # Max 5
                print(f"\n🔍 Réponse: {reply.reply_id}")
                print(f"   Contenu: {reply.content[:40]}...")
                print(f"   Déjà liké: {'✅' if reply.liked else '❌'}")
                
                if not reply.liked and config.engagement.auto_like_replies:
                    print("   🎯 Candidat pour auto-like")
                    like_candidates += 1
                else:
                    print("   ⏭️ Ignoré")
            
            print(f"\n📊 {like_candidates} réponses candidates pour auto-like")
            print("💡 Utilisez le bot en mode normal pour les vraies actions")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test auto-like: {e}")
            return False
    
    def test_performance_metrics(self):
        """Test des métriques de performance"""
        print("\n⚡ Test Métriques Performance")
        print("=" * 50)
        
        try:
            import time
            
            # Test de récupération des tweets
            start_time = time.time()
            tweets = self.storage_manager.get_recent_tweets(hours=24)
            tweets_time = time.time() - start_time
            
            print(f"📝 Récupération tweets: {len(tweets)} en {tweets_time:.3f}s")
            
            # Test de récupération des réponses
            start_time = time.time()
            replies = self.storage_manager.get_recent_replies(hours=24)
            replies_time = time.time() - start_time
            
            print(f"💬 Récupération réponses: {len(replies)} en {replies_time:.3f}s")
            
            # Test de vérification d'existence en lot
            if replies:
                reply_ids = [r.reply_id for r in replies[:10]]
                
                start_time = time.time()
                existing_ids = self.storage_manager.get_existing_reply_ids(reply_ids)
                batch_time = time.time() - start_time
                
                print(f"🔍 Vérification lot: {len(reply_ids)} IDs en {batch_time:.3f}s")
                print(f"   {len(existing_ids)} existants trouvés")
            
            # Statistiques du cache
            cache_size = len(self.reply_handler._processed_replies)
            print(f"🧠 Cache mémoire: {cache_size} réponses")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur métriques: {e}")
            return False
    
    def test_quota_status(self):
        """Test du statut des quotas API"""
        print("\n📊 Test Statut Quotas API")
        print("=" * 50)
        
        try:
            quota_status = self.twitter_manager.get_quota_status()
            
            print("Quotas actuels:")
            print(f"   Plan API: {quota_status['plan']}")
            print(f"   Dernière réinitialisation: {quota_status['last_reset']}")
            
            print("\nUtilisation quotidienne:")
            for quota_type, usage in quota_status['daily_usage'].items():
                limit = quota_status['daily_limits'].get(quota_type, 'N/A')
                percentage = (usage / limit * 100) if isinstance(limit, int) and limit > 0 else 0
                print(f"   {quota_type}: {usage}/{limit} ({percentage:.1f}%)")
            
            # Vérifier si on peut faire d'autres requêtes
            remaining_reads = quota_status['daily_limits'].get('reads', 0) - quota_status['daily_usage'].get('reads', 0)
            
            if remaining_reads > 100:
                print("✅ Suffisamment de quota pour continuer les tests")
            else:
                print("⚠️ Quota faible, limitez les tests supplémentaires")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur quota: {e}")
            return False
    
    def run_safe_tests(self):
        """Exécuter tous les tests en mode sécurisé"""
        print("🧪 TESTS EN DIRECT DU SYSTÈME DE RÉPONSES")
        print("=" * 60)
        print("⚠️  Mode sécurisé: Utilisation minimale des API")
        print("=" * 60)
        
        tests = [
            ('Statut Quotas', self.test_quota_status),
            ('Réponses Récentes', lambda: self.test_recent_tweets_replies(hours=2)),
            ('Gestion Duplicatas', self.test_duplicate_handling_live),
            ('Simulation Auto-Like', self.test_auto_like_simulation),
            ('Métriques Performance', self.test_performance_metrics)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Démarrage: {test_name}")
                results[test_name] = test_func()
                
                if results[test_name]:
                    print(f"✅ {test_name}: RÉUSSI")
                else:
                    print(f"❌ {test_name}: ÉCHOUÉ")
                    
            except Exception as e:
                print(f"❌ Erreur dans {test_name}: {e}")
                results[test_name] = False
        
        # Résumé
        print("\n📊 RÉSUMÉ DES TESTS EN DIRECT")
        print("=" * 60)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 TOUS LES TESTS EN DIRECT RÉUSSIS !")
            print("✅ Le système de réponses fonctionne avec de vraies données")
        else:
            print("⚠️  Certains tests ont échoué")
            print("🔧 Vérifiez la connectivité et les quotas API")
        
        return passed == total


def main():
    """Point d'entrée principal"""
    
    print("⚠️  ATTENTION: Test avec vraies données Twitter")
    print("   Ce test utilise vos quotas API Twitter")
    
    response = input("\nContinuer? (o/N): ").lower().strip()
    
    if response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Test annulé par l'utilisateur")
        return 1
    
    tester = LiveReplyTester()
    success = tester.run_safe_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 