# 🚀 LoL Coach AI - Lancement & Utilisation

## ⚡ Démarrage Rapide

### 1️⃣ Interface Terminale (Classique)
```bash
python lol_coach.py
```
- Menu interactif
- Analyse détaillée par champion
- Recommandations build
- Détection live game
- Statistiques complètes

### 2️⃣ Interface Web (Nouveau!) 🌐
```bash
python app.py
```
- Puis ouvre: **http://localhost:5000**
- Responsive design
- Mobile-friendly
- Real-time live game overlay
- Plus facile à utiliser

---

## 📱 Accès Mobile

### Sur le même WiFi:
1. Trouve l'IP de ton PC:
   - **Windows**: Ouvre `Invite de commandes` → tape `ipconfig` → cherche `Adresse IPv4`
   - **Mac**: Terminal → `ifconfig` → cherche `inet`
   - **Linux**: Terminal → `ifconfig`

2. Sur ton téléphone:
   ```
   http://192.168.1.X:5000
   ```
   (Remplace X par ton IP)

3. Voilà! Accès complet depuis ton téléphone 📲

---

## 🎮 Workflow Typique

### Première Utilisation
1. **Synchronise tes stats** (2-5 minutes première fois)
   - Terminal: Option 1 → Entre 30 (ou plus)
   - Web: Clique "Synchroniser Stats"

2. **Attends** que toutes tes games soient analysées

3. C'est bon! Tu as maintenant tes stats personnalisées 📊

### Utilisation Courante
1. **Avant une game**:
   - Entre les 5 champions ennemis
   - Reçois build + runes + spells personnalisés
   - Lis les explications

2. **Pendant le champ select**:
   - Web UI détecte automatiquement
   - Affiche recommendations en direct
   - Updates toutes les 5 secondes

3. **En game**:
   - Web UI affiche items à acheter
   - Montre vs quel ennemi
   - Explique pourquoi chaque item

---

## 📊 Que Contient Chaque Recommendation?

### Items
```
• Kraken Slayer: 75pts ⭐
  └─ Ton WR: 55.2% (12g), +AD, Crit vs 2 AD enemies [HIGH]
```
- Score combiné (60% WR perso + 40% fit composition)
- Ton win rate personnel avec cet item
- Nombre de games (plus = plus fiable)
- Raisons concrètes (stats, passifs, vs menaces)

### Runes & Spells
```
🔮 Keystone: ID XXXX (60.1% WR)
📞 Spells: 4 / 12 (Flash + Teleport)
```
- Basé sur TES meilleures runes historiquement
- Avec ton win rate personnel
- Recommandé spécifiquement pour ton playstyle

### Reliability Tags
```
[RELIABLE] = 30+ games → très fiable
[HIGH] = 10-29 games → fiable
[MEDIUM] = 5-9 games → acceptable
[LOW] = 0-4 games → données limitées
```
- Plus le tag est haut, plus la recommandation est fiable

---

## 🔧 Menus Disponibles

### Terminal Interface
```
MENU PRINCIPAL
1. 📊 Synchroniser mes stats
2. 🏆 Voir statistiques globales
3. 🔍 Analyse détaillée d'un champion
4. 🎯 Recommandations de pick
5. 🔴 Détection game en cours
6. 🔄 Rafraîchir mes champions
7. 🗑️ Reset mes stats
0. ❌ Quitter
```

### Web Interface
- Dashboard automatique
- Sync button
- Build recommendation form
- Champions gallery
- Live game overlay
- Mobile accessible

---

## 💡 Tips & Tricks

### ⚡ Optimisation
- **Première sync est lente** (charge tout)
- **Syncs suivantes rapides** (seulement nouvelles games)
- **Attend au moins 3 games** pour que les runes soient bonnes
- **Plus de games = meilleures recommandations**

### 🎯 Utilisation Optimale
1. **Joue minimum 3 games** avec un champion
2. **Sync tes stats**
3. **Obtiens recommandations perso** basées sur TON style
4. **Adapte selon le match** (parfois ignore la meta)
5. **Continue à jouer** et améliore tes stats

### 🚀 Pour Pros
- Web API accessible: `curl http://localhost:5000/api/status`
- Données en JSON
- Facile à intégrer avec OBS/Stream deck
- Peut être déployé sur cloud

---

## ❌ Troubleshooting

### "Impossible de se connecter à l'API Riot"
```
1. Vérifie config.py
2. Reçois une nouvelle API key: https://developer.riotgames.com/
3. Les keys expirent après 24h
```

### "Pas assez de données"
```
1. Sync au moins 30 games
2. Joue le champion quelques fois
3. Attends que les données s'accumulent
```

### "Port 5000 déjà utilisé"
```bash
python app.py --port 5001
# Puis accède à http://localhost:5001
```

### "Pas de live game détecté"
```
1. Lance le jeu (en champ select ou en game)
2. Assure-toi d'être sur le bon compte
3. Attendsaprès quelques secondes
4. Recharge la page web
```

### "Erreur sur mobile - pas de connexion"
```
1. Vérifiez que vous êtes sur le même WiFi
2. Essaye l'IP directe (pas localhost)
3. Désactive le VPN si actif
4. Vérifie le pare-feu
```

---

## 📈 Limitations Connues

⚠️ **À Savoir:**
- Min 3 games requises par item/rune pour être recommendation
- Bayesian smoothing utilisé pour petits échantillons
- Meta change rapidement (vérifie le patch)
- Certains items très niche peuvent manquer d'historique
- Runes trop récentes sans beaucoup de données

✅ **C'est normal et attendu!**

---

## 🎓 Comment Ça Marche en Détail?

### Recommandation d'Items
```
Score = (WR_personnel * 0.6) + (Fit_composition * 0.4)

Où:
- WR_personnel = Ton win rate avec cet item (Bayesian lissé)
- Fit_composition = Score basé sur:
  - Stats de l'item (AD, AP, Armor, MR)
  - Passifs (anti-heal, pen, mobility, etc.)
  - Vs ennemis (tanks? healers? AP? AD?)
```

### Recommandation de Runes
```
Best_rune = argmax(WR_personnel[rune_id] for rune_id if games >= 2)

- Trie toutes tes runes par win rate
- Filtre celles avec 2+ games minimum
- Recommande la meilleure
```

### Recommendation de Spells
```
Priorités:
1. Flash (pour 99% des cas)
2. Champion-spécifique secondaire:
   - Support: Leona, Nautilus, etc. → TP ou Ignite
   - ADC: Jinx, Ashe, etc. → Heal
   - Jungler: Lee Sin, Elise, etc. → Smite
   - etc.
```

---

## 🌟 Utilisation Avancée

### Intégration OBS (Streaming)
```bash
# L'API Flask peut être utilisée pour afficher:
# - Items actuels
# - Build recommendation
# - Win rate vs composition ennemie
# - Live game timer
```

### Discord Bot (À venir)
```
/coach champion <name> <enemies>
# Retourne recommendation dans Discord
```

### Cloud Deployment (À venir)
```bash
# Deploy sur Heroku/Railway/Replit
# Accessible depuis n'importe où
```

---

## 📞 Support

Si tu as des questions:
1. Relis `README.md` (documentation complète)
2. Relis `README_WEB.md` (web interface)
3. Relis `QUICK_START.md` (démarrage rapide)
4. Vérifie `config.py` est bien configuré
5. Fais un sync complet

---

## 🎉 Enjoy!

Tu as maintenant:
✅ Recommendations personnalisées basées sur TES stats  
✅ Interface web beautiful et responsive  
✅ Accès mobile via WiFi  
✅ Runes & spells intelligents  
✅ Live game detection  
✅ Explications mathématiques pour chaque choix  

**Bon courage et bonne chance en ranked! 🎮✨**

P.S. Plus tu joues, meilleures sont les recommendations!
