#!/usr/bin/env python3
"""
Test pour vérifier que tous les prompts sont maintenant en anglais
"""

import json

def test_english_prompts():
    print("🇺🇸 Test: Vérification Prompts en Anglais")
    print("=" * 50)
    
    with open('config/prompts.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    # Vérifier system prompts
    print("\n📄 System Prompts:")
    tweet_gen = prompts['system_prompts']['tweet_generation']['content']
    auto_reply = prompts['system_prompts']['auto_reply']['content']
    
    print(f"✅ Tweet Generation: {tweet_gen[:80]}...")
    print(f"✅ Auto Reply: {auto_reply[:80]}...")
    
    # Vérifier user prompts
    print("\n📝 User Prompts:")
    tweet_template = prompts['user_prompts']['tweet_generation']['template']
    reply_template = prompts['user_prompts']['auto_reply']['template']
    image_template = prompts['user_prompts']['image_prompt']['template']
    
    print(f"✅ Tweet Template: {tweet_template[:80]}...")
    print(f"✅ Reply Template: {reply_template[:80]}...")
    print(f"✅ Image Template: {image_template[:80]}...")
    
    # Vérifier les modèles
    print("\n⚙️ Settings:")
    tweet_model = prompts['settings']['tweet_generation']['model']
    reply_model = prompts['settings']['auto_reply']['model']
    
    print(f"✅ Tweet Model: {tweet_model}")
    print(f"✅ Reply Model: {reply_model}")
    
    # Vérifications de langue
    english_checks = [
        ("Tweet system starts with 'You are'", tweet_gen.startswith("You are")),
        ("Reply system starts with 'You are'", auto_reply.startswith("You are")),
        ("Tweet template contains 'Generate'", "Generate" in tweet_template),
        ("Reply template contains 'Reply to'", "Reply to" in reply_template),
        ("Image template contains 'Create'", "Create" in image_template),
        ("No French detected", "Génère" not in json.dumps(prompts) and "Tu es" not in json.dumps(prompts))
    ]
    
    print("\n🔍 Vérifications Langue:")
    all_passed = True
    for check_name, check_result in english_checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False
    
    print(f"\n🎯 Résultat: {'✅ TOUT EN ANGLAIS' if all_passed else '❌ DU FRANÇAIS DÉTECTÉ'}")
    return all_passed

if __name__ == "__main__":
    success = test_english_prompts()
    if success:
        print("\n🎉 Configuration entièrement en anglais !")
        print("💡 Redémarrez le bot pour appliquer les changements.")
    else:
        print("\n⚠️ Certains éléments sont encore en français.") 