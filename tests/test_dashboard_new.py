#!/usr/bin/env python3
"""
Tests pour le nouveau Dashboard refactorisé
"""

import sys
import pytest
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_dashboard_imports():
    """Test des imports du nouveau dashboard"""
    try:
        from dashboard import DashboardServer, DashboardConfig
        from dashboard.config import DEFAULT_CONFIG, DARK_THEME
        from dashboard.server import DashboardServer
        from dashboard.routes import BotMetrics
        from dashboard.templates import get_dashboard_html
        
        print("✅ Tous les imports du dashboard fonctionnent")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_dashboard_config():
    """Test de la configuration du dashboard"""
    try:
        from dashboard.config import DashboardConfig, DEFAULT_CONFIG
        
        # Test config par défaut
        assert DEFAULT_CONFIG.host == "0.0.0.0"
        assert DEFAULT_CONFIG.port == 8080
        assert DEFAULT_CONFIG.title == "Twitter Bot Dashboard"
        
        # Test config personnalisée
        custom_config = DashboardConfig(
            host="127.0.0.1",
            port=9000,
            title="Test Dashboard"
        )
        
        config_dict = custom_config.to_dict()
        assert config_dict["host"] == "127.0.0.1"
        assert config_dict["port"] == 9000
        assert config_dict["title"] == "Test Dashboard"
        
        print("✅ Configuration du dashboard OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur config: {e}")
        return False


def test_dashboard_server_creation():
    """Test de création du serveur dashboard"""
    try:
        from dashboard.server import DashboardServer
        
        # Créer un serveur de test
        server = DashboardServer(host="127.0.0.1", port=8888)
        
        # Vérifier les propriétés
        assert server.config.host == "127.0.0.1"
        assert server.config.port == 8888
        assert server.app is not None
        
        # Vérifier le status
        status = server.get_status()
        assert "status" in status
        assert "uptime" in status
        assert "managers" in status
        
        print("✅ Création serveur dashboard OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")
        return False


def test_dashboard_templates():
    """Test de génération des templates HTML"""
    try:
        from dashboard.config import DashboardConfig
        from dashboard.templates import get_dashboard_html
        
        config = DashboardConfig(title="Test Dashboard")
        html = get_dashboard_html(config)
        
        # Vérifier que le HTML contient les éléments essentiels
        assert "<!DOCTYPE html>" in html
        assert "Test Dashboard" in html
        assert "Vue d'ensemble" in html
        assert "Configuration" in html
        assert "refreshData" in html  # JavaScript
        
        print("✅ Génération templates OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur templates: {e}")
        return False


def test_dashboard_metrics():
    """Test de la structure des métriques"""
    try:
        from dashboard.routes import BotMetrics
        
        # Créer des métriques de test
        metrics = BotMetrics(
            status="running",
            uptime="1:23:45",
            tweets_today=5,
            likes_today=12,
            replies_today=3,
            quota_usage={"posts": "5/50"},
            errors_count=0
        )
        
        assert metrics.status == "running"
        assert metrics.tweets_today == 5
        assert isinstance(metrics.quota_usage, dict)
        
        print("✅ Structure métriques OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur métriques: {e}")
        return False


def test_dashboard_start_script():
    """Test du script de démarrage"""
    try:
        # Vérifier que le script existe et est exécutable
        start_script = project_root / "dashboard" / "start.py"
        assert start_script.exists()
        
        # Vérifier les imports du script
        import dashboard.start
        
        print("✅ Script de démarrage OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur script start: {e}")
        return False


def test_dependencies_available():
    """Test de disponibilité des dépendances"""
    dependencies = []
    
    try:
        import fastapi
        dependencies.append("FastAPI ✅")
    except ImportError:
        dependencies.append("FastAPI ❌")
    
    try:
        import uvicorn
        dependencies.append("Uvicorn ✅")
    except ImportError:
        dependencies.append("Uvicorn ❌")
    
    try:
        import loguru
        dependencies.append("Loguru ✅")
    except ImportError:
        dependencies.append("Loguru ❌")
    
    print("📦 Dépendances:")
    for dep in dependencies:
        print(f"   {dep}")
    
    # Au minimum FastAPI et Uvicorn sont requis
    has_fastapi = "FastAPI ✅" in dependencies
    has_uvicorn = "Uvicorn ✅" in dependencies
    
    return has_fastapi and has_uvicorn


def run_all_tests():
    """Exécute tous les tests"""
    print("🧪 Tests du Dashboard v2.0 Refactorisé")
    print("=" * 50)
    
    tests = [
        ("Imports", test_dashboard_imports),
        ("Configuration", test_dashboard_config),
        ("Serveur", test_dashboard_server_creation),
        ("Templates", test_dashboard_templates),
        ("Métriques", test_dashboard_metrics),
        ("Script Start", test_dashboard_start_script),
        ("Dépendances", test_dependencies_available),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Exception dans {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Résultats:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests passent ! Dashboard prêt à utiliser.")
        print("🚀 Démarrage: python dashboard/start.py")
    else:
        print("⚠️  Certains tests échouent. Vérifiez les dépendances.")
        print("💡 Installation: pip install fastapi uvicorn loguru")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 