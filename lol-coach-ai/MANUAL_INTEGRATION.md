# 🔧 GUIDE D'INTÉGRATION MANUELLE

Si le script `apply_patch.py` ne fonctionne pas, suivez ce guide pour intégrer manuellement les améliorations.

---

## 📍 Étape 1 : Localiser la classe AIRecommender

1. Ouvrez `lol_coach.py` dans votre éditeur
2. Utilisez Ctrl+F pour chercher : `class AIRecommender:`
3. Vous devriez trouver la classe vers la ligne **2064**

---

## 🔍 Étape 2 : Localiser la méthode recommend_build()

Dans la classe `AIRecommender`, cherchez la méthode :
```python
def recommend_build(self, my_champion, enemy_champions, live_game=None, my_team_id=None):
```

Cette méthode commence vers la ligne **2280** et se termine avant la prochaine méthode `def recommend_runes_and_spells()`.

---

## ✂️ Étape 3 : Remplacer la méthode recommend_build()

1. **Sélectionnez** tout le contenu de la méthode `recommend_build()` (du `def` jusqu'à la fin)
2. **Copiez** le contenu du fichier `ai_recommender_improved.py`
3. **Remplacez** la méthode existante par le nouveau code

**Important** : Assurez-vous que l'indentation est correcte (4 espaces pour les m��thodes de classe)

---

## ➕ Étape 4 : Ajouter les nouvelles méthodes helper

Après la méthode `recommend_build()`, ajoutez les 8 nouvelles méthodes du fichier `ai_recommender_improved.py` :

1. `_select_mythic_item()`
2. `_select_boots()`
3. `_select_core_items()`
4. `_select_defensive_items()`
5. `_select_anti_heal()`
6. `_select_situational_items()`
7. `_generate_priority_sequence()`
8. `_adapt_build_to_live_game()`

**Placement** : Juste avant la méthode `recommend_runes_and_spells()`

---

## ✅ Étape 5 : Vérifier l'intégration

1. **Sauvegardez** le fichier
2. **Testez** la syntaxe Python :
   ```bash
   python -m py_compile lol_coach.py
   ```
3. Si aucune erreur, l'intégration est réussie!

---

## 🧪 Étape 6 : Tester les recommandations

Lancez votre application et testez :

```bash
python app.py
```

Puis appelez l'endpoint :
```
POST /api/recommend/build/Garen
{
  "enemies": ["Leona", "Morgana", "Lux", "Ashe", "Soraka"]
}
```

Vous devriez recevoir une réponse complète avec :
- ✅ Mythique
- ✅ Boots
- ✅ Core items
- ✅ Defensive items
- ✅ Anti-heal
- ✅ Situational items
- ✅ Priority sequence

---

## 🐛 Dépannage

### Erreur : "IndentationError"
→ Vérifiez que l'indentation est correcte (4 espaces)

### Erreur : "NameError: name 'BuildDatabase' is not defined"
→ Assurez-vous que `BuildDatabase` est importée/définie avant `AIRecommender`

### Erreur : "AttributeError: 'AIRecommender' object has no attribute '_select_mythic_item'"
→ Vérifiez que toutes les 8 méthodes helper ont été ajoutées

### Recommandations vides
→ Vérifiez que vous avez au moins 2 games avec le champion

---

## 📋 Checklist d'intégration

- [ ] Fichier `lol_coach.py` ouvert
- [ ] Classe `AIRecommender` localisée
- [ ] Méthode `recommend_build()` localisée
- [ ] Sauvegarde créée (backup)
- [ ] Nouvelle méthode `recommend_build()` copiée
- [ ] 8 méthodes helper ajoutées
- [ ] Indentation vérifiée
- [ ] Fichier sauvegardé
- [ ] Syntaxe testée (`py_compile`)
- [ ] Application testée
- [ ] Endpoint testé
- [ ] Recommandations reçues

---

## 📝 Exemple de structure finale

```python
class AIRecommender:
    """Système de recommandation avec toutes les données avancées"""

    def __init__(self, api, stats_manager, champion_manager, items_db):
        # ... code existant ...

    def score_item_for_composition(self, ...):
        # ... code existant ...

    def analyze_enemy_composition(self, ...):
        # ... code existant ...

    def recommend_champion(self, ...):
        # ... code existant ...

    def recommend_build(self, my_champion, enemy_champions, live_game=None, my_team_id=None):
        # ✅ NOUVELLE MÉTHODE AMÉLIORÉE
        # ... code du patch ...

    def _select_mythic_item(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _select_boots(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _select_core_items(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _select_defensive_items(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _select_anti_heal(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _select_situational_items(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _generate_priority_sequence(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def _adapt_build_to_live_game(self, ...):
        # ✅ NOUVELLE MÉTHODE HELPER
        # ... code du patch ...

    def recommend_runes_and_spells(self, ...):
        # ... code existant ...

    def _should_build_anti_heal(self, ...):
        # ... code existant ...
```

---

## 🎯 Résultat attendu

Après intégration, vos recommandations devraient ressembler à :

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
      "stats": {"ad": 55, "ah": 20, "hp": 300},
      "passives": ["ad", "ah", "cleave"],
      "reasons": ["Ton WR: 62.5% (8g)", "+55 AD", "+20% AH", "Pénétration"]
    }
  ],
  "priority_sequence": [
    {"step": 1, "item": "Stridebreaker", "reason": "Mythique optimal", "type": "mythic"},
    {"step": 2, "item": "Mercury's Treads", "reason": "CC heavy + 3 AP", "type": "boots"},
    {"step": 3, "item": "Black Cleaver", "reason": "Core: Ton WR: 62.5%, +55 AD", "type": "core"}
  ]
}
```

---

## 💡 Conseils

1. **Testez progressivement** : Testez après chaque ajout
2. **Gardez une sauvegarde** : Avant de modifier, créez une copie
3. **Utilisez un bon éditeur** : VS Code, PyCharm, etc. pour l'indentation
4. **Lisez les erreurs** : Elles vous indiqueront où est le problème
5. **Consultez le patch** : Si vous êtes bloqué, relisez `ai_recommender_improved.py`

---

## 📞 Support

Si vous avez des problèmes :

1. Vérifiez l'indentation (très important en Python!)
2. Vérifiez que toutes les méthodes sont présentes
3. Testez la syntaxe avec `python -m py_compile lol_coach.py`
4. Consultez les fichiers de documentation
5. Vérifiez que vous avez au moins 2 games avec le champion

---

## ✨ Conclusion

Une fois intégrées, ces améliorations transformeront votre système de recommandation en un outil **professionnel et intelligent** qui propose des builds **adaptées, justifiées et optimales**!
