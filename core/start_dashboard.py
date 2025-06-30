#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démarrage du Dashboard
REDIRECTION AUTOMATIQUE vers core/dashboard
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PATH pour trouver le module dashboard
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Redirection automatique vers le dashboard dans core"""
    
    print("🔄 Redirection vers le dashboard intégré dans core...")
    
    try:
        # Import depuis core.dashboard
        from core.dashboard import start_dashboard
        
        print("✅ Dashboard trouvé dans core/dashboard")
        print("🌐 Accès: http://localhost:8080")
        print("=" * 50)
        
        # Démarrage immédiat avec configuration par défaut
        start_dashboard(host="0.0.0.0", port=8080)
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Solutions:")
        print("   1. pip install fastapi uvicorn")
        print("   2. python core/dashboard/start.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 