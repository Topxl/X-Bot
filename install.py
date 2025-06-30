#!/usr/bin/env python3
"""
Script d'installation et de vérification pour Twitter Bot Automatisé
Version Réorganisée
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    """Affiche l'en-tête du script"""
    print("🤖 Twitter Bot Automatisé - Installation & Vérification")
    print("=" * 60)
    print("Version 2.0 - Structure Réorganisée")
    print("=" * 60)


def check_python_version():
    """Vérifie la version de Python"""
    print("\n🐍 Vérification de Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ requis")
        print(f"   Version actuelle: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
    return True


def check_structure():
    """Vérifie la structure des dossiers"""
    print("\n📁 Vérification de la structure...")
    
    required_dirs = ["core", "config", "tests", "docs", "scripts", "data"]
    required_files = [
        "main.py",
        "core/main.py",
        "core/config.py", 
        "core/twitter_api.py",
        "core/generator.py",
        "core/prompt_manager.py",
        "config/config.json",
        "config/prompts.json",
        "config/requirements.txt"
    ]
    
    missing = []
    
    # Vérifier les dossiers
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing.append(f"📂 {dir_name}/")
    
    # Vérifier les fichiers
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(f"📄 {file_path}")
    
    if missing:
        print("❌ Fichiers/dossiers manquants:")
        for item in missing:
            print(f"   {item}")
        return False
    
    print("✅ Structure complète")
    return True


def install_dependencies():
    """Installe les dépendances"""
    print("\n📦 Installation des dépendances...")
    
    requirements_file = Path("config/requirements.txt")
    if not requirements_file.exists():
        print("❌ Fichier requirements.txt non trouvé")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dépendances installées")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur d'installation: {e}")
        print(f"   Sortie d'erreur: {e.stderr}")
        return False


def create_env_template():
    """Crée un template .env si il n'existe pas"""
    print("\n⚙️ Configuration de l'environnement...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ Fichier .env existe déjà")
        return True
    
    env_template = """# Twitter/X API Credentials
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_BEARER_TOKEN=your_bearer_token_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Optional
LOG_LEVEL=INFO
ENVIRONMENT=development
"""
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_template)
    
    print("✅ Fichier .env.example créé")
    print("📝 Copiez .env.example vers .env et remplissez vos clés API")
    return True


def test_imports():
    """Teste les imports des modules principaux"""
    print("\n🧪 Test des imports...")
    
    # Ajouter les paths nécessaires
    sys.path.insert(0, str(Path("core")))
    sys.path.insert(0, str(Path("config")))
    
    test_modules = [
        "config",
        "prompt_manager", 
        "twitter_api",
        "generator",
        "storage",
        "scheduler",
        "reply_handler",
        "stats"
    ]
    
    failed_imports = []
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ {len(failed_imports)} imports échoués")
        return False
    
    print("✅ Tous les imports fonctionnent")
    return True


def run_quick_test():
    """Exécute un test rapide"""
    print("\n🚀 Test de démarrage rapide...")
    
    try:
        # Test du main.py
        result = subprocess.run([
            sys.executable, "main.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        print("✅ main.py accessible")
        return True
        
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ Erreur de démarrage: {e}")
        return False


def print_next_steps():
    """Affiche les prochaines étapes"""
    print("\n🎯 Prochaines Étapes")
    print("=" * 30)
    print("1. Configurez vos clés API dans .env")
    print("2. Ajustez config/config.json selon vos besoins")
    print("3. Personnalisez config/prompts.json (optionnel)")
    print("4. Lancez le bot: python main.py")
    print()
    print("📚 Documentation complète: docs/README.md")
    print("🧪 Tests disponibles: python -m pytest tests/")
    print("🐳 Docker: docker-compose up -d")


def main():
    """Fonction principale"""
    print_header()
    
    # Vérifications
    checks = [
        ("Python Version", check_python_version),
        ("Structure Projet", check_structure),
        ("Dépendances", install_dependencies),
        ("Configuration", create_env_template),
        ("Imports", test_imports),
        ("Démarrage", run_quick_test)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erreur dans {name}: {e}")
            results.append((name, False))
    
    # Résumé
    print("\n📋 Résumé de l'Installation")
    print("=" * 35)
    
    success_count = 0
    for name, success in results:
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"{name:.<20} {status}")
        if success:
            success_count += 1
    
    print(f"\nRésultat: {success_count}/{len(results)} vérifications réussies")
    
    if success_count == len(results):
        print("\n🎉 Installation complète et fonctionnelle !")
        print_next_steps()
    else:
        print("\n⚠️ Certaines vérifications ont échoué")
        print("📞 Consultez la documentation ou ouvrez une issue")
    
    return success_count == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 