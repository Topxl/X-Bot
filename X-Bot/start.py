#!/usr/bin/env python3
"""
🚀 LANCEUR UNIFIÉ - Bot Twitter Automatisé
Point d'entrée unique pour tous les modes de lancement !

Modes disponibles:
- python start.py              → Bot + Dashboard (mode complet)
- python start.py --dashboard  → Dashboard seulement
- python start.py --bot        → Bot seulement
- python start.py --help       → Aide
"""

import os
import sys
import time
import argparse
import threading
import subprocess
from pathlib import Path

def print_banner():
    """Affiche la bannière de démarrage"""
    print("=" * 60)
    print("🤖 BOT TWITTER AUTOMATISÉ - LANCEUR UNIFIÉ")
    print("=" * 60)
    print("✨ Configuration simplifiée - Un seul fichier pour tout !")
    print("🌐 Dashboard: http://localhost:8080")
    print("🤖 Bot: Génération automatique + engagement")
    print("=" * 60)

def setup_environment():
    """Configure l'environnement Python"""
    # S'assurer qu'on est dans le bon répertoire
    os.chdir(Path(__file__).parent)
    
    # Ajouter core au Python path
    core_path = str(Path.cwd() / "core")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

def start_dashboard_only():
    """Lance uniquement le dashboard"""
    try:
        print("📊 DÉMARRAGE DASHBOARD SEULEMENT")
        print("🌐 Interface web: http://localhost:8080")
        print("-" * 40)
        
        setup_environment()
        
        from core.dashboard.start import start_dashboard
        start_dashboard(host="0.0.0.0", port=8080)
        
    except ImportError as e:
        print(f"❌ Dashboard non disponible: {e}")
        print("💡 Installation: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        sys.exit(1)

def start_bot_only():
    """Lance uniquement le bot"""
    try:
        print("🤖 DÉMARRAGE BOT SEULEMENT")
        print("📝 Logs dans logs/bot_*.log")
        print("-" * 40)
        
        setup_environment()
        
        from main import main as bot_main
        bot_main()
        
    except ImportError as e:
        print(f"❌ Bot non disponible: {e}")
        print("📋 Vérifiez que core/main.py existe")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur bot: {e}")
        sys.exit(1)

def start_dashboard_thread():
    """Lance le dashboard en arrière-plan"""
    try:
        setup_environment()
        from core.dashboard.start import start_dashboard
        start_dashboard(host="0.0.0.0", port=8080)
    except Exception as e:
        print(f"⚠️ Dashboard thread error: {e}")

def start_bot_and_dashboard():
    """Lance bot + dashboard ensemble (mode par défaut)"""
    try:
        print("🚀 DÉMARRAGE COMPLET - BOT + DASHBOARD")
        print("🌐 Dashboard: http://localhost:8080")
        print("🤖 Bot: Automatisation complète")
        print("-" * 40)
        
        setup_environment()
        
        # Démarrer le dashboard en arrière-plan
        print("📊 Initialisation du dashboard...")
        dashboard_thread = threading.Thread(
            target=start_dashboard_thread,
            daemon=True,
            name="DashboardThread"
        )
        dashboard_thread.start()
        
        # Attendre que le dashboard démarre
        print("⏳ Préparation des services (3 secondes)...")
        time.sleep(3)
        
        print("✅ Dashboard en cours de démarrage")
        print("🤖 Lancement du bot principal...")
        print("-" * 40)
        
        # Lancer le bot principal
        from main import main as bot_main
        bot_main()
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("📋 Vérifiez l'installation des dépendances")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        sys.exit(1)

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Bot Twitter Automatisé - Lanceur Unifié",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python start.py                    # Mode complet (bot + dashboard)
  python start.py --dashboard        # Dashboard seulement  
  python start.py --bot              # Bot seulement
  python start.py --help             # Cette aide

Configuration:
  - Dashboard: Interface web de configuration sur http://localhost:8080
  - Bot: Génération automatique de contenu et engagement Twitter
  - Logs: Disponibles dans le dossier logs/
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--dashboard', '-d',
        action='store_true',
        help='Lance uniquement le dashboard web'
    )
    group.add_argument(
        '--bot', '-b',
        action='store_true',
        help='Lance uniquement le bot Twitter'
    )
    
    return parser.parse_args()

def main():
    """Point d'entrée principal"""
    try:
        args = parse_arguments()
        
        print_banner()
        
        # Mode dashboard seulement
        if args.dashboard:
            start_dashboard_only()
            
        # Mode bot seulement  
        elif args.bot:
            start_bot_only()
            
        # Mode par défaut : bot + dashboard
        else:
            start_bot_and_dashboard()
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé (Ctrl+C)")
        print("👋 Services arrêtés proprement")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez les dépendances: pip install -r requirements.txt")
        print("   2. Vérifiez la configuration dans config/")
        print("   3. Consultez les logs dans logs/")
        
    finally:
        print("\nFin du programme")

if __name__ == "__main__":
    main() 