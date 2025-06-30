#!/usr/bin/env python3
"""
Script de démarrage du Dashboard

Usage:
    python core/dashboard/start.py [--host HOST] [--port PORT] [--debug]
"""

import argparse
import sys
from pathlib import Path

# Ajouter les répertoires nécessaires au path Python
current_dir = Path(__file__).parent  # core/dashboard
core_dir = current_dir.parent        # core
root_dir = core_dir.parent           # racine

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(core_dir))

try:
    from core.dashboard import start_dashboard
    from core.dashboard.config import DashboardConfig
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Vérifiez que FastAPI et uvicorn sont installés:")
    print("   pip install fastapi uvicorn")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Démarre le dashboard Twitter Bot")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Adresse d'écoute (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080, 
        help="Port d'écoute (default: 8080)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Mode debug"
    )
    
    args = parser.parse_args()
    
    print("🤖 Dashboard Twitter Bot v2.0")
    print("=" * 40)
    print(f"🌐 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🐛 Debug: {args.debug}")
    print("=" * 40)
    
    try:
        # Configuration
        config = DashboardConfig(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        # Démarrage
        start_dashboard(host=args.host, port=args.port)
        
    except KeyboardInterrupt:
        print("\n👋 Arrêt du dashboard")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 