#!/usr/bin/env python3
"""
Utilitaire pour changer facilement le modèle GPT des réponses
"""

import json
import sys
from pathlib import Path

def load_prompts():
    """Charge le fichier prompts.json"""
    prompts_file = Path("config/prompts.json")
    if not prompts_file.exists():
        print("❌ Fichier config/prompts.json non trouvé")
        return None
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_prompts(data):
    """Sauvegarde le fichier prompts.json"""
    with open("config/prompts.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def show_current_config():
    """Affiche la configuration actuelle"""
    data = load_prompts()
    if not data:
        return
    
    settings = data["settings"]["auto_reply"]
    print(f"🔧 CONFIGURATION ACTUELLE:")
    print(f"   📱 Modèle principal: {settings['model']}")
    print(f"   🔄 Modèles alternatifs: {', '.join(settings.get('alternative_models', []))}")
    print(f"   🎛️ Température: {settings['temperature']}")
    print(f"   📏 Max tokens: {settings['max_tokens']}")

def change_model():
    """Change le modèle GPT"""
    available_models = [
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4",
        "gpt-3.5-turbo"
    ]
    
    print("\n🤖 MODÈLES DISPONIBLES:")
    for i, model in enumerate(available_models, 1):
        print(f"   {i}. {model}")
    
    try:
        choice = input("\n🔄 Choisir le modèle principal (1-4): ").strip()
        model_index = int(choice) - 1
        
        if 0 <= model_index < len(available_models):
            new_model = available_models[model_index]
            
            # Charger et modifier la config
            data = load_prompts()
            if not data:
                return
            
            data["settings"]["auto_reply"]["model"] = new_model
            
            # Réorganiser les alternatives
            alternatives = [m for m in available_models if m != new_model]
            data["settings"]["auto_reply"]["alternative_models"] = alternatives
            
            # Sauvegarder
            save_prompts(data)
            
            print(f"\n✅ Modèle changé vers: {new_model}")
            print(f"📋 Alternatives: {', '.join(alternatives)}")
            print("\n⚠️ Redémarre le bot pour appliquer les changements")
            
        else:
            print("❌ Choix invalide")
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Annulé")

def change_temperature():
    """Change la température du modèle"""
    try:
        temp = input("\n🌡️ Nouvelle température (0.1-1.0, actuellement {}): ".format(
            load_prompts()["settings"]["auto_reply"]["temperature"]
        )).strip()
        
        temp_value = float(temp)
        if 0.1 <= temp_value <= 1.0:
            data = load_prompts()
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

def toggle_english():
    """Active/désactive les réponses en anglais"""
    data = load_prompts()
    current_content = data["system_prompts"]["auto_reply"]["content"]
    
    if "Always respond in English" in current_content:
        # Déjà en anglais
        answer = input("\n🌍 Passer aux réponses en français ? (y/N): ").strip().lower()
        if answer == 'y':
            # Changer vers français
            new_content = current_content.replace(
                "You are a crypto Twitter bot expert who responds to comments on your posts", 
                "Tu es un bot Twitter expert en crypto qui répond aux commentaires sur tes posts"
            ).replace(
                "Your replies are short (max 100 characters), friendly and engaging. Use relevant emojis and encourage discussion. Always stay positive and professional. IMPORTANT: Vary your responses - avoid repetitions, use questions, references to current events, different emojis. Each response must be unique and contextual. Always respond in English.",
                "Tes réponses sont courtes (max 100 caractères), amicales et engageantes. Tu utilises des emojis pertinents et encourages la discussion. Reste toujours positif et professionnel. IMPORTANT: Varie tes réponses - évite les répétitions, utilise des questions, des références à l'actualité, des emojis différents. Chaque réponse doit être unique et contextuelle."
            )
            
            data["system_prompts"]["auto_reply"]["content"] = new_content
            data["user_prompts"]["auto_reply"]["template"] = data["user_prompts"]["auto_reply"]["template"].replace(
                "Reply to this comment on my crypto tweet:", "Réponds à ce commentaire sur mon tweet crypto:"
            ).replace(
                "Be friendly, engaging and encourage discussion. Vary your responses - use questions, different emojis, references to crypto news. Max 100 characters, avoid repetitions. Always respond in English.",
                "Sois amical, engageant et encourage la discussion. Varie tes réponses - utilise des questions, des emojis différents, des références à l'actualité crypto. Max 100 caractères, évite les répétitions."
            )
            
            save_prompts(data)
            print("✅ Réponses configurées en français")
    else:
        # Déjà en français  
        answer = input("\n🌍 Passer aux réponses en anglais ? (y/N): ").strip().lower()
        if answer == 'y':
            # Déjà configuré en anglais par défaut
            print("✅ Réponses déjà configurées en anglais")

def main():
    """Menu principal"""
    while True:
        print("\n" + "="*50)
        print("🤖 CONFIGURATION MODÈLE GPT RÉPONSES")
        print("="*50)
        
        show_current_config()
        
        print(f"\n📋 OPTIONS:")
        print(f"   1. 🔄 Changer le modèle GPT")
        print(f"   2. 🌡️ Ajuster la température")
        print(f"   3. 🌍 Basculer langue (EN/FR)")
        print(f"   4. 📊 Voir la config complète")
        print(f"   5. 🚪 Quitter")
        
        try:
            choice = input(f"\n➤ Votre choix (1-5): ").strip()
            
            if choice == "1":
                change_model()
            elif choice == "2":
                change_temperature()
            elif choice == "3":
                toggle_english()
            elif choice == "4":
                data = load_prompts()
                print(f"\n🔧 CONFIG COMPLÈTE auto_reply:")
                print(json.dumps(data["settings"]["auto_reply"], indent=2))
            elif choice == "5":
                print("👋 Au revoir!")
                break
            else:
                print("❌ Choix invalide")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break

if __name__ == "__main__":
    main() 