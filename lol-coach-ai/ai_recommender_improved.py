"""
PATCH AMÉLIORÉ POUR AIRecommender
Remplace la méthode recommend_build() par une version complète et intelligente
"""

def recommend_build_improved(self, my_champion, enemy_champions, live_game=None, my_team_id=None):
    """Recommande un build COMPLET basé sur:
    - TES stats personnelles (WR par item)
    - Stats GLOBALES des items (WR global)
    - Stats du champion (AD/AP, classe)
    - Composition ennemie (champions, items qu'ils build)
    - Synergies items (combos)
    """

    enemy_analysis = self.analyze_enemy_composition(enemy_champions)
    champ_data = self.api.champions_data.get(my_champion)

    if not champ_data:
        return {"error": f"Champion {my_champion} non trouvé"}

    champ_class = BuildDatabase.get_champion_class(champ_data)
    champ_dmg = BuildDatabase.get_champion_damage_type(champ_data)

    build = {
        "champion": my_champion,
        "class": champ_class,
        "damage_type": champ_dmg,
        "boots": {"name": "", "why": ""},
        "mythic": None,
        "core_items": [],
        "defensive_items": [],
        "situational": [],
        "anti_heal": None,
        "warnings": [],
        "analysis": {
            "enemy_composition": enemy_analysis,
            "your_stats": {
                "class": champ_class,
                "damage_type": champ_dmg
            }
        }
    }

    # ===== ÉTAPE 1: ANALYSER LES STATS DU CHAMPION =====
    your_builds = self.stats.get_best_builds(my_champion, min_games=2)
    
    # ===== ÉTAPE 2: SÉLECTIONNER MYTHIQUE =====
    mythic_item = self._select_mythic_item(my_champion, champ_dmg, champ_class, enemy_analysis, your_builds)
    if mythic_item:
        build["mythic"] = mythic_item

    # ===== ÉTAPE 3: SÉLECTIONNER BOOTS =====
    boots = self._select_boots(champ_class, champ_dmg, enemy_analysis)
    build["boots"] = boots

    # ===== ÉTAPE 4: ITEMS OFFENSIFS CORE =====
    core_items = self._select_core_items(my_champion, champ_dmg, champ_class, enemy_analysis, your_builds)
    build["core_items"] = core_items

    # ===== ÉTAPE 5: ITEMS DÉFENSIFS =====
    defensive_items = self._select_defensive_items(my_champion, champ_dmg, champ_class, enemy_analysis)
    build["defensive_items"] = defensive_items

    # ===== ÉTAPE 6: ANTI-HEAL SI NÉCESSAIRE =====
    if enemy_analysis["healing_threat"]:
        anti_heal = self._select_anti_heal(my_champion, champ_dmg, champ_class, enemy_analysis)
        if anti_heal:
            build["anti_heal"] = anti_heal

    # ===== ÉTAPE 7: ITEMS SITUATIONNELS =====
    situational = self._select_situational_items(my_champion, champ_dmg, champ_class, enemy_analysis)
    build["situational"] = situational

    # ===== ÉTAPE 8: GÉNÉRER LA SÉQUENCE PRIORITAIRE =====
    build["priority_sequence"] = self._generate_priority_sequence(build)

    # ===== ÉTAPE 9: ADAPTER SI PARTIE EN COURS =====
    if live_game and my_team_id is not None:
        try:
            adaptive_build = self._adapt_build_to_live_game(build, live_game, my_team_id, my_champion)
            return adaptive_build
        except Exception as e:
            print(f"⚠️ Erreur adaptation live: {e}")
            return build

    return build


def _select_mythic_item(self, champion, dmg_type, champ_class, enemy_analysis, your_builds):
    """Sélectionne le meilleur item mythique basé sur les stats"""
    
    mythic_candidates = []
    
    # Mythiques AD
    if dmg_type == "ad":
        mythic_candidates = [
            {"id": 6631, "name": "Stridebreaker", "for": ["fighter", "tank"]},
            {"id": 6630, "name": "Goredrinker", "for": ["fighter"]},
            {"id": 6632, "name": "Divine Sunderer", "for": ["fighter"]},
            {"id": 3078, "name": "Trinity Force", "for": ["fighter"]},
            {"id": 6673, "name": "Immortal Shieldbow", "for": ["adc"]},
            {"id": 6672, "name": "Kraken Slayer", "for": ["adc"]},
            {"id": 6671, "name": "Galeforce", "for": ["adc"]},
        ]
    # Mythiques AP
    elif dmg_type == "ap":
        mythic_candidates = [
            {"id": 6655, "name": "Luden's Companion", "for": ["mage"]},
            {"id": 6653, "name": "Liandry's Torment", "for": ["mage"]},
            {"id": 6656, "name": "Everfrost", "for": ["mage"]},
            {"id": 6657, "name": "Rod of Ages", "for": ["mage"]},
            {"id": 4633, "name": "Riftmaker", "for": ["mage"]},
        ]
    # Mythiques Support/Tank
    else:
        mythic_candidates = [
            {"id": 3190, "name": "Locket of the Iron Solari", "for": ["support", "tank"]},
            {"id": 6662, "name": "Iceborn Gauntlet", "for": ["tank"]},
            {"id": 6664, "name": "Hollow Radiance", "for": ["tank"]},
            {"id": 3084, "name": "Heartsteel", "for": ["tank"]},
        ]

    best_mythic = None
    best_score = 0

    for mythic in mythic_candidates:
        # Vérifier si c'est approprié pour la classe
        if champ_class not in mythic.get("for", []):
            continue

        score = 50  # baseline

        # Bonus si tu as joué cet item avec succès
        if your_builds:
            best_items = your_builds.get("best_items", [])
            for item in best_items:
                if item.get("item_id") == mythic["id"]:
                    score += item.get("winrate", 50) - 50
                    score += 10  # Bonus pour expérience personnelle

        # Bonus basé sur la composition ennemie
        item_stats = self.items_db.extract_item_stats(mythic["id"])
        item_passives = self.items_db.get_item_passives(mythic["id"])

        # Défense vs composition
        if enemy_analysis["ad_damage"] >= 2 and item_stats["armor"] > 0:
            score += 5
        if enemy_analysis["ap_damage"] >= 2 and item_stats["mr"] > 0:
            score += 5

        # Passifs utiles
        if enemy_analysis["tank_count"] >= 2 and ("pen" in item_passives or "armor_pen" in item_passives):
            score += 15
        if enemy_analysis["assassin_count"] >= 2 and ("survival" in item_passives or "shield" in item_passives):
            score += 10

        if score > best_score:
            best_score = score
            best_mythic = {
                "id": mythic["id"],
                "name": mythic["name"],
                "score": round(best_score, 1),
                "why": f"Mythique optimal pour {champ_class} vs cette compo"
            }

    return best_mythic


def _select_boots(self, champ_class, dmg_type, enemy_analysis):
    """Sélectionne les boots optimales"""
    
    boots_options = []

    # Défense magique
    if enemy_analysis["cc_heavy"] or enemy_analysis["ap_damage"] >= 3:
        boots_options.append({
            "name": "Mercury's Treads",
            "why": f"CC heavy + {enemy_analysis['ap_damage']:.0f} AP ennemis",
            "priority": 10
        })

    # Défense physique
    if enemy_analysis["ad_damage"] >= 3:
        boots_options.append({
            "name": "Plated Steelcaps",
            "why": f"{enemy_analysis['ad_damage']:.0f} AD ennemis",
            "priority": 9
        })

    # Offensif
    if dmg_type == "ap":
        boots_options.append({
            "name": "Sorcerer's Shoes",
            "why": "Pénétration magique",
            "priority": 5
        })
    elif champ_class == "adc":
        boots_options.append({
            "name": "Berserker's Greaves",
            "why": "Vitesse d'attaque ADC",
            "priority": 5
        })
    else:
        boots_options.append({
            "name": "Ionian Boots of Lucidity",
            "why": "Ability Haste",
            "priority": 3
        })

    # Sélectionner les meilleures boots
    if boots_options:
        boots_options.sort(key=lambda x: x["priority"], reverse=True)
        return boots_options[0]

    return {"name": "Plated Steelcaps", "why": "Défense standard"}


def _select_core_items(self, champion, dmg_type, champ_class, enemy_analysis, your_builds):
    """Sélectionne les items offensifs core"""
    
    core_items = []

    if not your_builds:
        return core_items

    best_items = your_builds.get("best_items", [])

    for item in best_items[:5]:
        item_id = item.get("item_id", 0)
        item_name = item.get("name", "Unknown")
        personal_wr = item.get("winrate", 50)
        games = item.get("games", 0)

        # Extraire les stats
        item_stats = self.items_db.extract_item_stats(item_id)
        item_passives = self.items_db.get_item_passives(item_id)

        # Calculer un score composite
        score = personal_wr  # Commencer par ton WR personnel

        # Bonus si stats correspondent au champion
        if dmg_type == "ad" and item_stats["ad"] > 0:
            score += min(item_stats["ad"] / 50 * 10, 15)
        elif dmg_type == "ap" and item_stats["ap"] > 0:
            score += min(item_stats["ap"] / 30 * 10, 15)

        # Bonus si utile vs composition
        if enemy_analysis["tank_count"] >= 2 and ("pen" in item_passives or "armor_pen" in item_passives):
            score += 10
        if enemy_analysis["ad_damage"] >= 2 and item_stats["armor"] > 0:
            score += 5
        if enemy_analysis["ap_damage"] >= 2 and item_stats["mr"] > 0:
            score += 5

        reasons = []
        if games >= 3:
            reasons.append(f"Ton WR: {personal_wr:.0f}% ({games}g)")
        if item_stats["ad"] > 0:
            reasons.append(f"+{item_stats['ad']:.0f} AD")
        if item_stats["ap"] > 0:
            reasons.append(f"+{item_stats['ap']:.0f} AP")
        if item_stats["ah"] > 0:
            reasons.append(f"+{item_stats['ah']:.0f}% AH")
        if "pen" in item_passives or "armor_pen" in item_passives:
            reasons.append("Pénétration")

        core_items.append({
            "id": item_id,
            "name": item_name,
            "score": round(score, 1),
            "personal_wr": round(personal_wr, 1),
            "stats": item_stats,
            "passives": item_passives,
            "reasons": reasons
        })

    core_items.sort(key=lambda x: x["score"], reverse=True)
    return core_items[:3]


def _select_defensive_items(self, champion, dmg_type, champ_class, enemy_analysis):
    """Sélectionne les items défensifs"""
    
    defensive_items = []

    # Défense vs AD
    if enemy_analysis["ad_damage"] >= 2:
        defensive_items.append({
            "name": "Thornmail" if champ_class == "tank" else "Randuin's Omen",
            "why": f"{enemy_analysis['ad_damage']:.0f} AD ennemis",
            "priority": 8
        })

    # Défense vs AP
    if enemy_analysis["ap_damage"] >= 2:
        defensive_items.append({
            "name": "Banshee's Veil" if dmg_type == "ad" else "Spirit Visage",
            "why": f"{enemy_analysis['ap_damage']:.0f} AP ennemis",
            "priority": 8
        })

    # Survie vs assassins
    if enemy_analysis["assassin_count"] >= 2:
        defensive_items.append({
            "name": "Zhonya's Hourglass" if dmg_type == "ap" else "Guardian Angel",
            "why": f"{enemy_analysis['assassin_count']} assassins",
            "priority": 9
        })

    # Survie vs engage
    if enemy_analysis["engage_threat"]:
        defensive_items.append({
            "name": "Abyssal Mask" if dmg_type == "ap" else "Kaenic Rookern",
            "why": "Réduction des dégâts vs engage",
            "priority": 6
        })

    defensive_items.sort(key=lambda x: x["priority"], reverse=True)
    return defensive_items[:2]


def _select_anti_heal(self, champion, dmg_type, champ_class, enemy_analysis):
    """Sélectionne l'item anti-heal si vraiment utile"""
    
    # Vérifier si ce champion bénéficie d'anti-heal
    if not self._should_build_anti_heal(champion, dmg_type, champ_class):
        return None

    if dmg_type == "ad":
        return {
            "name": "Mortal Reminder",
            "why": f"Anti-heal vs {', '.join(enemy_analysis['healing_champions'][:2])}",
            "priority": 7
        }
    else:
        return {
            "name": "Morellonomicon",
            "why": f"Anti-heal vs {', '.join(enemy_analysis['healing_champions'][:2])}",
            "priority": 7
        }


def _select_situational_items(self, champion, dmg_type, champ_class, enemy_analysis):
    """Sélectionne les items situationnels"""
    
    situational = []

    # Pénétration vs tanks
    if enemy_analysis["tank_count"] >= 2:
        if dmg_type == "ad":
            situational.append({
                "name": "Lord Dominik's Regards",
                "why": f"{enemy_analysis['tank_count']} tanks avec armure",
                "priority": 8
            })
        else:
            situational.append({
                "name": "Void Staff",
                "why": f"{enemy_analysis['tank_count']} tanks avec MR",
                "priority": 8
            })

    # Mobilité vs CC
    if enemy_analysis["cc_heavy"]:
        situational.append({
            "name": "Kaenic Rookern" if dmg_type == "ad" else "Abyssal Mask",
            "why": "Réduction dégâts vs CC",
            "priority": 6
        })

    # Sustain vs poke
    if enemy_analysis["mage_count"] >= 2:
        situational.append({
            "name": "Maw of Malmortius" if dmg_type == "ad" else "Adaptive Helm",
            "why": "Sustain vs poke mages",
            "priority": 5
        })

    situational.sort(key=lambda x: x["priority"], reverse=True)
    return situational[:2]


def _generate_priority_sequence(self, build):
    """Génère la séquence d'achat prioritaire"""
    
    sequence = []
    step = 1

    # 1. Mythique
    if build.get("mythic"):
        sequence.append({
            "step": step,
            "item": build["mythic"]["name"],
            "reason": build["mythic"]["why"],
            "type": "mythic"
        })
        step += 1

    # 2. Boots
    if build.get("boots") and build["boots"].get("name"):
        sequence.append({
            "step": step,
            "item": build["boots"]["name"],
            "reason": build["boots"]["why"],
            "type": "boots"
        })
        step += 1

    # 3. Items core offensifs
    for item in build.get("core_items", [])[:2]:
        sequence.append({
            "step": step,
            "item": item["name"],
            "reason": f"Core: {', '.join(item['reasons'][:2])}",
            "type": "core"
        })
        step += 1

    # 4. Anti-heal si nécessaire
    if build.get("anti_heal"):
        sequence.append({
            "step": step,
            "item": build["anti_heal"]["name"],
            "reason": build["anti_heal"]["why"],
            "type": "anti_heal"
        })
        step += 1

    # 5. Défensif si nécessaire
    for item in build.get("defensive_items", [])[:1]:
        sequence.append({
            "step": step,
            "item": item["name"],
            "reason": item["why"],
            "type": "defensive"
        })
        step += 1

    # 6. Situationnel
    for item in build.get("situational", [])[:1]:
        sequence.append({
            "step": step,
            "item": item["name"],
            "reason": item["why"],
            "type": "situational"
        })
        step += 1

    return sequence


def _adapt_build_to_live_game(self, build, live_game, my_team_id, champion):
    """Adapte la build si la partie est en cours"""
    
    try:
        # Analyser les items ennemis
        enemy_items = []
        for participant in live_game.get("participants", []):
            if participant.get("teamId") != my_team_id:
                enemy_items.extend(participant.get("items", []))

        # Si ennemis build beaucoup d'armure, recommander pénétration
        armor_count = sum(1 for item_id in enemy_items if self.items_db.is_armor_item(item_id))
        if armor_count >= 3:
            build["warnings"] = build.get("warnings", [])
            build["warnings"].append("⚠️ Ennemis build beaucoup d'armure - Priorité pénétration!")

        # Si ennemis build beaucoup de MR
        mr_count = sum(1 for item_id in enemy_items if self.items_db.is_mr_item(item_id))
        if mr_count >= 3:
            build["warnings"] = build.get("warnings", [])
            build["warnings"].append("⚠️ Ennemis build beaucoup de MR - Priorité pénétration magique!")

    except Exception:
        pass

    return build
