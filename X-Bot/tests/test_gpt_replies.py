#!/usr/bin/env python3
"""
Test des réponses GPT contextuelles
Vérifie la qualité et la variété des réponses générées
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent/core au path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir / 'core'))

from llm_providers import get_llm_manager
from storage import Reply
from datetime import datetime

def test_contextual_responses():
    """Test la génération de réponses contextuelles"""
    print("🧪 TEST RÉPONSES GPT CONTEXTUELLES")
    print("=" * 50)
    
    try:
        # Initialiser le manager LLM
        manager = get_llm_manager()
        
        # Cas de test avec différents types de tweets
        test_cases = [
            {
                "category": "Message Bullish",
                "content": "Bitcoin is going to the moon! 🚀",
                "expected_keywords": ["moon", "bitcoin", "btc", "🚀", "🌕", "bull"]
            },
            {
                "category": "Question Technique", 
                "content": "What's your opinion on DeFi protocols?",
                "expected_keywords": ["defi", "protocol", "opinion", "think", "experience"]
            },
            {
                "category": "Analyse Marché",
                "content": "Market is looking bearish today 📉",
                "expected_keywords": ["bear", "market", "dip", "📉", "buy", "hodl"]
            },
            {
                "category": "Remerciement",
                "content": "Thanks for the great analysis! 💯",
                "expected_keywords": ["thanks", "analysis", "helpful", "💯", "glad"]
            }
        ]
        
        print(f"🎯 Test de {len(test_cases)} types de messages:")
        print("-" * 45)
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['category']}")
            print(f"💬 Input: \"{test_case['content']}\"")
            
            # Générer la réponse
            system_prompt = """You are MaxiMeme, a crypto expert bot on Twitter.
            Respond in French, keep it under 60 characters, be contextual and engaging.
            Use relevant emojis and ask follow-up questions."""
            
            user_prompt = f"Respond to this tweet: {test_case['content']}"
            
            try:
                response = manager.generate_reply(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=60,
                    temperature=0.9
                )
                
                if response:
                    print(f"✅ Output: \"{response}\"")
                    print(f"📏 Longueur: {len(response)} caractères")
                    
                    # Analyser la contextualité
                    response_lower = response.lower()
                    content_lower = test_case['content'].lower()
                    
                    # Vérifier si c'est contextuel (contient des mots-clés pertinents)
                    contextual_score = 0
                    matched_keywords = []
                    
                    for keyword in test_case['expected_keywords']:
                        if keyword.lower() in response_lower:
                            contextual_score += 1
                            matched_keywords.append(keyword)
                    
                    # Vérifier que ce n'est pas une réponse générique
                    generic_phrases = [
                        "thanks for engaging", "great point", "keep it up",
                        "exactly", "totally agree", "nice share"
                    ]
                    
                    is_generic = any(phrase in response_lower for phrase in generic_phrases)
                    
                    print(f"🎯 Mots-clés pertinents: {matched_keywords}")
                    print(f"📊 Score contextuel: {contextual_score}/{len(test_case['expected_keywords'])}")
                    print(f"🎭 Générique: {'❌ Oui' if is_generic else '✅ Non'}")
                    
                    # Évaluation globale
                    is_good = (
                        contextual_score > 0 and 
                        not is_generic and 
                        len(response) <= 200  # Longueur Twitter appropriée
                    )
                    
                    print(f"🏆 Qualité: {'✅ Excellente' if is_good else '⚠️ À améliorer'}")
                    
                    results.append({
                        'category': test_case['category'],
                        'response': response,
                        'contextual_score': contextual_score,
                        'is_generic': is_generic,
                        'is_good': is_good
                    })
                    
                else:
                    print("❌ Aucune réponse générée")
                    results.append({
                        'category': test_case['category'],
                        'response': None,
                        'is_good': False
                    })
                    
            except Exception as e:
                print(f"❌ Erreur génération: {e}")
                results.append({
                    'category': test_case['category'],
                    'response': None,
                    'is_good': False
                })
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur test contextuel: {e}")
        return []

def test_response_variety():
    """Test la variété des réponses (pas de répétition)"""
    print(f"\n🎭 TEST VARIÉTÉ DES RÉPONSES")
    print("=" * 35)
    
    try:
        manager = get_llm_manager()
        
        # Même message généré plusieurs fois
        test_message = "Bitcoin is pumping hard today! 🚀"
        responses = []
        
        print(f"💬 Message test: \"{test_message}\"")
        print(f"🔄 Génération de 3 réponses différentes...\n")
        
        for i in range(3):
            response = manager.generate_reply(
                system_prompt="You are MaxiMeme. Respond in French, be contextual and varied.",
                user_prompt=f"Respond to: {test_message}",
                max_tokens=60,
                temperature=0.9
            )
            
            if response:
                responses.append(response)
                print(f"🎯 Réponse {i+1}: \"{response}\"")
            else:
                print(f"❌ Réponse {i+1}: Échec")
        
        # Analyser la variété
        if len(responses) >= 2:
            unique_responses = len(set(responses))
            variety_score = unique_responses / len(responses) * 100
            
            print(f"\n📊 Analyse variété:")
            print(f"   📝 Réponses générées: {len(responses)}")
            print(f"   🎭 Réponses uniques: {unique_responses}")
            print(f"   📈 Score variété: {variety_score:.1f}%")
            
            if variety_score >= 80:
                print(f"   ✅ Excellente variété!")
            elif variety_score >= 60:
                print(f"   ⚠️ Variété acceptable")
            else:
                print(f"   ❌ Trop de répétitions")
            
            return variety_score >= 60
        else:
            print("❌ Pas assez de réponses pour tester la variété")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test variété: {e}")
        return False

def main():
    """Test complet des réponses GPT"""
    print("🤖 TEST COMPLET RÉPONSES GPT")
    print("=" * 45)
    
    # Test 1: Réponses contextuelles
    contextual_results = test_contextual_responses()
    
    # Test 2: Variété des réponses
    variety_result = test_response_variety()
    
    # Résumé final
    print(f"\n{'='*45}")
    print(f"📊 RÉSUMÉ DES TESTS GPT")
    print("="*30)
    
    if contextual_results:
        good_responses = [r for r in contextual_results if r.get('is_good', False)]
        print(f"🎯 Réponses contextuelles: {len(good_responses)}/{len(contextual_results)}")
        
        for result in contextual_results:
            status = "✅" if result.get('is_good', False) else "❌"
            print(f"   {status} {result['category']}")
    
    variety_status = "✅" if variety_result else "❌"
    print(f"🎭 Variété des réponses: {variety_status}")
    
    # Score global
    if contextual_results:
        good_count = len([r for r in contextual_results if r.get('is_good', False)])
        total_count = len(contextual_results)
        success_rate = good_count / total_count if total_count > 0 else 0
        
        print(f"\n🏆 Score global: {good_count}/{total_count} ({success_rate:.1%})")
        
        if success_rate >= 0.8 and variety_result:
            print(f"🎉 RÉPONSES GPT EXCELLENTES!")
            print(f"✅ Contextuelles, variées, et engageantes")
        elif success_rate >= 0.6:
            print(f"⚠️ Réponses GPT correctes mais perfectibles")
        else:
            print(f"❌ Réponses GPT nécessitent amélioration")
    
    print(f"\n💡 Pour améliorer:")
    print(f"   • Ajuster température dans prompts.json")
    print(f"   • Optimiser les prompts système") 
    print(f"   • Vérifier force_llm: true")

if __name__ == "__main__":
    main() 