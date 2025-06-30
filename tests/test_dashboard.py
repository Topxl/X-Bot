#!/usr/bin/env python3
"""
Test basique du Dashboard Web
"""

import sys
from pathlib import Path

# Ajouter le dossier core au PATH
current_dir = Path(__file__).parent.parent
core_dir = current_dir / "core"
sys.path.insert(0, str(core_dir))

def test_dashboard_imports():
    """Test des imports du dashboard"""
    print("🧪 Test Dashboard - Imports")
    print("=" * 40)
    
    try:
        # Test import FastAPI
        import fastapi
        print("✅ FastAPI disponible")
    except ImportError as e:
        print(f"❌ FastAPI manquant : {e}")
        return False
    
    try:
        # Test import uvicorn
        import uvicorn
        print("✅ Uvicorn disponible")
    except ImportError as e:
        print(f"❌ Uvicorn manquant : {e}")
        return False
    
    try:
        # Test import websockets
        import websockets
        print("✅ WebSockets disponible")
    except ImportError as e:
        print(f"❌ WebSockets manquant : {e}")
        return False
    
    try:
        # Test import du dashboard
        from dashboard import DashboardServer, start_dashboard
        print("✅ Module dashboard importé")
    except ImportError as e:
        print(f"❌ Erreur import dashboard : {e}")
        return False
    
    return True


def test_dashboard_creation():
    """Test de création d'instance du dashboard"""
    print("\n🧪 Test Dashboard - Création Instance")
    print("=" * 40)
    
    try:
        from dashboard import DashboardServer
        
        # Créer une instance (sans démarrer le serveur)
        dashboard = DashboardServer(host="127.0.0.1", port=8080)
        print("✅ Instance DashboardServer créée")
        
        # Vérifier les attributs de base
        assert dashboard.host == "127.0.0.1"
        assert dashboard.port == 8080
        assert hasattr(dashboard, 'app')
        print("✅ Attributs de base corrects")
        
        # Vérifier que l'app FastAPI est créée
        from fastapi import FastAPI
        assert isinstance(dashboard.app, FastAPI)
        print("✅ Instance FastAPI créée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création dashboard : {e}")
        return False


def test_dashboard_routes():
    """Test des routes du dashboard"""
    print("\n🧪 Test Dashboard - Routes")
    print("=" * 40)
    
    try:
        from dashboard import DashboardServer
        
        dashboard = DashboardServer()
        
        # Récupérer les routes
        routes = [route.path for route in dashboard.app.routes]
        
        expected_routes = ["/", "/health", "/api/metrics"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} trouvée")
            else:
                print(f"❌ Route {route} manquante")
                return False
        
        print("✅ Toutes les routes essentielles présentes")
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification routes : {e}")
        return False


def test_metrics_collection():
    """Test de collecte des métriques"""
    print("\n🧪 Test Dashboard - Collecte Métriques")
    print("=" * 40)
    
    try:
        from dashboard import DashboardServer
        import asyncio
        
        dashboard = DashboardServer()
        
        # Test de collecte des métriques
        async def test_collect():
            metrics = await dashboard.collect_metrics()
            
            # Vérifier les champs requis
            required_fields = [
                'status', 'uptime', 'tweets_today', 
                'likes_today', 'replies_today', 'quota_usage'
            ]
            
            for field in required_fields:
                if hasattr(metrics, field):
                    print(f"✅ Champ {field} présent")
                else:
                    print(f"❌ Champ {field} manquant")
                    return False
            
            print("✅ Structure des métriques correcte")
            return True
        
        # Exécuter le test async
        result = asyncio.run(test_collect())
        return result
        
    except Exception as e:
        print(f"❌ Erreur collecte métriques : {e}")
        return False


def main():
    """Exécuter tous les tests"""
    print("🎛️ Tests Dashboard Web Bot Twitter")
    print("=" * 60)
    
    tests = [
        test_dashboard_imports,
        test_dashboard_creation,
        test_dashboard_routes,
        test_metrics_collection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} échoué")
        except Exception as e:
            print(f"❌ Erreur dans {test.__name__} : {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats : {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests passent ! Dashboard prêt à utiliser")
        print("\n💡 Pour démarrer le dashboard :")
        print("   python start_dashboard.py")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 