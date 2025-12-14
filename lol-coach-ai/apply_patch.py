#!/usr/bin/env python3
"""
Script d'application automatique du patch de recommandation améliorée
"""

import os
import re
import shutil
from datetime import datetime

def apply_patch():
    """Applique le patch au fichier lol_coach.py"""
    
    print("=" * 70)
    print("🔧 APPLICATION DU PATCH - SYSTÈME DE RECOMMANDATION AMÉLIORÉ")
    print("=" * 70)
    print()
    
    # Chemins
    main_file = "lol_coach.py"
    patch_file = "ai_recommender_improved.py"
    backup_file = f"lol_coach.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Vérifications
    if not os.path.exists(main_file):
        print(f"❌ Erreur: {main_file} non trouvé!")
        return False
    
    if not os.path.exists(patch_file):
        print(f"❌ Erreur: {patch_file} non trouvé!")
        return False
    
    print(f"✅ Fichiers trouvés")
    print(f"   - {main_file}")
    print(f"   - {patch_file}")
    print()
    
    # Créer une sauvegarde
    print(f"💾 Création d'une sauvegarde...")
    try:
        shutil.copy(main_file, backup_file)
        print(f"   ✅ Sauvegarde créée: {backup_file}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        return False
    
    print()
    
    # Lire les fichiers
    print("📖 Lecture des fichiers...")
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            main_content = f.read()
        with open(patch_file, 'r', encoding='utf-8') as f:
            patch_content = f.read()
        print("   ✅ Fichiers lus avec succès")
    except Exception as e:
        print(f"   ❌ Erreur lors de la lecture: {e}")
        return False
    
    print()
    
    # Extraire les nouvelles méthodes du patch
    print("🔍 Extraction des nouvelles méthodes...")
    
    # Extraire les fonctions du patch
    methods = {}
    
    # Pattern pour extraire chaque fonction
    pattern = r'def (_\w+)\(self.*?\n(?:.*?\n)*?(?=def _\w+\(self|$)'
    
    # Extraire manuellement les méthodes
    method_names = [
        "recommend_build_improved",
        "_select_mythic_item",
        "_select_boots",
        "_select_core_items",
        "_select_defensive_items",
        "_select_anti_heal",
        "_select_situational_items",
        "_generate_priority_sequence",
        "_adapt_build_to_live_game"
    ]
    
    print(f"   Méthodes à ajouter: {len(method_names)}")
    for method in method_names:
        print(f"      - {method}")
    
    print()
    
    # Trouver la classe AIRecommender
    print("🔎 Localisation de la classe AIRecommender...")
    
    ai_recommender_match = re.search(r'class AIRecommender:', main_content)
    if not ai_recommender_match:
        print("   ❌ Classe AIRecommender non trouvée!")
        return False
    
    print(f"   ✅ Classe trouvée à la position {ai_recommender_match.start()}")
    
    print()
    
    # Trouver la méthode recommend_build existante
    print("🔎 Localisation de la méthode recommend_build()...")
    
    # Pattern pour trouver la méthode recommend_build
    recommend_build_pattern = r'def recommend_build\(self.*?\n(?:.*?\n)*?(?=\n    def |\nclass |\Z)'
    recommend_build_match = re.search(recommend_build_pattern, main_content, re.DOTALL)
    
    if not recommend_build_match:
        print("   ❌ Méthode recommend_build() non trouvée!")
        return False
    
    print(f"   ✅ Méthode trouvée")
    print(f"      Position: {recommend_build_match.start()}")
    print(f"      Longueur: {len(recommend_build_match.group())} caractères")
    
    print()
    
    # Créer le contenu de remplacement
    print("✏️  Préparation du remplacement...")
    
    # Extraire les nouvelles méthodes du patch
    new_methods_code = patch_content.replace("def recommend_build_improved(", "def recommend_build(")
    
    # Ajouter les nouvelles méthodes après recommend_build
    replacement_code = new_methods_code
    
    print("   ✅ Code de remplacement préparé")
    
    print()
    
    # Effectuer le remplacement
    print("🔄 Remplacement de la méthode...")
    
    try:
        new_content = main_content[:recommend_build_match.start()] + replacement_code + main_content[recommend_build_match.end():]
        print("   ✅ Remplacement effectué")
    except Exception as e:
        print(f"   ❌ Erreur lors du remplacement: {e}")
        return False
    
    print()
    
    # Sauvegarder le fichier modifié
    print("💾 Sauvegarde du fichier modifié...")
    
    try:
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"   ✅ Fichier {main_file} mis à jour")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        # Restaurer la sauvegarde
        shutil.copy(backup_file, main_file)
        print(f"   🔄 Sauvegarde restaurée depuis {backup_file}")
        return False
    
    print()
    print("=" * 70)
    print("✅ PATCH APPLIQUÉ AVEC SUCCÈS!")
    print("=" * 70)
    print()
    print("📝 Résumé des changements:")
    print("   • Méthode recommend_build() complètement refondue")
    print("   • 8 nouvelles méthodes helper ajoutées")
    print("   • Scoring intelligent des items")
    print("   • Analyse complète de composition")
    print("   • Adaptation live game")
    print()
    print("💾 Sauvegarde de sécurité:")
    print(f"   {backup_file}")
    print()
    print("🚀 Prêt à utiliser!")
    print()
    
    return True


if __name__ == "__main__":
    success = apply_patch()
    exit(0 if success else 1)
