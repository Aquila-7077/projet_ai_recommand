# 📚 EXEMPLES D'UTILISATION - SYSTÈME DE RECOMMANDATION AMÉLIORÉ

## 🎮 Exemple 1 : Garen vs Composition CC Heavy

### Requête
```bash
curl -X POST http://localhost:5000/api/recommend/build/Garen \
  -H "Content-Type: application/json" \
  -d '{
    "enemies": ["Leona", "Morgana", "Lux", "Ashe", "Soraka"]
  }'
```

### Réponse
```json
{
  "champion": "Garen",
  "class": "fighter",
  "damage_type": "ad",
  "mythic": {
    "id": 6631,
    "name": "Stridebreaker",
    "score": 72.5,
    "why": "Mythique optimal pour fighter vs cette compo"
  },
  "boots": {
    "name": "Mercury's Treads",
    "why": "CC heavy + 3 AP ennemis",
    "priority": 10
  },
  "core_items": [
    {
      "id": 3071,
      "name": "Black Cleaver",
      "score": 68.3,
      "personal_wr": 62.5,
      "stats": {
        "ad": 55,
        "ah": 20,
        "hp": 300
      },
      "passives": ["ad", "ah", "cleave"],
      "reasons": [
        "Ton WR: 62.5% (8g)",
        "+55 AD",
        "+20% AH",
        "Pénétration"
      ]
    },
    {
      "id": 3143,
      "name": "Randuin's Omen",
      "score": 61.2,
      "personal_wr": 58.0,
      "stats": {
        "armor": 60,
        "hp": 400
      },
      "passives": ["armor", "slow"],
      "reasons": [
        "Ton WR: 58.0% (5g)",
        "+60 Armor",
        "Slow vs AD"
      ]
    }
  ],
  "defensive_items": [
    {
      "name": "Thornmail",
      "why": "3 AD ennemis",
      "priority": 8
    }
  ],
  "anti_heal": {
    "name": "Mortal Reminder",
    "why": "Anti-heal vs Soraka, Yuumi",
    "priority": 7
  },
  "situational": [
    {
      "name": "Lord Dominik's Regards",
      "why": "2 tanks avec armure",
      "priority": 8
    }
  ],
  "priority_sequence": [
    {
      "step": 1,
      "item": "Stridebreaker",
      "reason": "Mythique optimal pour fighter vs cette compo",
      "type": "mythic"
    },
    {
      "step": 2,
      "item": "Mercury's Treads",
      "reason": "CC heavy + 3 AP ennemis",
      "type": "boots"
    },
    {
      "step": 3,
      "item": "Black Cleaver",
      "reason": "Core: Ton WR: 62.5%, +55 AD, Pénétration",
      "type": "core"
    },
    {
      "step": 4,
      "item": "Mortal Reminder",
      "reason": "Anti-heal vs Soraka, Yuumi",
      "type": "anti_heal"
    },
    {
      "step": 5,
      "item": "Thornmail",
      "reason": "3 AD ennemis",
      "type": "defensive"
    },
    {
      "step": 6,
      "item": "Lord Dominik's Regards",
      "reason": "2 tanks avec armure",
      "type": "situational"
    }
  ],
  "analysis": {
    "enemy_composition": {
      "tank_count": 1,
      "assassin_count": 0,
      "mage_count": 2,
      "adc_count": 1,
      "fighter_count": 0,
      "ap_damage": 2.5,
      "ad_damage": 1.5,
      "healing_threat": true,
      "cc_heavy": true,
      "engage_threat": true,
      "healing_champions": ["Soraka"],
      "cc_champions": ["Leona", "Morgana"],
      "engage_champions": ["Leona"]
    },
    "your_stats": {
      "class": "fighter",
      "damage_type": "ad"
    }
  }
}
```

### Interprétation
- **Mythique** : Stridebreaker pour la mobilité vs CC
- **Boots** : Mercury's pour la résistance au CC et à l'AP
- **Core** : Black Cleaver pour l'AD et la pénétration
- **Défensif** : Thornmail pour l'armure vs AD
- **Anti-heal** : Mortal Reminder vs Soraka
- **Situationnel** : Lord Dominik's vs tanks

---

## 🎮 Exemple 2 : ADC vs Composition Assassin

### Requête
```bash
curl -X POST http://localhost:5000/api/recommend/build/Ashe \
  -H "Content-Type: application/json" \
  -d '{
    "enemies": ["Zed", "Rengar", "LeBlanc", "Thresh", "Evelynn"]
  }'
```

### Réponse (résumé)
```json
{
  "champion": "Ashe",
  "class": "adc",
  "damage_type": "ad",
  "mythic": {
    "name": "Immortal Shieldbow",
    "score": 78.5,
    "why": "Mythique optimal pour ADC vs 3 assassins"
  },
  "boots": {
    "name": "Plated Steelcaps",
    "why": "2 AD assassins (Zed, Rengar)",
    "priority": 9
  },
  "core_items": [
    {
      "name": "Kraken Slayer",
      "score": 72.1,
      "personal_wr": 65.0,
      "reasons": ["Ton WR: 65.0% (10g)", "+80 AD", "Crit", "Pen"]
    },
    {
      "name": "Rapid Firecannon",
      "score": 68.5,
      "personal_wr": 60.0,
      "reasons": ["Ton WR: 60.0% (6g)", "+80 AD", "Crit", "Mobilité"]
    }
  ],
  "defensive_items": [
    {
      "name": "Guardian Angel",
      "why": "3 assassins (Zed, Rengar, LeBlanc)",
      "priority": 9
    }
  ],
  "priority_sequence": [
    {"step": 1, "item": "Immortal Shieldbow", "reason": "Mythique optimal vs assassins", "type": "mythic"},
    {"step": 2, "item": "Plated Steelcaps", "reason": "2 AD assassins", "type": "boots"},
    {"step": 3, "item": "Kraken Slayer", "reason": "Core: Ton WR: 65.0%, +80 AD", "type": "core"},
    {"step": 4, "item": "Guardian Angel", "reason": "3 assassins", "type": "defensive"}
  ]
}
```

### Interprétation
- **Mythique** : Immortal Shieldbow pour le shield vs assassins
- **Boots** : Plated Steelcaps pour l'armure vs AD assassins
- **Core** : Kraken Slayer pour le crit et la pénétration
- **Défensif** : Guardian Angel pour la survie vs assassins

---

## 🎮 Exemple 3 : Mage vs Composition Tank

### Requête
```bash
curl -X POST http://localhost:5000/api/recommend/build/Lux \
  -H "Content-Type: application/json" \
  -d '{
    "enemies": ["Malphite", "Ornn", "Leona", "Ashe", "Soraka"]
  }'
```

### Réponse (résumé)
```json
{
  "champion": "Lux",
  "class": "mage",
  "damage_type": "ap",
  "mythic": {
    "name": "Luden's Companion",
    "score": 75.3,
    "why": "Mythique optimal pour mage vs 2 tanks"
  },
  "boots": {
    "name": "Sorcerer's Shoes",
    "why": "Pénétration magique",
    "priority": 5
  },
  "core_items": [
    {
      "name": "Void Staff",
      "score": 82.1,
      "personal_wr": 68.0,
      "reasons": ["Ton WR: 68.0% (12g)", "+80 AP", "Pénétration MR", "vs 2 tanks"]
    },
    {
      "name": "Liandry's Torment",
      "score": 71.5,
      "personal_wr": 62.0,
      "reasons": ["Ton WR: 62.0% (8g)", "+80 AP", "Dégâts vs tanks"]
    }
  ],
  "defensive_items": [
    {
      "name": "Zhonya's Hourglass",
      "why": "Survie vs Leona engage",
      "priority": 7
    }
  ],
  "anti_heal": {
    "name": "Morellonomicon",
    "why": "Anti-heal vs Soraka",
    "priority": 6
  },
  "priority_sequence": [
    {"step": 1, "item": "Luden's Companion", "reason": "Mythique optimal", "type": "mythic"},
    {"step": 2, "item": "Sorcerer's Shoes", "reason": "Pénétration magique", "type": "boots"},
    {"step": 3, "item": "Void Staff", "reason": "Core: Ton WR: 68.0%, Pénétration MR vs 2 tanks", "type": "core"},
    {"step": 4, "item": "Morellonomicon", "reason": "Anti-heal vs Soraka", "type": "anti_heal"},
    {"step": 5, "item": "Zhonya's Hourglass", "reason": "Survie vs Leona", "type": "defensive"}
  ]
}
```

### Interprétation
- **Mythique** : Luden's pour l'AP et la pénétration
- **Boots** : Sorcerer's pour la pénétration magique
- **Core** : Void Staff pour la pénétration MR vs tanks
- **Anti-heal** : Morellonomicon vs Soraka
- **Défensif** : Zhonya's pour la survie vs Leona

---

## 🎮 Exemple 4 : Support vs Composition Engage

### Requête
```bash
curl -X POST http://localhost:5000/api/recommend/build/Thresh \
  -H "Content-Type: application/json" \
  -d '{
    "enemies": ["Malphite", "Hecarim", "Zed", "Ashe", "Evelynn"]
  }'
```

### Réponse (résumé)
```json
{
  "champion": "Thresh",
  "class": "support",
  "damage_type": "ad",
  "mythic": {
    "name": "Locket of the Iron Solari",
    "score": 76.2,
    "why": "Mythique optimal pour support vs 2 engage"
  },
  "boots": {
    "name": "Plated Steelcaps",
    "why": "2 AD (Zed, Ashe)",
    "priority": 8
  },
  "core_items": [
    {
      "name": "Hollow Radiance",
      "score": 69.3,
      "personal_wr": 61.0,
      "reasons": ["Ton WR: 61.0% (7g)", "Armure", "MR", "Réduction dégâts"]
    }
  ],
  "defensive_items": [
    {
      "name": "Kaenic Rookern",
      "why": "Réduction dégâts vs engage",
      "priority": 8
    }
  ],
  "priority_sequence": [
    {"step": 1, "item": "Locket of the Iron Solari", "reason": "Mythique optimal", "type": "mythic"},
    {"step": 2, "item": "Plated Steelcaps", "reason": "2 AD", "type": "boots"},
    {"step": 3, "item": "Hollow Radiance", "reason": "Core: Ton WR: 61.0%, Armure + MR", "type": "core"},
    {"step": 4, "item": "Kaenic Rookern", "reason": "Réduction dégâts vs engage", "type": "defensive"}
  ]
}
```

### Interprétation
- **Mythique** : Locket pour le shield d'équipe
- **Boots** : Plated Steelcaps pour l'armure
- **Core** : Hollow Radiance pour l'armure et la MR
- **Défensif** : Kaenic Rookern pour la réduction de dégâts

---

## 📊 Comparaison des recommandations

### Garen vs CC Heavy
```
Mythique: Stridebreaker (mobilité)
Boots: Mercury's (CC resist)
Core: Black Cleaver (AD + pen)
Défensif: Thornmail (armor)
Anti-heal: Mortal Reminder
```

### Ashe vs Assassins
```
Mythique: Immortal Shieldbow (shield)
Boots: Plated Steelcaps (armor)
Core: Kraken Slayer (crit + pen)
Défensif: Guardian Angel (survie)
```

### Lux vs Tanks
```
Mythique: Luden's (AP + pen)
Boots: Sorcerer's (magic pen)
Core: Void Staff (MR pen)
Anti-heal: Morellonomicon
Défensif: Zhonya's (survie)
```

### Thresh vs Engage
```
Mythique: Locket (team shield)
Boots: Plated Steelcaps (armor)
Core: Hollow Radiance (armor + MR)
Défensif: Kaenic Rookern (dmg reduction)
```

---

## 🔍 Analyse des scores

### Score composite
```
Score = (WR personnel * 0.6) + (Fit composition * 0.4)

Exemple Black Cleaver pour Garen:
- WR personnel: 62.5%
- Fit composition: 75% (AD + pen vs tanks)
- Score = (62.5 * 0.6) + (75 * 0.4) = 37.5 + 30 = 67.5
```

### Raisons détaillées
```
Chaque item inclut :
- Ton WR personnel avec cet item
- Stats extraites (AD, AP, AH, etc.)
- Passifs utiles
- Bonus vs composition
```

---

## 💡 Conseils d'utilisation

1. **Suivez la séquence** : L'ordre proposé est optimal
2. **Adaptez si nécessaire** : Si vous êtes très en retard, adaptez
3. **Vérifiez les raisons** : Comprenez pourquoi chaque item est recommandé
4. **Utilisez en live** : Les recommandations s'adaptent en live game
5. **Testez différentes compos** : Voyez comment les recommandations changent

---

## 🎯 Résumé

Le système de recommandation amélioré propose maintenant :

✅ **Mythique** adapté à votre champion et la composition  
✅ **Boots** optimales pour la survie  
✅ **Core items** avec scoring composite  
✅ **Défensif** basé sur les menaces  
✅ **Anti-heal** intelligent  
✅ **Situationnel** pour l'adaptation  
✅ **Séquence** d'achat prioritaire  
✅ **Raisons** détaillées pour chaque item  

**Résultat** : Des builds **précises, justifiées et adaptées**!
