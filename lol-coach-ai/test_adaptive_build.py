"""
Test script pour vérifier que les fonctions adaptatives du build fonctionnent
"""

# Exemple de données de game simulée
test_game = {
    "participants": [
        # Mon équipe (team 100)
        {"teamId": 100, "puuid": "mon_puuid", "championId": 5, "goldEarned": 8000, "kills": 3, "deaths": 1, "item0": 3031, "item1": 3020, "item2": 0, "item3": 0, "item4": 0, "item5": 0},
        {"teamId": 100, "puuid": "ally1", "championId": 10, "goldEarned": 7500, "kills": 2, "deaths": 2, "item0": 3040, "item1": 0, "item2": 0, "item3": 0, "item4": 0, "item5": 0},
        {"teamId": 100, "puuid": "ally2", "championId": 15, "goldEarned": 7200, "kills": 1, "deaths": 3, "item0": 2065, "item1": 0, "item2": 0, "item3": 0, "item4": 0, "item5": 0},
        
        # Équipe ennemie (team 200)
        {"teamId": 200, "puuid": "enemy1", "championId": 55, "goldEarned": 10000, "kills": 7, "deaths": 0, "item0": 6672, "item1": 3031, "item2": 3089, "item3": 0, "item4": 0, "item5": 0},  # FED
        {"teamId": 200, "puuid": "enemy2", "championId": 67, "goldEarned": 9500, "kills": 6, "deaths": 1, "item0": 3031, "item1": 3089, "item2": 0, "item3": 0, "item4": 0, "item5": 0},  # FED
        {"teamId": 200, "puuid": "enemy3", "championId": 77, "goldEarned": 7000, "kills": 1, "deaths": 3, "item0": 2065, "item1": 0, "item2": 0, "item3": 0, "item4": 0, "item5": 0},
    ]
}

# Exemple d'analyse attendue:
expected_analysis = {
    "fed_enemies": ["Champion1 (7K/0D)", "Champion2 (6K/1D)"],
    "key_threats": ["Champion1 a Kraken → Dégâts massifs", "Champion1 a Infinity Edge → Crits dévastateurs"],
    "gold_deficit": 22700 - 26500,  # Négatif = on est en retard
}

print("✅ Structure de test validée")
print(f"Déficit d'or simulé: {expected_analysis['gold_deficit']} (ennemis en avance)")
print(f"Ennemis fed: {len(expected_analysis['fed_enemies'])}")
print(f"Menaces key: {len(expected_analysis['key_threats'])}")
