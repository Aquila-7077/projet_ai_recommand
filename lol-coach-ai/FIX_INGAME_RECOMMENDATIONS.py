"""
FIX POUR L'OPTION 5 - RECOMMANDATIONS IN-GAME AMÉLIORÉES

Remplace la méthode _handle_in_game() pour afficher une build COMPLÈTE et intelligente
"""

def _handle_in_game_improved(self, game):
    """Gère l'affichage et recommandations pour une partie en cours - VERSION AMÉLIORÉE"""

    my_champion = game.get("my_champion")
    my_team = game.get("my_team", [])
    enemy_team = game.get("enemy_team", [])
    game_time = game.get("game_time_seconds", 0)
    is_ranked = game.get("is_ranked", False)

    print(f"\n🎮 TU ES EN GAME!")
    print(f"   Mode: {'RANKED' if is_ranked else 'Normal/Practice'}")

    if game_time > 0:
        mins = game_time // 60
        secs = game_time % 60
        print(f"   Durée: {mins}:{secs:02d}")

    if my_champion:
        print(f"\n   🎮 Tu joues: {my_champion}")
    else:
        print(f"\n   ⚠️ Champion non détecté")
        return

    # Nettoyer les équipes (enlever None/vides)
    my_team_clean = [c for c in my_team if c]
    enemy_team_clean = [c for c in enemy_team if c]

    if my_team_clean:
        print(f"   👥 Ton équipe: {' '.join(my_team_clean)}")

    if enemy_team_clean:
        print(f"   👹 Ennemis: {' '.join(enemy_team_clean)}")
    else:
        print(f"   👹 Ennemis: Non détectés (Practice Tool?)")

    # ===== PRÉDICTION DE VICTOIRE =====
    if enemy_team_clean:  # Seulement si on a des ennemis
        prediction = self.stats.predict_win_chance(my_champion, my_team_clean, enemy_team_clean)

        print(f"\n{'─' * 80}")
        print(f"🔮 PRÉDICTION DE VICTOIRE")
        print(f"{'─' * 80}")

        confidence_icon = "🟢" if prediction['confidence'] == "HIGH" else "🟡" if prediction['confidence'] == "MEDIUM" else "🔴"
        print(f"\n   {prediction['win_chance']:.0f}% de chances de victoire {confidence_icon}")
        print(f"   Confiance: {prediction['confidence']}")

        if prediction['factors']:
            print(f"\n   Facteurs:")
            for key, value in list(prediction['factors'].items())[:3]:
                print(f"   • {key}: {value}")

        if prediction['recommendations']:
            print(f"\n   Conseils:")
            for rec in prediction['recommendations'][:2]:
                print(f"   {rec}")

    # ===== RECOMMANDATIONS BUILD COMPLÈTES =====
    print(f"\n{'─' * 80}")
    print(f"⚡ RECOMMANDATIONS BUILD COMPLÈTES")
    print(f"{'─' * 80}")

    # Utiliser enemy_team même vide (pour Practice Tool)
    build = self.recommender.recommend_build(
        my_champion,
        enemy_team_clean if enemy_team_clean else [],
        live_game=game,
        my_team_id=game.get('participants', [{}])[0].get('teamId') if game.get('participants') else None
    )

    # ===== 1. AFFICHER WARNINGS =====
    if build.get('warnings'):
        print(f"\n⚠️ ALERTES:")
        for w in build['warnings'][:3]:
            print(f"   {w}")

    # ===== 2. AFFICHER MYTHIQUE =====
    mythic = build.get('mythic')
    if mythic:
        print(f"\n🏆 MYTHIQUE (1er item):")
        print(f"   {mythic.get('name', 'N/A')}")
        print(f"   → {mythic.get('why', 'Optimal')}")
        print(f"   Score: {mythic.get('score', 0)}/100")

    # ===== 3. AFFICHER BOOTS =====
    boots = build.get('boots', {})
    if boots and boots.get('name'):
        print(f"\n🥾 BOTTES:")
        print(f"   {boots.get('name', 'N/A')}")
        print(f"   → {boots.get('why', 'Standard')}")

    # ===== 4. AFFICHER ITEMS CORE OFFENSIFS =====
    core_items = build.get('core_items', [])
    if core_items:
        print(f"\n📊 ITEMS CORE OFFENSIFS (Top 3):")
        for i, item in enumerate(core_items[:3], 1):
            wr = item.get('personal_wr', 0)
            games = item.get('games', 0)
            score = item.get('score', 0)
            star = "⭐" if wr >= 55 else ""
            
            print(f"\n   {i}. {item.get('name', 'Unknown')} {star}")
            print(f"      Ton WR: {wr}% ({games}g)")
            print(f"      Score: {score}/100")
            
            # Afficher les raisons
            reasons = item.get('reasons', [])
            if reasons:
                print(f"      Raisons:")
                for reason in reasons[:3]:
                    print(f"        • {reason}")

    # ===== 5. AFFICHER ITEMS DÉFENSIFS =====
    defensive_items = build.get('defensive_items', [])
    if defensive_items:
        print(f"\n🛡️ ITEMS DÉFENSIFS:")
        for item in defensive_items[:2]:
            print(f"   • {item.get('name', 'Unknown')}")
            print(f"     → {item.get('why', '')}")

    # ===== 6. AFFICHER ANTI-HEAL =====
    anti_heal = build.get('anti_heal')
    if anti_heal:
        when_text = anti_heal.get('when', 'Quand nécessaire')
        if "Optionnel" in when_text:
            print(f"\n🟡 ANTI-HEAL (optionnel):")
        else:
            print(f"\n💊 ANTI-HEAL (RECOMMANDÉ):")
        print(f"   {anti_heal.get('name', 'N/A')}")
        print(f"   → {anti_heal.get('why', '')}")

    # ===== 7. AFFICHER ITEMS SITUATIONNELS =====
    situational = build.get('situational', [])
    if situational:
        print(f"\n🎯 ITEMS SITUATIONNELS:")
        for item in situational[:2]:
            print(f"   • {item.get('name', 'Unknown')}")
            print(f"     → {item.get('why', '')}")

    # ===== 8. AFFICHER SÉQUENCE D'ACHAT PRIORITAIRE =====
    priority_seq = build.get('priority_sequence', [])
    if priority_seq:
        print(f"\n📋 SÉQUENCE D'ACHAT PRIORITAIRE:")
        for seq in priority_seq[:6]:
            step = seq.get('step', 0)
            item = seq.get('item', 'Unknown')
            reason = seq.get('reason', '')
            item_type = seq.get('type', '')
            
            # Emoji par type
            emoji_map = {
                'mythic': '🏆',
                'boots': '🥾',
                'core': '📊',
                'anti_heal': '💊',
                'defensive': '🛡️',
                'situational': '🎯'
            }
            emoji = emoji_map.get(item_type, '•')
            
            print(f"   {step}. {emoji} {item}")
            print(f"      → {reason}")

    # ===== 9. AFFICHER PLAYSTYLE =====
    playstyle = self.stats.get_playstyle_analysis(my_champion)
    if playstyle:
        print(f"\n��� RAPPEL PLAYSTYLE:")
        print(f"   🎯 Tu es {playstyle['playstyle']} player sur {my_champion}")
        print(f"   💬 {playstyle['tip']}")
        print(f"   📊 Avg CS/min: {playstyle['avg_cs_per_min']}")
        print(f"   💰 Avg Gold/min: {playstyle['avg_gold_per_min']:.0f}")

    # ===== 10. AFFICHER ANALYSE COMPOSITION ENNEMIE =====
    if build.get('analysis'):
        analysis = build['analysis'].get('enemy_composition', {})
        if analysis:
            print(f"\n🔍 ANALYSE COMPOSITION ENNEMIE:")
            print(f"   Tanks: {analysis.get('tank_count', 0)}")
            print(f"   Assassins: {analysis.get('assassin_count', 0)}")
            print(f"   Mages: {analysis.get('mage_count', 0)}")
            print(f"   ADCs: {analysis.get('adc_count', 0)}")
            print(f"   Dégâts AD: {analysis.get('ad_damage', 0):.1f}")
            print(f"   Dégâts AP: {analysis.get('ap_damage', 0):.1f}")

    print(f"\n{'─' * 80}")
    print("✅ Recommandations générées basées sur:")
    print("   • Tes stats personnelles (WR par item)")
    print("   • Composition ennemie")
    print("   • Stats du champion")
    print("   • Tendances récentes")
    print(f"{'─' * 80}\n")
