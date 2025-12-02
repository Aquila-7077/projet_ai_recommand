# LoL Coach AI - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Python (if not already installed)
Download from: https://www.python.org/downloads/

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Your Account
Edit `config.py`:
```python
API_KEY = "your-riot-api-key"  # Get from: https://developer.riotgames.com/
SUMMONER_NAME = "YourSummonerName"
TAG_LINE = "YourTag"  # e.g., "NA1"
REGION = "na1"
REGION_ACCOUNT = "americas"
```

### Step 4: Choose Your Interface

**Option A: Terminal (Original)**
```bash
python lol_coach.py
```

**Option B: Web Interface (New!) 🌐**
```bash
python app.py
```
Then open: http://localhost:5000

---

## 📱 Mobile Access (Same WiFi)

1. Find your PC's IP:
   - Windows: `ipconfig` → look for IPv4 Address
   - Mac/Linux: `ifconfig` → look for inet

2. On mobile browser: `http://<your-ip>:5000`
   - Example: `http://192.168.1.100:5000`

---

## 🎮 Features

### Terminal Interface
- Full menu-driven experience
- Champion analysis
- Live game detection  
- Build recommendations
- Statistics tracking

### Web Interface
- Beautiful responsive design
- Real-time live game overlay
- Mobile-friendly
- Live recommendations updates
- Champion picker suggestions

---

## 📊 First Use

1. **Sync your games** (takes 2-5 min first time)
   - Terminal: Select option 1
   - Web: Click "Sync Stats"

2. **View recommendations**
   - Terminal: Select option 4, enter enemies
   - Web: Type enemy champions, click recommend

3. **View your stats**
   - Terminal: Select option 2 or 3
   - Web: Click "Load Champions"

---

## 🔧 Troubleshooting

### "API Key Invalid"
- Check config.py
- Get a fresh key from: https://developer.riotgames.com/
- Keys expire after 24 hours

### "Summoner not found"
- Check spelling and tag are correct
- Use exact capitalization

### Port 5000 in use (Web UI)
```bash
python app.py --port 5001
```

### Can't connect from mobile
- Ensure same WiFi network
- Check firewall isn't blocking port 5000
- Try IP address directly, not localhost

---

## 📈 What You'll Get

✅ **Personalized builds** - Based on YOUR win rates, not global meta  
✅ **Intelligent scoring** - Items scored vs enemy composition  
✅ **Rune/Spell recommendations** - Optimized for your playstyle  
✅ **Live game detection** - Get champ select suggestions automatically  
✅ **Win rate predictions** - Know your likely outcomes  
✅ **Detailed explanations** - Understand WHY each item is recommended  

---

## 📚 More Info

- **Features guide**: Read `README.md`
- **Web UI guide**: Read `README_WEB.md`
- **API documentation**: See `API_DOCS.md` (if exists)

---

## 💡 Tips

- First sync takes longest (analyzes all your games)
- Subsequent syncs only fetch new games
- Recommendations improve as you play more games
- Minimum 3 games required for reliable item recommendations
- Live game overlay updates every 5 seconds

---

## ⚠️ Important Notes

- This tool is **NOT** a replacement for learning the game
- Recommendations are based on your personal stats
- Meta changes! Adapt recommendations based on current patch
- Have fun and improve! 🎮

---

## Need Help?

1. Check `README.md` for full documentation
2. Check `README_WEB.md` if using web interface
3. Verify your API key and config.py
4. Make sure you've synced at least once

Enjoy! 🎮✨
