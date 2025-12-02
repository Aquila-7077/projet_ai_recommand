# LoL Coach AI - Web Interface Guide

## Installation & Setup

### 1. Install Flask dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Access the Web UI

**On your computer (same machine):**
- Open browser: `http://localhost:5000`

**On your mobile phone (same WiFi network):**
1. Find your computer's IP address:
   - Windows: `ipconfig` in command prompt, look for "IPv4 Address"
   - Mac/Linux: `ifconfig` in terminal, look for "inet"
   
2. On mobile phone, open: `http://<your-computer-ip>:5000`
   - Example: `http://192.168.1.100:5000`

**Important:** Your phone must be on the **same WiFi network** as your computer.

---

## Features

### 📊 Live Game Detection
- Automatically detects when you're in champ select or in-game
- Shows real-time recommendations
- Updates every 5 seconds

### 🔨 Build Recommendations
- Enter enemy champions
- Get personalized build recommendations based on **your stats**
- Shows items, runes, spells with win rates
- Explains **why** each item is recommended

### 🏆 Champion Statistics
- View all your played champions
- See win rates and game counts
- Detailed stats per champion

### 📝 Sync Stats
- Manually sync your last 30 games
- Updates win rates and build data

---

## API Endpoints

All endpoints are available at `http://localhost:5000/api/`

### Status
- `GET /api/status` - Check connection status
- `GET /api/stats/global` - Get global player stats

### Champions
- `GET /api/champions` - List all played champions
- `GET /api/champion/<name>` - Get detailed stats for a champion
- `POST /api/recommend/champions` - Recommend champions vs enemy comp
  - Body: `{"enemies": ["Champ1", ...], "allies": ["Ally1", ...]}`

### Builds
- `POST /api/recommend/build/<champion>` - Get full build recommendation
  - Body: `{"enemies": ["Enemy1", ...]}`

### Live Game
- `GET /api/live-game` - Check if in-game and get recommendations

### Sync
- `POST /api/sync` - Sync latest games
  - Body: `{"count": 30}`

---

## Troubleshooting

### Can't connect from phone?
1. Check both devices are on **same WiFi**
2. Check firewall isn't blocking port 5000
3. Make sure server is running (`python app.py`)
4. Try the IP address format: `http://192.168.x.x:5000`

### API returns error?
1. Make sure you've synced stats first (click "Sync Stats")
2. Check your `config.py` is correct
3. Check your Riot API key hasn't expired

### Port 5000 already in use?
```bash
# Kill process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :5000
kill -9 <PID>
```

---

## Mobile Optimization

The web UI is fully responsive and optimized for mobile:
- Touch-friendly buttons
- Mobile-sized cards
- Fast loading
- Works on any modern browser

---

## Advanced: Running on Cloud/Remote Server

To access from anywhere (not just local network):

### Option 1: Ngrok Tunnel (Free, temporary)
```bash
pip install ngrok
python -c "from pyngrok import ngrok; print(ngrok.connect(5000))"
```

### Option 2: Heroku/Railway/Replit
Deploy `app.py` to a cloud platform and it becomes accessible worldwide.

### Option 3: Your own domain (Advanced)
Use a reverse proxy like Caddy or nginx to expose locally.

---

## Performance Tips

- First sync takes longer (loads all your games)
- Subsequent syncs only fetch new games
- Live game detection runs every 5 seconds
- Cache is stored locally in `data/` folder

---

## Security Notes

- API is **not** password protected (runs on local network only)
- Your API key stays in `config.py` (never sent to browser)
- Data is stored locally on your computer
