"""
Stratégies de Tweets Viraux - Basé sur Nick Huber
=================================================

Implémente les techniques éprouvées pour créer du contenu viral :
- Structure gagnante (Hook → Stance → Specificity → Impact)
- Sélection de sujets polarisants 
- Psychologie de l'engagement
- Formatage optimisé
"""

import random
from typing import Dict, List, Tuple, Optional
from loguru import logger
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Types de contenu viral"""
    POWERFUL_HOOK = "powerful_hook"
    CONTROVERSIAL_STANCE = "controversial_stance"
    EDUCATIONAL_VALUE = "educational_value"
    PERSONAL_INSIGHT = "personal_insight"
    PROBLEM_SOLVER = "problem_solver"


class EngagementStrategy(Enum):
    """Stratégies d'engagement"""
    ENTERTAINMENT = "entertainment"  # Make people laugh
    PROVOCATION = "provocation"     # Strike emotion
    EDUCATION = "education"         # Teach something useful


@dataclass
class ViralStructure:
    """Structure d'un tweet viral selon Nick Huber"""
    hook: str           # Powerful first line (1/8 second to capture)
    stance: str         # Bold, authoritative position
    specificity: str    # Precise numbers, relatable examples
    impact: str         # Optional follow-up, CTA, reinforcement


class ViralStrategies:
    """
    Générateur de contenu viral basé sur les techniques de Nick Huber
    
    Implémente la formule gagnante :
    1. Hook puissant (première ligne)
    2. Position ferme (éviter la nuance)
    3. Spécificité (chiffres, exemples)
    4. Impact (call to action optionnel)
    """
    
    def __init__(self):
        self.hooks = self._load_viral_hooks()
        self.stance_patterns = self._load_stance_patterns()
        self.specificity_enhancers = self._load_specificity_enhancers()
        self.impact_closers = self._load_impact_closers()
        self.controversial_topics = self._load_controversial_topics()
        
    def _load_viral_hooks(self) -> List[str]:
        """Hooks puissants pour capturer l'attention en 1/8 seconde"""
        return [
            "If you {action}, you're not {positive_trait}. You're {negative_trait}.",
            "Most people fail at {topic} because they {wrong_approach}.",
            "The {industry} doesn't want you to know this:",
            "I just realized why {majority_group} stay {undesired_state}:",
            "Unpopular opinion: {controversial_statement}",
            "Everyone talks about {popular_thing}, but nobody mentions {overlooked_thing}.",
            "After {specific_time} doing {activity}, here's what I learned:",
            "The {expert_group} are lying to you about {topic}:",
            "You're doing {common_activity} wrong. Here's why:",
            "Stop {common_behavior}. Start {alternative_behavior}.",
            "This will be controversial but:",
            "Hot take: {bold_statement}",
            "I lost {specific_amount} because I believed this myth:",
            "The truth about {topic} that nobody talks about:",
            "If you want to {achieve_goal}, stop {common_mistake}."
        ]
    
    def _load_stance_patterns(self) -> List[str]:
        """Patterns pour prendre une position ferme"""
        return [
            "There's no middle ground here. Either {option_a} or {option_b}.",
            "I don't care if this offends people: {bold_statement}",
            "The data is clear: {factual_claim}",
            "After {experience}, I'm convinced that {conclusion}",
            "Anyone who says {common_belief} has never {relevant_experience}",
            "The {timeframe} rule: {specific_guideline}",
            "Here's the hard truth: {uncomfortable_reality}",
            "If you disagree with this, you're {consequence}",
            "This is exactly why {group} {outcome}:",
            "The proof is in the numbers: {statistic}"
        ]
    
    def _load_specificity_enhancers(self) -> Dict[str, List[str]]:
        """Éléments pour ajouter de la spécificité"""
        return {
            "timeframes": [
                "20 hours a week", "3 months", "18 months", "5 years", 
                "6 AM every day", "every Sunday morning", "the last 2 years"
            ],
            "precise_numbers": [
                "87% of", "exactly 23", "within 48 hours", "after 1,247 attempts",
                "in 15 minutes", "costs $47", "saves 3.5 hours daily"
            ],
            "specific_examples": [
                "like when Elon tweeted about Dogecoin",
                "the same way Netflix killed Blockbuster",
                "just like the iPhone replaced BlackBerry",
                "similar to how Amazon started with books"
            ],
            "relatable_scenarios": [
                "scrolling Twitter at 2 AM",
                "checking charts during dinner",
                "explaining crypto to your parents",
                "watching your portfolio during a crash"
            ]
        }
    
    def _load_impact_closers(self) -> List[str]:
        """Closers pour maximiser l'impact"""
        return [
            "Agree or disagree? 👇",
            "Change my mind. I'll wait.",
            "Unpopular opinion but someone had to say it.",
            "This is exactly why {outcome}.",
            "If you don't believe me, try {specific_action}.",
            "Save this post. You'll thank me later.",
            "Most people won't do this. Will you?",
            "That's how you {achieve_goal}.",
            "Now you know why {expert_group} do this.",
            "Share this if you agree. The truth needs to spread."
        ]
    
    def _load_controversial_topics(self) -> Dict[str, List[str]]:
        """Sujets qui polarisent dans le crypto/business"""
        return {
            "crypto": [
                "Bitcoin maximalism vs altcoins",
                "DeFi vs traditional banking", 
                "NFTs as investment vs art",
                "Centralized vs decentralized exchanges",
                "HODL vs day trading",
                "Proof of Work vs Proof of Stake",
                "Regulation vs decentralization"
            ],
            "business": [
                "Remote work vs office culture",
                "Hustle culture vs work-life balance", 
                "Formal education vs self-taught skills",
                "Networking vs skill building",
                "Taking risks vs playing it safe",
                "Following trends vs being contrarian"
            ],
            "lifestyle": [
                "Social media addiction",
                "Instant gratification culture",
                "Content consumption vs creation",
                "Following vs leading",
                "Comfort zone vs growth zone"
            ]
        }
    
    def generate_viral_structure(self, topic: str, content_type: ContentType, 
                               strategy: EngagementStrategy) -> ViralStructure:
        """
        Génère une structure virale complète
        
        Args:
            topic: Sujet du tweet
            content_type: Type de contenu viral
            strategy: Stratégie d'engagement
            
        Returns:
            ViralStructure: Structure complète du tweet viral
        """
        # Sélectionner un hook approprié
        hook = self._select_hook(topic, content_type)
        
        # Créer une position ferme
        stance = self._create_stance(topic, strategy)
        
        # Ajouter de la spécificité
        specificity = self._add_specificity(topic, stance)
        
        # Créer un impact closer
        impact = self._create_impact(topic, strategy)
        
        return ViralStructure(
            hook=hook,
            stance=stance,
            specificity=specificity,
            impact=impact
        )
    
    def _select_hook(self, topic: str, content_type: ContentType) -> str:
        """Sélectionne un hook approprié au sujet"""
        hooks = random.choices(self.hooks, k=3)
        
        # Customiser selon le type de contenu
        if content_type == ContentType.CONTROVERSIAL_STANCE:
            preferred = [h for h in hooks if any(word in h.lower() 
                       for word in ["unpopular", "controversial", "truth", "lying"])]
            return preferred[0] if preferred else hooks[0]
        
        elif content_type == ContentType.EDUCATIONAL_VALUE:
            preferred = [h for h in hooks if any(word in h.lower() 
                       for word in ["learned", "realize", "truth", "wrong"])]
            return preferred[0] if preferred else hooks[0]
            
        return hooks[0]
    
    def _create_stance(self, topic: str, strategy: EngagementStrategy) -> str:
        """Crée une position ferme et autoritaire"""
        pattern = random.choice(self.stance_patterns)
        
        # Adapter selon la stratégie
        if strategy == EngagementStrategy.PROVOCATION:
            return pattern.replace("{bold_statement}", f"{topic} is completely overrated")
        elif strategy == EngagementStrategy.EDUCATION:
            return pattern.replace("{conclusion}", f"{topic} works differently than most think")
        else:  # ENTERTAINMENT
            return pattern.replace("{bold_statement}", f"{topic} is funnier than people realize")
    
    def _add_specificity(self, topic: str, stance: str) -> str:
        """Ajoute des détails spécifiques et chiffrés"""
        specifics = []
        
        # Ajouter un chiffre précis
        number = random.choice(self.specificity_enhancers["precise_numbers"])
        specifics.append(f"{number} people who {topic.lower()}")
        
        # Ajouter un exemple relatable
        example = random.choice(self.specificity_enhancers["relatable_scenarios"])
        specifics.append(f"Like {example}")
        
        return " ".join(specifics)
    
    def _create_impact(self, topic: str, strategy: EngagementStrategy) -> str:
        """Crée un closer qui maximise l'impact"""
        closer = random.choice(self.impact_closers)
        
        # Personnaliser selon la stratégie
        if strategy == EngagementStrategy.PROVOCATION:
            return closer.replace("{outcome}", "people get triggered")
        elif strategy == EngagementStrategy.EDUCATION:
            return closer.replace("{achieve_goal}", f"master {topic}")
        
        return closer
    
    def format_viral_tweet(self, structure: ViralStructure) -> str:
        """
        Formate la structure en tweet viral optimisé
        
        Applique les règles de formatage de Nick Huber :
        - Texte digestible
        - Langage simple
        - Éviter les mots d'hésitation
        - Créer un pattern interrupt
        """
        lines = []
        
        # Hook (première ligne - crucial)
        lines.append(structure.hook)
        lines.append("")  # Ligne vide pour respiration
        
        # Stance (position ferme)
        lines.append(structure.stance)
        lines.append("")
        
        # Specificity (détails qui rendent crédible)
        lines.append(structure.specificity)
        lines.append("")
        
        # Impact (closer mémorable)
        lines.append(structure.impact)
        
        tweet = "\n".join(lines)
        
        # Optimisations finales
        tweet = self._apply_formatting_rules(tweet)
        
        return tweet
    
    def _apply_formatting_rules(self, text: str) -> str:
        """Applique les règles de formatage viral"""
        # Supprimer les mots d'hésitation
        hedging_words = ["maybe", "sometimes", "possibly", "perhaps", "might"]
        for word in hedging_words:
            text = text.replace(f" {word} ", " ")
            text = text.replace(f" {word.capitalize()} ", " ")
        
        # Simplifier le langage
        replacements = {
            "utilize": "use",
            "facilitate": "help", 
            "approximately": "about",
            "numerous": "many",
            "additionally": "also"
        }
        
        for complex_word, simple_word in replacements.items():
            text = text.replace(complex_word, simple_word)
            text = text.replace(complex_word.capitalize(), simple_word.capitalize())
        
        return text
    
    def get_viral_topic_suggestions(self, category: str = "crypto") -> List[str]:
        """Retourne des suggestions de sujets viraux"""
        if category in self.controversial_topics:
            return self.controversial_topics[category]
        return self.controversial_topics["crypto"]  # Default
    
    def analyze_viral_potential(self, text: str) -> Dict[str, float]:
        """
        Analyse le potentiel viral d'un tweet
        
        Returns:
            Dict avec scores pour différents aspects
        """
        scores = {
            "hook_strength": 0.0,      # Pouvoir du hook
            "stance_clarity": 0.0,     # Clarté de la position  
            "specificity": 0.0,        # Niveau de détail
            "controversy": 0.0,        # Potentiel de controverse
            "pattern_interrupt": 0.0,  # Capacité à arrêter le scroll
            "overall": 0.0             # Score global
        }
        
        # Analyser le hook (première ligne)
        first_line = text.split('\n')[0] if '\n' in text else text
        hook_indicators = ["if you", "most people", "unpopular", "truth", "wrong", "stop"]
        scores["hook_strength"] = sum(1 for indicator in hook_indicators 
                                    if indicator in first_line.lower()) / len(hook_indicators)
        
        # Analyser la clarté de position
        stance_indicators = ["there's no", "i don't care", "anyone who", "exactly why"]
        scores["stance_clarity"] = sum(1 for indicator in stance_indicators 
                                     if indicator in text.lower()) / len(stance_indicators)
        
        # Analyser la spécificité
        import re
        numbers = re.findall(r'\d+', text)
        specific_words = ["exactly", "precisely", "specific", "after", "within"]
        scores["specificity"] = (len(numbers) + sum(1 for word in specific_words 
                               if word in text.lower())) / 10
        
        # Analyser le potentiel de controverse
        controversial_words = ["controversial", "unpopular", "disagree", "wrong", "lying"]
        scores["controversy"] = sum(1 for word in controversial_words 
                                  if word in text.lower()) / len(controversial_words)
        
        # Pattern interrupt (mots qui arrêtent le scroll)
        interrupt_words = ["wait", "stop", "wrong", "lying", "truth", "secret"]
        scores["pattern_interrupt"] = sum(1 for word in interrupt_words 
                                        if word in text.lower()) / len(interrupt_words)
        
        # Score global
        scores["overall"] = sum(scores.values()) / (len(scores) - 1)
        
        return scores


# Factory function pour DI Container
def create_viral_strategies() -> ViralStrategies:
    """Factory function pour le DI Container"""
    return ViralStrategies()


# Instance globale (fallback)
_viral_strategies: Optional[ViralStrategies] = None

def get_viral_strategies() -> ViralStrategies:
    """Retourne l'instance globale des stratégies virales"""
    global _viral_strategies
    if _viral_strategies is None:
        _viral_strategies = ViralStrategies()
    return _viral_strategies 