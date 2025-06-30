#!/usr/bin/env python3
"""
Gestionnaire de modèles LLM modulaire
Support: OpenAI, LM Studio, et configuration .env
Optimisé: LM_ALTERNATIVE_IPS utilisées seulement si localhost échoue
"""

import json
import os
import sys
from pathlib import Path
import subprocess

def load_prompts():
    """Charge le fichier prompts.json"""
    prompts_file = Path("../config/prompts.json") if Path("../config/prompts.json").exists() else Path("config/prompts.json")
    if not prompts_file.exists():
        print("❌ Fichier config/prompts.json non trouvé")
        return None
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_prompts(data):
    """Sauvegarde le fichier prompts.json"""
    prompts_file = Path("../config/prompts.json") if Path("../config/prompts.json").exists() else Path("config/prompts.json")
    with open(prompts_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_env():
    """Charge le fichier .env"""
    env_file = Path("../.env") if Path("../.env").exists() else Path(".env")
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def save_env(env_vars):
    """Sauvegarde le fichier .env"""
    env_file = Path("../.env") if Path("../.env").exists() else Path(".env")
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Configuration LLM Provider\n")
        f.write("# Choisir: auto, openai, lmstudio\n")
        f.write(f"LLM_PROVIDER={env_vars.get('LLM_PROVIDER', 'auto')}\n\n")
        
        f.write("# Configuration OpenAI\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', '')}\n\n")
        
        f.write("# Configuration LM Studio\n")
        f.write(f"LM_API_URL={env_vars.get('LM_API_URL', 'http://localhost:1234')}\n")
        if 'LM_ALTERNATIVE_IPS' in env_vars and env_vars['LM_ALTERNATIVE_IPS'].strip():
            f.write(f"LM_ALTERNATIVE_IPS={env_vars['LM_ALTERNATIVE_IPS']}\n")
        f.write("# LM_ALTERNATIVE_IPS=192.168.1.34,192.168.1.33  # Optionnel - fallback IPs\n")
        if 'LM_MODEL_NAME' in env_vars:
            f.write(f"LM_MODEL_NAME={env_vars['LM_MODEL_NAME']}\n")
        f.write("# LM_MODEL_NAME=nom-modele-specifique  # Optionnel - auto-détecté si non spécifié\n\n")
        
        # Autres variables existantes
        for key, value in env_vars.items():
            if not key.startswith(('LLM_', 'OPENAI_', 'LM_')):
                f.write(f"{key}={value}\n")

def show_current_config():
    """Affiche la configuration actuelle"""
    print("🔧 CONFIGURATION ACTUELLE:")
    print("=" * 50)
    
    # Prompts config
    data = load_prompts()
    if data:
        settings = data["settings"]["auto_reply"]
        print(f"📋 Prompts.json:")
        print(f"   🤖 Provider: {settings.get('provider', 'auto')}")
        print(f"   📱 Modèle: {settings['model']}")
        print(f"   🎛️ Température: {settings['temperature']}")
        print(f"   📏 Max tokens: {settings['max_tokens']}")
    
    # Env config
    env_vars = load_env()
    print(f"\n🌍 Variables d'environnement:")
    print(f"   🎯 LLM_PROVIDER: {env_vars.get('LLM_PROVIDER', 'auto')}")
    print(f"   🔑 OPENAI_API_KEY: {'✅ Configuré' if env_vars.get('OPENAI_API_KEY') else '❌ Manquant'}")
    print(f"   🏠 LM_API_URL: {env_vars.get('LM_API_URL', 'http://localhost:1234')}")
    
    alt_ips = env_vars.get('LM_ALTERNATIVE_IPS', '')
    if alt_ips and alt_ips.strip():
        print(f"   🔄 LM_ALTERNATIVE_IPS: {alt_ips} (fallback si localhost échoue)")
    else:
        print(f"   🔄 LM_ALTERNATIVE_IPS: ✅ Non nécessaire (localhost suffit)")
    
    lm_model = env_vars.get('LM_MODEL_NAME', 'Auto-détecté')
    print(f"   🤖 LM_MODEL_NAME: {lm_model} {'(intelligent)' if lm_model == 'Auto-détecté' else '(manuel)'}")

def configure_provider():
    """Configure le provider LLM"""
    print("\n🎯 CONFIGURATION PROVIDER")
    print("=" * 30)
    print("1. 🤖 Auto (LM Studio localhost → alternatives → OpenAI)")
    print("2. 🏠 LM Studio uniquement (localhost + fallback)")
    print("3. ☁️ OpenAI uniquement")
    
    try:
        choice = input("\n➤ Choisir le provider (1-3): ").strip()
        
        env_vars = load_env()
        
        if choice == "1":
            env_vars["LLM_PROVIDER"] = "auto"
            print("✅ Provider configuré: Auto (localhost → alternatives → OpenAI)")
        elif choice == "2":
            env_vars["LLM_PROVIDER"] = "lmstudio"
            configure_lm_studio(env_vars)
            print("✅ Provider configuré: LM Studio")
        elif choice == "3":
            env_vars["LLM_PROVIDER"] = "openai"
            configure_openai(env_vars)
            print("✅ Provider configuré: OpenAI")
        else:
            print("❌ Choix invalide")
            return
        
        save_env(env_vars)
        
    except KeyboardInterrupt:
        print("\n❌ Annulé")

def configure_openai(env_vars):
    """Configure OpenAI"""
    current_key = env_vars.get('OPENAI_API_KEY', '')
    display_key = f"{current_key[:8]}..." if current_key else "Non configuré"
    
    print(f"\n🔑 Configuration OpenAI")
    print(f"Clé actuelle: {display_key}")
    
    new_key = input("➤ Nouvelle clé API (Enter pour garder): ").strip()
    if new_key:
        env_vars['OPENAI_API_KEY'] = new_key

def configure_lm_studio(env_vars):
    """Configure LM Studio avec fallback intelligent"""
    print(f"\n🏠 Configuration LM Studio")
    
    current_url = env_vars.get('LM_API_URL', 'http://localhost:1234')
    print(f"URL principale: {current_url}")
    new_url = input("➤ Nouvelle URL principale (Enter pour garder localhost:1234): ").strip()
    if new_url:
        env_vars['LM_API_URL'] = new_url
    
    print(f"\n💡 IPs alternatives seulement si vous avez d'autres machines LM Studio")
    current_ips = env_vars.get('LM_ALTERNATIVE_IPS', '')
    if current_ips:
        print(f"IPs alternatives actuelles: {current_ips}")
    else:
        print(f"Aucune IP alternative (localhost suffit généralement)")
    
    configure_alt = input("➤ Ajouter des IPs alternatives ? (y/N): ").strip().lower()
    if configure_alt == 'y':
        new_ips = input("➤ IPs alternatives (séparées par virgules, ou Enter pour supprimer): ").strip()
        if new_ips:
            env_vars['LM_ALTERNATIVE_IPS'] = new_ips
        elif 'LM_ALTERNATIVE_IPS' in env_vars:
            del env_vars['LM_ALTERNATIVE_IPS']
    
    current_model = env_vars.get('LM_MODEL_NAME', 'Auto-détecté')
    print(f"Modèle actuel: {current_model}")
    print(f"💡 Laissez vide pour auto-détection (recommandé)")
    new_model = input("➤ Nouveau modèle spécifique (Enter pour auto-détection): ").strip()
    if new_model:
        env_vars['LM_MODEL_NAME'] = new_model
    elif 'LM_MODEL_NAME' in env_vars:
        # Supprimer la variable pour forcer l'auto-détection
        del env_vars['LM_MODEL_NAME']

def test_providers():
    """Test les providers disponibles"""
    print("\n🧪 TEST DES PROVIDERS")
    print("=" * 30)
    
    try:
        # Test du système modulaire
        parent_dir = Path(__file__).parent.parent
        sys.path.append(str(parent_dir / 'core'))
        from llm_providers import get_llm_manager
        
        manager = get_llm_manager()
        info = manager.get_active_provider_info()
        
        print(f"🎯 Provider actif: {info['provider']}")
        print(f"📡 Disponible: {'✅' if info['available'] else '❌'}")
        print(f"🤖 Modèles: {len(info['models'])} disponibles")
        
        if info['models']:
            print(f"   📋 Exemples: {', '.join(info['models'][:3])}...")
        
        if info['provider'] == 'lmstudio':
            print(f"🏠 URL active: {info.get('active_url', 'N/A')}")
            print(f"📦 Modèle configuré: {info.get('configured_model', 'N/A')}")
            
            # Indiquer si on utilise localhost ou alternative
            active_url = info.get('active_url', '')
            if 'localhost' in active_url or '127.0.0.1' in active_url:
                print(f"✅ Utilise localhost (optimal)")
            else:
                print(f"⚠️ Utilise IP alternative (localhost non disponible)")
        
        # Test de génération
        print(f"\n🔄 Test de génération...")
        response = manager.generate_reply(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say hello briefly",
            max_tokens=20,
            temperature=0.7
        )
        
        if response:
            print(f"✅ Test réussi: \"{response}\"")
        else:
            print(f"❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")

def restart_bot():
    """Redémarre le bot"""
    print("\n🔄 REDÉMARRAGE DU BOT")
    print("=" * 25)
    
    try:
        # Aller dans le répertoire parent
        os.chdir(Path(__file__).parent.parent)
        
        # Arrêter les processus existants
        print("⏹️ Arrêt des processus...")
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                      capture_output=True, shell=True)
        
        # Redémarrer
        print("🚀 Redémarrage...")
        subprocess.Popen(["python", "main.py"], shell=True)
        
        print("✅ Bot redémarré avec la nouvelle configuration")
        
    except Exception as e:
        print(f"❌ Erreur redémarrage: {e}")

def main():
    """Menu principal"""
    while True:
        print("\n" + "="*60)
        print("🤖 GESTIONNAIRE MODÈLES LLM MODULAIRE")
        print("="*60)
        
        show_current_config()
        
        print(f"\n📋 OPTIONS:")
        print(f"   1. 🎯 Configurer Provider (OpenAI/LM Studio)")
        print(f"   2. 🌡️ Ajuster température")
        print(f"   3. 🧪 Tester les providers")
        print(f"   4. 📊 Voir config complète")
        print(f"   5. 🔄 Redémarrer le bot")
        print(f"   6. 🚪 Quitter")
        
        try:
            choice = input(f"\n➤ Votre choix (1-6): ").strip()
            
            if choice == "1":
                configure_provider()
            elif choice == "2":
                change_temperature()
            elif choice == "3":
                test_providers()
            elif choice == "4":
                data = load_prompts()
                env_vars = load_env()
                print(f"\n🔧 CONFIG COMPLÈTE:")
                if data:
                    print(f"Prompts: {json.dumps(data['settings']['auto_reply'], indent=2)}")
                print(f"Env: {json.dumps({k:v for k,v in env_vars.items() if k.startswith(('LLM_', 'OPENAI_', 'LM_'))}, indent=2)}")
            elif choice == "5":
                restart_bot()
            elif choice == "6":
                print("👋 Au revoir!")
                break
            else:
                print("❌ Choix invalide")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break

def change_temperature():
    """Change la température du modèle"""
    try:
        data = load_prompts()
        if not data:
            return
            
        current_temp = data["settings"]["auto_reply"]["temperature"]
        
        temp = input(f"\n🌡️ Nouvelle température (0.1-1.0, actuelle {current_temp}): ").strip()
        
        temp_value = float(temp)
        if 0.1 <= temp_value <= 1.0:
            data["settings"]["auto_reply"]["temperature"] = temp_value
            save_prompts(data)
            
            print(f"✅ Température changée vers: {temp_value}")
            if temp_value < 0.3:
                print("🧊 Réponses plus conservatrices et prévisibles")
            elif temp_value > 0.8:
                print("🔥 Réponses plus créatives et variées")
            else:
                print("⚖️ Bon équilibre créativité/cohérence")
        else:
            print("❌ Valeur invalide (doit être entre 0.1 et 1.0)")
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Annulé")

if __name__ == "__main__":
    main() 