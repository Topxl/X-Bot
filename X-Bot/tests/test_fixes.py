#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections d'erreurs
"""

from datetime import datetime
from loguru import logger

from twitter_api import get_twitter_manager
from storage import get_storage_manager
from reply_handler import get_reply_handler


def test_twitter_api_fixes():
    """Test des corrections Twitter API"""
    
    print("🔧 Test Twitter API Fixes")
    print("=========================")
    
    try:
        twitter_manager = get_twitter_manager()
        
        # Test search viral tweets (sans min_faves)
        print("1. Testing search_viral_tweets...")
        viral_tweets = twitter_manager.search_viral_tweets(
            keywords=['crypto', 'bitcoin'], 
            max_results=5
        )
        print(f"   ✅ Found {len(viral_tweets)} viral tweets")
        
        # Test get_tweet_replies avec format flexible
        print("2. Testing get_tweet_replies...")
        # Utiliser un tweet ID existant de nos logs
        replies = twitter_manager.get_tweet_replies(
            "1938877951854141582",  # From logs
            max_results=5
        )
        print(f"   ✅ Found {len(replies)} replies")
        
        return True
        
    except Exception as e:
        print(f"❌ Twitter API error: {e}")
        return False


def test_storage_fixes():
    """Test des corrections Storage"""
    
    print("\n🗄️ Test Storage Fixes")
    print("=====================")
    
    try:
        storage_manager = get_storage_manager()
        
        # Test upload_image method exists
        print("1. Testing upload_image method...")
        if hasattr(storage_manager, 'upload_image'):
            print("   ✅ upload_image method exists")
        else:
            print("   ❌ upload_image method missing")
            return False
        
        # Test get_recent_tweets
        print("2. Testing get_recent_tweets...")
        tweets = storage_manager.get_recent_tweets(hours=24)
        print(f"   ✅ Found {len(tweets)} recent tweets")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return False


def test_reply_handler_startup():
    """Test du système de startup check"""
    
    print("\n🚀 Test Reply Handler Startup")
    print("=============================")
    
    try:
        reply_handler = get_reply_handler()
        
        # Test stats
        print("1. Testing handler stats...")
        stats = reply_handler.get_reply_stats()
        print(f"   ✅ Stats: {stats}")
        
        # Test force startup check
        print("2. Testing force startup check...")
        result = reply_handler.force_startup_check()
        print(f"   ✅ Startup check: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Reply handler error: {e}")
        return False


def test_quota_status():
    """Test du statut des quotas"""
    
    print("\n📊 Test Quota Status")
    print("====================")
    
    try:
        twitter_manager = get_twitter_manager()
        
        quota_status = twitter_manager.get_quota_status()
        print("Quota Status:")
        print(f"   • Daily usage: {quota_status['daily_usage']}")
        print(f"   • Daily limits: {quota_status['daily_limits']}")
        print(f"   • API Plan: {quota_status['plan']}")
        print(f"   • Last reset: {quota_status['last_reset']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quota status error: {e}")
        return False


def main():
    """Test complet"""
    
    print("🛠️ TEST COMPLETE DES CORRECTIONS")
    print("================================")
    
    results = {}
    
    # Test chaque composant
    results['twitter_api'] = test_twitter_api_fixes()
    results['storage'] = test_storage_fixes()
    results['reply_handler'] = test_reply_handler_startup()
    results['quota'] = test_quota_status()
    
    # Résumé
    print("\n📋 RÉSUMÉ DES TESTS")
    print("==================")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component.upper()}: {status}")
    
    print(f"\nRésultat: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Toutes les corrections fonctionnent !")
    else:
        print("⚠️ Certaines corrections nécessitent encore des ajustements")


if __name__ == "__main__":
    main() 