#!/usr/bin/env python3
"""
Générateur de Tweets Viraux - Stratégies Nick Huber
==================================================

Utilitaire simple pour générer des tweets viraux optimisés
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "core"))

def generate_viral_tweet(topic=None, content_type=None, strategy=None):
    """Génère un tweet viral avec analyse"""
    try:
        from container import get_container
        
        # Obtenir le générateur de contenu via DI Container
        container = get_container()
        content_generator = container.get('content')
        
        print(f"🎯 Génération d'un tweet viral...")
        if topic:
            print(f"   Sujet: {topic}")
        if content_type:
            print(f"   Type: {content_type}")
        if strategy:
            print(f"   Stratégie: {strategy}")
        print()
        
        # Générer le tweet viral
        viral_tweet = content_generator.generate_viral_tweet(
            topic=topic,
            content_type=content_type,
            strategy=strategy
        )
        
        if viral_tweet:
            print("✅ TWEET VIRAL GÉNÉRÉ!")
            print("=" * 50)
            print(viral_tweet)
            print("=" * 50)
            print(f"📏 Longueur: {len(viral_tweet)} caractères")
            
            # Analyser le potentiel viral
            print("\n📊 ANALYSE DU POTENTIEL VIRAL:")
            analysis = content_generator.get_viral_analysis(viral_tweet)
            
            if "error" not in analysis:
                scores = analysis.get('scores', {})
                print(f"   📈 Score global: {scores.get('overall', 0):.2f}/1.0")
                print(f"   🎯 Grade: {analysis.get('grade', 'N/A')}")
                print(f"   💪 Hook strength: {scores.get('hook_strength', 0):.2f}")
                print(f"   🔥 Stance clarity: {scores.get('stance_clarity', 0):.2f}")
                print(f"   📋 Specificity: {scores.get('specificity', 0):.2f}")
                print(f"   ⚡ Controversy: {scores.get('controversy', 0):.2f}")
                print(f"   🛑 Pattern interrupt: {scores.get('pattern_interrupt', 0):.2f}")
                
                print(f"\n💭 {analysis.get('overall_assessment', '')}")
                
                if analysis.get('recommendations'):
                    print(f"\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
                    for i, rec in enumerate(analysis['recommendations'], 1):
                        print(f"   {i}. {rec}")
                        
            else:
                print(f"   ❌ Erreur d'analyse: {analysis['error']}")
                
            return viral_tweet
        else:
            print("❌ Échec de la génération du tweet viral")
            return None
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Interface principale"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Générateur de Tweets Viraux - Stratégies Nick Huber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python generate_viral_tweet.py --topic "Bitcoin vs Ethereum"
  python generate_viral_tweet.py --type controversial_stance --strategy provocation
  python generate_viral_tweet.py --topic "DeFi regulation" --type educational_value --strategy education
  
Types de contenu disponibles:
  - powerful_hook         : Hook puissant pour capturer l'attention
  - controversial_stance  : Position controversée qui polarise
  - educational_value     : Contenu éducatif avec valeur ajoutée
  - personal_insight      : Insight personnel authentique
  - problem_solver        : Solution à un problème spécifique
  
Stratégies d'engagement:
  - entertainment : Faire rire (divertissement)
  - provocation   : Déclencher de l'émotion (provocation)
  - education     : Enseigner quelque chose d'utile (éducation)
        """
    )
    
    parser.add_argument(
        '--topic', '-t',
        help='Sujet du tweet (ex: "Bitcoin maximalism", "DeFi vs banks")'
    )
    
    parser.add_argument(
        '--type', '-c',
        choices=['powerful_hook', 'controversial_stance', 'educational_value', 'personal_insight', 'problem_solver'],
        help='Type de contenu viral'
    )
    
    parser.add_argument(
        '--strategy', '-s',
        choices=['entertainment', 'provocation', 'education'],
        help='Stratégie d\'engagement'
    )
    
    parser.add_argument(
        '--multiple', '-m',
        type=int,
        default=1,
        help='Générer plusieurs tweets (défaut: 1)'
    )
    
    parser.add_argument(
        '--analyze-only', '-a',
        help='Analyser un tweet existant au lieu d\'en générer un nouveau'
    )
    
    args = parser.parse_args()
    
    print("🤖 Générateur de Tweets Viraux - Stratégies Nick Huber")
    print("=" * 60)
    
    if args.analyze_only:
        # Mode analyse seulement
        try:
            from container import get_container
            container = get_container()
            content_generator = container.get('content')
            
            print(f"📊 Analyse du tweet: {args.analyze_only}")
            print("-" * 40)
            
            analysis = content_generator.get_viral_analysis(args.analyze_only)
            
            if "error" not in analysis:
                scores = analysis.get('scores', {})
                print(f"📈 Score global: {scores.get('overall', 0):.2f}/1.0")
                print(f"🎯 Grade: {analysis.get('grade', 'N/A')}")
                print(f"💭 {analysis.get('overall_assessment', '')}")
                
                if analysis.get('recommendations'):
                    print(f"\n💡 Recommandations:")
                    for i, rec in enumerate(analysis['recommendations'], 1):
                        print(f"   {i}. {rec}")
            else:
                print(f"❌ Erreur: {analysis['error']}")
                
        except Exception as e:
            print(f"❌ Erreur d'analyse: {e}")
        
        return
    
    # Mode génération
    for i in range(args.multiple):
        if args.multiple > 1:
            print(f"\n🔄 Tweet #{i+1}/{args.multiple}")
            print("-" * 30)
            
        tweet = generate_viral_tweet(
            topic=args.topic,
            content_type=args.type,
            strategy=args.strategy
        )
        
        if tweet and args.multiple > 1 and i < args.multiple - 1:
            input("\n⏸️  Appuyez sur Entrée pour le tweet suivant...")

if __name__ == "__main__":
    main() 