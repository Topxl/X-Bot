#!/usr/bin/env python3
"""
Script de Migration vers Nouvelle Architecture

Ce script aide à migrer du système actuel vers :
- Dependency Injection Container
- Event Bus System  
- Error Recovery Manager
- Messages d'erreur informatifs

Usage:
    python scripts/migrate_to_new_architecture.py [--dry-run] [--backup]
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Ajouter le path pour les imports
sys.path.append(str(Path(__file__).parent.parent / "core"))

from loguru import logger


class ArchitectureMigrator:
    """
    Migrateur pour la nouvelle architecture
    
    Transforme le code existant pour utiliser :
    - DI Container au lieu de singletons
    - Event Bus pour la communication
    - Error Recovery pour la robustesse
    """
    
    def __init__(self, dry_run: bool = False, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.project_root = Path(__file__).parent.parent
        self.core_dir = self.project_root / "core"
        self.backup_dir = self.project_root / "backup_old_architecture"
        
        # Configuration des transformations
        self.singleton_patterns = [
            "get_config_manager",
            "get_storage_manager", 
            "get_twitter_manager",
            "get_content_generator",
            "get_task_scheduler",
            "get_reply_handler",
            "get_prompt_manager"
        ]
        
        # Mapping vers nouvelle architecture
        self.service_mapping = {
            "get_config_manager": "container.get('config')",
            "get_storage_manager": "container.get('storage')",
            "get_twitter_manager": "container.get('twitter')",
            "get_content_generator": "container.get('content')",
            "get_task_scheduler": "container.get('scheduler')",
            "get_reply_handler": "container.get('reply_handler')",
            "get_prompt_manager": "container.get('prompts')"
        }
    
    def run_migration(self) -> bool:
        """
        Lance la migration complète
        
        Returns:
            bool: True si succès, False sinon
        """
        logger.info("🚀 Starting architecture migration to new pattern...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No files will be modified")
        
        try:
            # 1. Backup si demandé
            if self.backup and not self.dry_run:
                self._create_backup()
            
            # 2. Analyser le code existant
            analysis = self._analyze_current_code()
            self._report_analysis(analysis)
            
            # 3. Créer les nouveaux imports
            self._add_new_imports()
            
            # 4. Transformer les singletons en DI
            self._transform_singletons()
            
            # 5. Ajouter error recovery
            self._add_error_recovery()
            
            # 6. Créer exemple d'utilisation
            self._create_usage_examples()
            
            # 7. Générer guide de migration
            self._generate_migration_guide()
            
            logger.success("✅ Architecture migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Crée un backup de l'architecture actuelle"""
        logger.info("💾 Creating backup of current architecture...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # Copier les fichiers core
        core_backup = self.backup_dir / "core"
        shutil.copytree(self.core_dir, core_backup)
        
        # Copier start.py
        if (self.project_root / "start.py").exists():
            shutil.copy2(self.project_root / "start.py", self.backup_dir)
        
        logger.info(f"✅ Backup created in: {self.backup_dir}")
    
    def _analyze_current_code(self) -> Dict[str, Any]:
        """Analyse le code actuel pour identifier les patterns"""
        logger.info("🔍 Analyzing current code patterns...")
        
        analysis = {
            'singleton_usage': {},
            'error_patterns': {},
            'files_to_modify': [],
            'potential_issues': []
        }
        
        # Scanner tous les fichiers Python
        for py_file in self.core_dir.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Chercher usage des singletons
                for pattern in self.singleton_patterns:
                    if pattern in content:
                        if pattern not in analysis['singleton_usage']:
                            analysis['singleton_usage'][pattern] = []
                        analysis['singleton_usage'][pattern].append(str(py_file))
                        
                        if str(py_file) not in analysis['files_to_modify']:
                            analysis['files_to_modify'].append(str(py_file))
                
                # Chercher patterns d'erreur problématiques
                error_patterns = [
                    "except Exception as e:",
                    "return None",
                    "pass  # TODO",
                    "raise NotImplementedError"
                ]
                
                for pattern in error_patterns:
                    if pattern in content:
                        if pattern not in analysis['error_patterns']:
                            analysis['error_patterns'][pattern] = []
                        analysis['error_patterns'][pattern].append(str(py_file))
                
            except Exception as e:
                analysis['potential_issues'].append(f"Could not read {py_file}: {e}")
        
        return analysis
    
    def _report_analysis(self, analysis: Dict[str, Any]) -> None:
        """Affiche le rapport d'analyse"""
        logger.info("📊 Migration Analysis Report:")
        logger.info("=" * 50)
        
        # Singletons usage
        if analysis['singleton_usage']:
            logger.info("🔧 Singleton patterns found:")
            for pattern, files in analysis['singleton_usage'].items():
                logger.info(f"   • {pattern}: {len(files)} files")
                for file in files[:3]:  # Show first 3
                    logger.info(f"     - {Path(file).name}")
                if len(files) > 3:
                    logger.info(f"     ... and {len(files) - 3} more")
        
        # Error patterns
        if analysis['error_patterns']:
            logger.info("⚠️ Error patterns to improve:")
            for pattern, files in analysis['error_patterns'].items():
                logger.info(f"   • {pattern}: {len(files)} files")
        
        # Files to modify
        logger.info(f"📝 Files requiring modification: {len(analysis['files_to_modify'])}")
        
        # Issues
        if analysis['potential_issues']:
            logger.warning("❗ Potential issues:")
            for issue in analysis['potential_issues']:
                logger.warning(f"   • {issue}")
    
    def _add_new_imports(self) -> None:
        """Ajoute les imports pour la nouvelle architecture"""
        logger.info("📦 Adding new architecture imports...")
        
        # Template d'imports pour la nouvelle architecture
        new_imports = '''
# Nouvelle architecture - Imports ajoutés par migration
from container import get_container
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity
'''
        
        # Ajouter aux fichiers principaux
        main_files = [
            self.core_dir / "main.py",
            self.core_dir / "twitter_api.py", 
            self.core_dir / "generator.py",
            self.core_dir / "storage.py"
        ]
        
        for file_path in main_files:
            if not file_path.exists():
                continue
                
            logger.info(f"   📝 Adding imports to {file_path.name}")
            
            if not self.dry_run:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Vérifier si déjà ajouté
                    if "from container import" in content:
                        continue
                    
                    # Trouver position d'insertion (après les imports existants)
                    lines = content.split('\n')
                    insert_position = 0
                    
                    for i, line in enumerate(lines):
                        if line.startswith('from ') or line.startswith('import '):
                            insert_position = i + 1
                    
                    # Insérer les nouveaux imports
                    lines.insert(insert_position, new_imports)
                    
                    file_path.write_text('\n'.join(lines), encoding='utf-8')
                    
                except Exception as e:
                    logger.error(f"Failed to add imports to {file_path}: {e}")
    
    def _transform_singletons(self) -> None:
        """Transforme les singletons en DI"""
        logger.info("🔄 Transforming singletons to DI container...")
        
        for file_path in self.core_dir.rglob("*.py"):
            if file_path.name.startswith("test_") or file_path.name in ["container.py", "events.py", "error_handler.py"]:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Remplacer chaque singleton pattern
                for old_pattern, new_pattern in self.service_mapping.items():
                    if old_pattern in content:
                        logger.info(f"   🔧 Transforming {old_pattern}() in {file_path.name}")
                        
                        # Remplacer les appels
                        content = content.replace(f"{old_pattern}()", new_pattern)
                        
                        # Ajouter container si nécessaire
                        if "container = get_container()" not in content and "container.get(" in content:
                            # Trouver une bonne position pour ajouter
                            lines = content.split('\n')
                            
                            # Chercher une fonction ou méthode
                            for i, line in enumerate(lines):
                                if ("def " in line and "def __" not in line) or "class " in line:
                                    # Ajouter après la définition
                                    if i + 1 < len(lines):
                                        indent = "    " if "def " in line else ""
                                        lines.insert(i + 1, f"{indent}container = get_container()")
                                        break
                            content = '\n'.join(lines)
                
                # Écrire si changements
                if content != original_content and not self.dry_run:
                    file_path.write_text(content, encoding='utf-8')
                    logger.info(f"   ✅ Updated {file_path.name}")
                elif content != original_content:
                    logger.info(f"   🔍 Would update {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Failed to transform {file_path}: {e}")
    
    def _add_error_recovery(self) -> None:
        """Ajoute error recovery aux fonctions critiques"""
        logger.info("🛡️ Adding error recovery patterns...")
        
        # Fonctions critiques à protéger
        critical_functions = [
            "post_tweet",
            "generate_tweet_content", 
            "save_tweet",
            "like_reply",
            "check_mentions"
        ]
        
        for file_path in self.core_dir.rglob("*.py"):
            if file_path.name.startswith("test_"):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                modified = False
                
                for i, line in enumerate(lines):
                    # Chercher définitions de fonctions critiques
                    for func_name in critical_functions:
                        if f"def {func_name}" in line and "@safe_execute" not in lines[i-1]:
                            logger.info(f"   🛡️ Adding error recovery to {func_name} in {file_path.name}")
                            
                            if not self.dry_run:
                                # Déterminer les paramètres du décorateur
                                decorator = "    @safe_execute(\n"
                                decorator += "        user_message_key='general_error',\n"
                                decorator += "        severity=ErrorSeverity.MEDIUM,\n"
                                decorator += f"        module='{file_path.stem}'\n"
                                decorator += "    )"
                                
                                # Insérer le décorateur
                                lines.insert(i, decorator)
                                modified = True
                                break
                
                if modified and not self.dry_run:
                    file_path.write_text('\n'.join(lines), encoding='utf-8')
                    
            except Exception as e:
                logger.error(f"Failed to add error recovery to {file_path}: {e}")
    
    def _create_usage_examples(self) -> None:
        """Crée des exemples d'utilisation de la nouvelle architecture"""
        logger.info("📖 Creating usage examples...")
        
        examples_dir = self.project_root / "examples" 
        if not self.dry_run:
            examples_dir.mkdir(exist_ok=True)
        
        # Exemple 1: Utilisation du DI Container
        di_example = '''"""
Exemple d'utilisation du DI Container

Ce fichier montre comment utiliser la nouvelle architecture
de dependency injection pour un code plus modulaire.
"""

from core.container import get_container
from core.events import get_event_bus, EventTypes
from core.error_handler import safe_execute, ErrorSeverity

def example_di_usage():
    """Exemple d'utilisation du container DI"""
    
    # Obtenir le container
    container = get_container()
    
    # Utiliser les services via DI (plus de singletons!)
    config = container.get('config')
    twitter = container.get('twitter') 
    storage = container.get('storage')
    
    print(f"Services loaded: {list(container.get_registered_services().keys())}")
    
    return True

@safe_execute(
    user_message_key="twitter_api_error",
    severity=ErrorSeverity.MEDIUM,
    fallback_category="content_generation",
    module="example"
)
def example_error_recovery():
    """Exemple de fonction avec récupération d'erreur"""
    
    # Cette fonction est automatiquement protégée
    # Les erreurs sont gérées avec des messages utilisateur
    # Et des fallbacks automatiques
    
    container = get_container()
    twitter = container.get('twitter')
    
    # Si cette ligne échoue, l'error handler gère automatiquement
    result = twitter.post_tweet("Test avec error recovery!")
    
    return result

def example_event_usage():
    """Exemple d'utilisation du système d'événements"""
    
    event_bus = get_event_bus()
    
    # S'abonner à un événement
    def handle_tweet_posted(event):
        print(f"Tweet posted: {event.data}")
    
    event_bus.subscribe(EventTypes.TWEET_POSTED, handle_tweet_posted)
    
    # Publier un événement  
    event_bus.publish(
        EventTypes.TWEET_POSTED,
        data={'tweet_id': '123', 'content': 'Hello World!'},
        source='example'
    )
    
    # Voir les statistiques
    stats = event_bus.get_stats()
    print(f"Event stats: {stats}")

if __name__ == "__main__":
    print("🚀 Testing new architecture examples...")
    
    example_di_usage()
    example_error_recovery() 
    example_event_usage()
    
    print("✅ Examples completed!")
'''
        
        if not self.dry_run:
            (examples_dir / "new_architecture_examples.py").write_text(di_example)
        
        logger.info(f"   📖 Created DI container example")
    
    def _generate_migration_guide(self) -> None:
        """Génère un guide de migration détaillé"""
        logger.info("📚 Generating migration guide...")
        
        guide_content = f'''# Guide de Migration - Nouvelle Architecture

## Vue d'ensemble

Cette migration transforme le bot Twitter d'une architecture basée sur des singletons vers une architecture moderne utilisant :

- **Dependency Injection Container** : Gestion flexible des dépendances
- **Event Bus System** : Communication découplée entre modules  
- **Error Recovery Manager** : Gestion robuste des erreurs avec fallbacks
- **Messages utilisateur informatifs** : UX améliorée lors d'erreurs

## Changements majeurs

### 1. Remplacement des Singletons

**Avant :**
```python
config_manager = get_config_manager()
twitter_manager = get_twitter_manager() 
```

**Après :**
```python
container = get_container()
config_manager = container.get('config')
twitter_manager = container.get('twitter')
```

### 2. Gestion d'erreur améliorée

**Avant :**
```python
def post_tweet(content):
    try:
        # ... code ...
        return result
    except Exception as e:
        logger.error(f"Failed: {{e}}")
        return None
```

**Après :**
```python
@safe_execute(
    user_message_key="twitter_api_error",
    severity=ErrorSeverity.MEDIUM,
    fallback_category="content_generation"
)
def post_tweet(content):
    # ... code ...
    # Erreurs gérées automatiquement avec messages utilisateur
    # et fallbacks intelligents
    return result
```

### 3. Communication par événements

**Avant :**
```python
# Couplage direct entre modules
if tweet_posted:
    storage.save_tweet(tweet_data)
    metrics.update_stats() 
```

**Après :**
```python
# Communication découplée via événements
event_bus.publish(
    EventTypes.TWEET_POSTED,
    data=tweet_data,
    source='twitter_manager'
)
# Les autres modules écoutent et réagissent automatiquement
```

## Migration étape par étape

### Étape 1: Backup
```bash
# Backup automatique créé dans: {self.backup_dir}
```

### Étape 2: Installation des nouveaux modules
- ✅ `core/container.py` - DI Container
- ✅ `core/events.py` - Event Bus System  
- ✅ `core/error_handler.py` - Error Recovery Manager
- ✅ `core/new_main.py` - Nouveau main avec architecture

### Étape 3: Migration du code existant
- 🔄 Transformation automatique des singletons
- 🛡️ Ajout d'error recovery aux fonctions critiques
- 📦 Ajout des imports nécessaires

### Étape 4: Tests et validation
```bash
# Tester la nouvelle architecture
python core/new_main.py

# Comparer avec l'ancienne version si besoin
python core/main.py
```

## Avantages de la nouvelle architecture

### 🎯 **Dependency Injection**
- ✅ Tests unitaires simplifiés (injection de mocks)
- ✅ Configuration flexible par environnement
- ✅ Cycle de vie des objets contrôlé
- ✅ Couplage réduit entre modules

### 📡 **Event Bus**
- ✅ Modules découplés 
- ✅ Extensibilité (nouveaux handlers facilement)
- ✅ Monitoring et debugging améliorés
- ✅ Architecture réactive

### 🛡️ **Error Recovery**
- ✅ Messages utilisateur informatifs (plus de logs techniques)
- ✅ Fallbacks automatiques (le bot continue malgré les erreurs)
- ✅ Statistiques d'erreur détaillées
- ✅ Alertes pour erreurs critiques

## Comparaison performance

| Aspect | Avant | Après |
|--------|-------|-------|
| **Startup** | Singleton lazy loading | DI container optimisé |
| **Memory** | Objets globaux persistants | Gestion cycle de vie |
| **Errors** | Arrêt brutal | Graceful degradation |
| **Extensibility** | Modification directe | Event handlers + DI |
| **Testing** | Singletons difficiles | Injection facile |

## Migration personnalisée

Pour adapter cette migration à vos besoins spécifiques :

1. **Ajouter de nouveaux services :**
```python
container.register('mon_service', MonServiceClass, singleton=True)
```

2. **Créer des événements personnalisés :**
```python
class MonEventTypes:
    CUSTOM_EVENT = "mon.evenement.custom"
    
event_bus.subscribe(MonEventTypes.CUSTOM_EVENT, mon_handler)
```

3. **Définir des fallbacks spécifiques :**
```python
error_manager.register_fallback(
    'ma_categorie',
    FallbackStrategy('mon_fallback', ma_fonction_fallback)
)
```

## Fichiers à réviser manuellement

Après la migration automatique, vérifiez ces aspects :

- [ ] **Imports** : Tous les nouveaux imports sont présents
- [ ] **Tests** : Mise à jour des tests pour utiliser DI
- [ ] **Configuration** : Paramètres de logging et error recovery
- [ ] **Monitoring** : Handlers d'événements pour vos métriques
- [ ] **Deployment** : Scripts de déploiement mis à jour

## Support et troubleshooting

En cas de problème :

1. **Logs détaillés** disponibles avec la nouvelle architecture
2. **Event history** pour debugging : `event_bus.get_recent_events()`
3. **Error statistics** : `error_manager.get_error_stats()`
4. **Service health** : Monitoring intégré dans `new_main.py`

## Date de migration
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
🎉 **Félicitations !** Votre bot utilise maintenant une architecture moderne, robuste et extensible.
'''
        
        if not self.dry_run:
            (self.project_root / "MIGRATION_GUIDE.md").write_text(guide_content)
        
        logger.info("   📚 Migration guide created: MIGRATION_GUIDE.md")


def main():
    """Point d'entrée du script de migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate to new architecture")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without modifying files")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    
    args = parser.parse_args()
    
    # Configuration du logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    print("🏗️ Architecture Migration Tool")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    
    if args.no_backup:
        print("⚠️ No backup will be created")
    
    print()
    
    # Lancer la migration
    migrator = ArchitectureMigrator(
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Review MIGRATION_GUIDE.md")
        print("2. Test new architecture: python core/new_main.py")
        print("3. Update your deployment scripts")
        print("4. Run tests to validate functionality")
    else:
        print("\n❌ Migration failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 