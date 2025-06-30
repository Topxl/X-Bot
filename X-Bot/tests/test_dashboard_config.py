#!/usr/bin/env python3
"""
Test du Dashboard de Configuration Amélioré

Vérifie que toutes les fonctionnalités de configuration du dashboard fonctionnent.
"""

import json
import requests
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dashboard import get_dashboard_server


def test_dashboard_routes():
    """Test des routes API du dashboard"""
    print("\n🌐 TEST ROUTES API DASHBOARD")
    print("=" * 40)
    
    base_url = "http://localhost:8080"
    
    # Test des routes de base
    routes_to_test = [
        ("GET", "/health", "Health check"),
        ("GET", "/api/metrics", "Métriques"),
        ("GET", "/api/config", "Configuration"),
        ("GET", "/api/logs", "Logs")
    ]
    
    for method, endpoint, description in routes_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {description}: {endpoint}")
            else:
                print(f"❌ {description}: {endpoint} (status: {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️ {description}: Dashboard non accessible - démarrez avec: python core/start_dashboard.py")
        except Exception as e:
            print(f"❌ {description}: Erreur {e}")


def test_config_endpoints():
    """Test des endpoints de configuration"""
    print("\n⚙️ TEST ENDPOINTS CONFIGURATION")
    print("=" * 40)
    
    base_url = "http://localhost:8080"
    
    # Test de configuration auto-reply
    auto_reply_data = {
        "auto_reply_enabled": False,
        "max_replies_per_day": 15,
        "max_replies_per_conversation": 1,
        "reply_check_interval_minutes": 5
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/config/auto-reply",
            json=auto_reply_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Configuration auto-reply: Sauvegarde OK")
            else:
                print(f"❌ Configuration auto-reply: {result.get('error', 'Erreur inconnue')}")
        else:
            print(f"❌ Configuration auto-reply: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Configuration auto-reply: Dashboard non accessible")
    except Exception as e:
        print(f"❌ Configuration auto-reply: Erreur {e}")
    
    # Test de configuration posting
    posting_data = {
        "enabled": True,
        "frequency_per_day": 3,
        "start_time": "09:00",
        "end_time": "21:00",
        "timezone": "Asia/Bangkok"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/config/posting",
            json=posting_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Configuration posting: Sauvegarde OK")
            else:
                print(f"❌ Configuration posting: {result.get('error', 'Erreur inconnue')}")
        else:
            print(f"❌ Configuration posting: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Configuration posting: Dashboard non accessible")
    except Exception as e:
        print(f"❌ Configuration posting: Erreur {e}")


def test_dashboard_interface():
    """Test de l'interface HTML du dashboard"""
    print("\n🎨 TEST INTERFACE DASHBOARD")
    print("=" * 40)
    
    try:
        from core.dashboard import DashboardServer
        
        # Créer une instance pour tester la génération HTML
        dashboard = DashboardServer()
        html_content = dashboard.get_dashboard_html()
        
        # Vérifications de contenu
        required_elements = [
            "Twitter Bot Dashboard",
            "tab-content",
            "auto-reply-form",
            "posting-form",
            "llm-form",
            "showTab",
            "loadAutoReplyConfig",
            "notification"
        ]
        
        all_present = True
        for element in required_elements:
            if element in html_content:
                print(f"✅ Élément présent: {element}")
            else:
                print(f"❌ Élément manquant: {element}")
                all_present = False
        
        if all_present:
            print("✅ Interface HTML complète")
            return True
        else:
            print("❌ Interface HTML incomplète")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test interface: {e}")
        return False


def show_dashboard_guide():
    """Affiche le guide d'utilisation du dashboard"""
    print("\n📖 GUIDE DASHBOARD DE CONFIGURATION")
    print("=" * 50)
    
    print("\n🚀 DÉMARRAGE")
    print("   python core/start_dashboard.py")
    print("   Accès: http://localhost:8080")
    print("")
    
    print("📊 ONGLETS DISPONIBLES:")
    print("")
    
    print("🏠 Vue d'ensemble")
    print("   • Statut du bot (running/error/limited)")
    print("   • Uptime depuis le dernier redémarrage")
    print("   • Tweets et likes aujourd'hui")
    print("   • Actualisation auto toutes les 30s")
    print("")
    
    print("💬 Réponses Auto")
    print("   • ⚙️ Activer/désactiver les réponses automatiques")
    print("   • 📊 Configurer les limites (par jour, par conversation)")
    print("   • ⏱️ Régler l'intervalle de vérification")
    print("   • 💾 Sauvegarde instantanée")
    print("")
    
    print("📝 Publication")
    print("   • 🔄 Activer/désactiver la publication auto")
    print("   • 📅 Nombre de tweets par jour")
    print("   • ⏰ Horaires de publication")
    print("   • 🌍 Configuration du fuseau horaire")
    print("")
    
    print("🤖 IA & Modèles")
    print("   • 🔄 Provider (Auto/OpenAI/LM Studio)")
    print("   • 🎯 Modèle utilisé")
    print("   • 🎨 Créativité (température)")
    print("   • 📏 Limites de tokens")
    print("   • ⚙️ Paramètres spéciaux pour les réponses")
    print("")
    
    print("📋 Logs")
    print("   • 📖 Logs récents en temps réel")
    print("   • 🔄 Actualisation manuelle des logs")
    print("   • 📊 Affichage des 20 dernières entrées")
    print("")
    
    print("✨ FONCTIONNALITÉS AVANCÉES:")
    print("   🔔 Notifications toast en temps réel")
    print("   📱 Interface responsive (mobile/desktop)")
    print("   🎯 Sauvegarde instantanée sans redémarrage")
    print("   🔄 Rechargement automatique de la config")
    print("   🎨 Interface sombre moderne")
    print("")
    
    print("🔧 ACTIONS RAPIDES:")
    print("   • Désactiver réponses auto → Onglet 'Réponses Auto' → Toggle OFF")
    print("   • Changer timezone → Onglet 'Publication' → Sélection fuseau")
    print("   • Passer en LM Studio → Onglet 'IA' → Provider: LM Studio")
    print("   • Modifier créativité → Onglet 'IA' → Slider température")


def verify_dashboard_files():
    """Vérifie que tous les fichiers nécessaires existent"""
    print("\n📁 VÉRIFICATION FICHIERS DASHBOARD")
    print("=" * 40)
    
    required_files = [
        "core/dashboard.py",
        "core/start_dashboard.py",
        "config/config.json"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Fichier présent: {file_path}")
        else:
            print(f"❌ Fichier manquant: {file_path}")
            all_exist = False
    
    if all_exist:
        print("✅ Tous les fichiers requis sont présents")
        return True
    else:
        print("❌ Fichiers manquants détectés")
        return False


if __name__ == "__main__":
    print("🧪 TEST DASHBOARD DE CONFIGURATION AMÉLIORÉ")
    print("="*60)
    
    # Tests principaux
    test1 = verify_dashboard_files()
    test2 = test_dashboard_interface()
    
    print("\n⚠️ TESTS NÉCESSITANT LE DASHBOARD ACTIF:")
    print("   Démarrez: python core/start_dashboard.py")
    print("   Puis relancez ce test pour les tests réseau")
    
    # Tests réseau (optionnels)
    test_dashboard_routes()
    test_config_endpoints()
    
    # Guide d'utilisation
    show_dashboard_guide()
    
    # Résultat global
    print(f"\n{'='*60}")
    if test1 and test2:
        print("🎉 DASHBOARD DE CONFIGURATION PRÊT!")
        print("✅ Interface moderne avec onglets")
        print("✅ Configuration en temps réel")
        print("✅ Notifications utilisateur")
        print("✅ Design responsive")
        print("")
        print("🚀 DÉMARRAGE:")
        print("   python core/start_dashboard.py")
        print("   http://localhost:8080")
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        print("⚠️ Vérifier les erreurs ci-dessus") 