"""
API Flask pour LoL Coach AI - Permet d'accéder aux recommandations via HTTP
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from lol_coach import (
    LoLCoachAI, RiotAPI, AdvancedStatsManager, ItemsDatabase,
    RuneDatabase, SpellDatabase, AIRecommender, ChampionManager
)
from config import API_KEY, SUMMONER_NAME, TAG_LINE, REGION, REGION_ACCOUNT
import json
import os
import requests

app = Flask(__name__)
CORS(app)  # Allow requests from anywhere (for mobile/web access)

# Global instances
coach_ai = None
api_error = None

def init_coach():
    """Initialize the coach AI system"""
    global coach_ai, api_error
    if coach_ai is None:
        try:
            coach_ai = LoLCoachAI()
            coach_ai.connect()
            api_error = None
        except Exception as e:
            api_error = str(e)
            print(f"\n[!] Erreur lors de la connexion API Riot: {e}")
            print("[!] Certaines fonctionnalites seront limitees")
            print("[!] Verifiez votre cle API dans config.py")
            return None
    return coach_ai
# =========================
# Helpers LCU / Live Client
# =========================

def get_live_data():
    """
    Lit le Live Client Data (port 2999).
    Renvoie le JSON complet si disponible, sinon None.
    """
    try:
        r = requests.get("http://127.0.0.1:2999/liveclientdata/allgamedata", timeout=1)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def adjust_build(build, my_data, enemy_data):
    """
    Adapte une build initiale selon le feed / items ennemis.
    - build: liste (strings / ids dépend de ton recommender)
    - my_data: dict du joueur local (LiveClient player dict)
    - enemy_data: liste de dicts (LiveClient player dicts)
    Retourne une nouvelle liste représentant la build adaptée.
    """

    # defensive copy
    new_build = list(build) if build else []

    # Safety: normaliser noms d'items si présents sous forme dict
    def item_name(it):
        if not it:
            return ""
        if isinstance(it, dict):
            return (it.get("displayName") or it.get("name") or "").lower()
        return str(it).lower()

    # --- 1) Anti-heal detection (si ennemis ont beaucoup de sustain/omnivamp/heal items) ---
    for e in enemy_data:
        for it in e.get("items", []) or []:
            nm = item_name(it)
            if any(k in nm for k in ("vamp", "ravenous", "ravenous", "blood", "heal", "death")):
                if not any("mortal" in str(b).lower() or "morello" in str(b).lower() for b in new_build):
                    new_build.append("Mortal Reminder")
                break

    # --- 2) Armor stacking detection (si ennemis ont items d'armure) ---
    armor_indicators = ("chain", "platemail", "thornmail", "guardian", "armor", "randuin")
    for e in enemy_data:
        for it in e.get("items", []) or []:
            nm = item_name(it)
            if any(k in nm for k in armor_indicators):
                if not any("dominik" in str(b).lower() or "lord dominik" in str(b).lower() for b in new_build):
                    new_build.append("Lord Dominik's Regards")
                break

    # --- 3) Si tu meurs souvent (feed) -> prioriser défensif ---
    deaths = my_data.get("deaths") if my_data else None
    try:
        if deaths is None:
            deaths = my_data.get("death") if my_data else 0
    except Exception:
        deaths = 0

    if deaths is None:
        deaths = 0

    if int(deaths) >= 4:
        if not any("guardian angel" in str(b).lower() for b in new_build):
            # mettre un item défensif en tête si possible
            new_build.insert(0, "Guardian Angel")

    # --- 4) Si low gold vs build attendue -> proposer options moins chères (simple heuristique) ---
    # (ici on ne manipule pas d'IDs précis, juste logique de démonstration)
    try:
        my_gold = int(my_data.get("totalGold", 0) if my_data else 0)
    except Exception:
        my_gold = 0

    # si trop peu d'or pour la build complète, on essaye de remplacer le dernier item par un item cheap
    if new_build and my_gold < 1000:
        # heuristique : si le dernier item est couteux, propose un objet plus cheap en placeholder
        cheap_placeholder = "Tear of the Goddess"  # remplace par une logique plus fine si besoin
        if len(new_build) >= 1 and "tear" not in str(new_build[-1]).lower():
            # append cheap option si pas déjà présent
            if cheap_placeholder not in new_build:
                new_build.append(cheap_placeholder)

    # Dé-dup (sauf si l'ordre est important) — on maintient la première occurrence
    seen = set()
    deduped = []
    for it in new_build:
        k = str(it).lower()
        if k not in seen:
            deduped.append(it)
            seen.add(k)

    return deduped

# ═════════════════════════════════════════════════════════════════════════════
# STATUS & INFO ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/status', methods=['GET'])
def status():
    """Check if API is running and connected"""
    global api_error
    
    if api_error:
        return jsonify({
            "status": "error",
            "error": api_error,
            "message": "Cle API Riot invalide ou expirée. Verifie config.py"
        }), 500
    
    try:
        coach = init_coach()
        if coach is None:
            return jsonify({
                "status": "error",
                "error": api_error or "Impossible de se connecter"
            }), 500
        
        return jsonify({
            "status": "ok",
            "summoner": coach.summoner_name,
            "puuid": coach.puuid[:10] + "..." if coach.puuid else None,
            "games_analyzed": len(coach.stats.stats.get("analyzed_matches", []))
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de diagnostic - Verifie l'etat du serveur et de l'API"""
    import socket
    
    def get_network_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    global api_error
    network_ip = get_network_ip()
    
    health_check = {
        "server": "ok",
        "flask": "running",
        "access_urls": {
            "pc": "http://localhost:5000",
            "mobile": f"http://{network_ip}:5000"
        },
        "api_connected": api_error is None,
        "api_error": api_error
    }
    
    if api_error:
        health_check["server"] = "warning"
    else:
        # If coach is initialized, add LCU / lockfile diagnostics
        try:
            coach = init_coach()
            if coach and hasattr(coach, 'api'):
                api = coach.api
                health_check['lcu'] = {
                    'lcu_detected': getattr(api, 'lcu_detected', False),
                    'lockfile_path': getattr(api, 'lcu_lockfile_path', None),
                    'liveclient_available': getattr(api, 'liveclient_available', False),
                    'lcu_error': getattr(api, 'lcu_error', None)
                }
        except Exception:
            pass
    
    return jsonify(health_check)

# ═════════════════════════════════════════════════════════════════════════════
# GAMEFLOW (Queue / Lobby / ReadyCheck / ChampSelect / InProgress)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/gameflow', methods=['GET'])
def gameflow():
    """Retourne l'état actuel du client LoL (Matchmaking, ChampSelect, InProgress...)"""
    coach = init_coach()
    try:
        # utilise lcu_request existant sur ton objet api
        phase = coach.api.lcu_request("GET", "/lol-gameflow/v1/gameflow-phase")
        return jsonify({"phase": phase})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/lcu-debug', methods=['GET'])
def lcu_debug():
    """Return detailed LCU diagnostics and try additional common lockfile locations."""
    try:
        coach = init_coach()
        api = coach.api if coach else None
    except Exception:
        api = None

    result = {
        'api_present': coach is not None,
        'lcu_detected': getattr(api, 'lcu_detected', False) if api else False,
        'lockfile_path': getattr(api, 'lcu_lockfile_path', None) if api else None,
        'liveclient_available': getattr(api, 'liveclient_available', False) if api else False,
        'lcu_error': getattr(api, 'lcu_error', None) if api else None,
        'additional_checks': []
    }

    # Extra common locations to probe
    additional_paths = [
        os.path.join(os.getenv('LOCALAPPDATA', ''), 'Riot Games', 'Riot Client', 'lockfile'),
        os.path.join(os.getenv('PROGRAMFILES', ''), 'Riot Games', 'Riot Client', 'lockfile'),
        os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Riot Games', 'Riot Client', 'lockfile'),
        #os.path.join('C:\', 'Riot Games', 'League of Legends', 'lockfile'),
    ]

    for p in additional_paths:
        try:
            if p and os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as fh:
                    content = fh.read().strip()
                result['additional_checks'].append({'path': p, 'exists': True, 'content': content})
            else:
                result['additional_checks'].append({'path': p, 'exists': False})
        except Exception as e:
            result['additional_checks'].append({'path': p, 'exists': False, 'error': str(e)})

    # Also check environment override
    env_lock = os.getenv('LCU_LOCKFILE')
    result['env_lockfile'] = env_lock
    if env_lock:
        try:
            if os.path.exists(env_lock):
                with open(env_lock, 'r', encoding='utf-8') as fh:
                    content = fh.read().strip()
                result['env_lockfile_content'] = content
            else:
                result['env_lockfile_content'] = None
        except Exception as e:
            result['env_lockfile_error'] = str(e)

    # For any discovered lockfile content, try to parse and call the champ-select endpoint
    def try_champ_select(port, password):
        entry = {'port': port, 'tested': False}
        try:
            url = f"https://127.0.0.1:{port}/lol-champ-select/v1/session"
            # Basic auth riot:password
            try:
                resp = requests.get(url, auth=('riot', password), verify=False, timeout=2)
                entry['tested'] = True
                entry['status_code'] = resp.status_code
                try:
                    entry['body'] = resp.json()
                except Exception:
                    entry['body'] = resp.text[:1000]
            except Exception as e:
                entry['error'] = str(e)
        except Exception as e:
            entry['error'] = str(e)
        return entry

    result['champ_select_tests'] = []
    # collect all lockfile-like contents from additional_checks + env
    candidates = []
    for c in result.get('additional_checks', []):
        if c.get('exists') and c.get('content'):
            candidates.append({'path': c.get('path'), 'content': c.get('content')})
    if result.get('env_lockfile_content'):
        candidates.append({'path': env_lock, 'content': result.get('env_lockfile_content')})
    if getattr(api, 'lcu_lockfile_path', None):
        # try the path already detected by the coach
        try:
            p = api.lcu_lockfile_path
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as fh:
                    content = fh.read().strip()
                candidates.append({'path': p, 'content': content})
        except Exception:
            pass

    for cand in candidates:
        content = cand.get('content')
        parts = content.split(':') if content else []
        if len(parts) >= 4:
            port = parts[2]
            password = parts[3]
            test = try_champ_select(port, password)
            test['lockfile_path'] = cand.get('path')
            result['champ_select_tests'].append(test)

    # Test Live Client Data (port 2999)
    try:
        lcd = {'tested': False}
        try:
            resp = requests.get('http://127.0.0.1:2999/liveclientdata/allgamedata', timeout=1)
            lcd['tested'] = True
            lcd['status_code'] = resp.status_code
            try:
                lcd['body_keys'] = list(resp.json().keys())
            except Exception:
                lcd['body'] = resp.text[:1000]
        except Exception as e:
            lcd['error'] = str(e)
        result['liveclient_test'] = lcd
    except Exception:
        result['liveclient_test'] = {'error': 'unexpected'}

    return jsonify(result)

@app.route('/api/stats/global', methods=['GET'])
def global_stats():
    """Get global player statistics"""
    try:
        coach = init_coach()
        if coach is None:
            return jsonify({"error": api_error or "API non connectée"}), 500
        stats = coach.stats.get_global_stats()
        if not stats:
            return jsonify({"error": "No stats yet"}), 404
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# CHAMPION RECOMMENDATIONS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/recommend/champions', methods=['POST'])
def recommend_champions():
    """
    Recommend champions based on enemy composition
    POST body: {
        "enemies": ["Champion1", "Champion2", ...],
        "allies": ["Ally1", "Ally2", ...] (optional)
    }
    """
    try:
        data = request.json
        enemies = data.get('enemies', [])
        allies = data.get('allies', [])
        
        if not enemies:
            return jsonify({"error": "No enemies provided"}), 400
        
        coach = init_coach()
        recommendations = coach.recommender.recommend_champion(enemies, allies)
        
        return jsonify({
            "recommendations": recommendations,
            "count": len(recommendations)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# BUILD RECOMMENDATIONS (ITEMS + RUNES + SPELLS)
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/recommend/build/<champion>', methods=['POST'])
def recommend_build(champion):
    """
    Recommend build (items, runes, spells) for a champion vs enemy composition
    POST body: {
        "enemies": ["Enemy1", "Enemy2", ...]
    }
    """
    try:
        data = request.json
        enemies = data.get('enemies', [])
        
        if not enemies:
            return jsonify({"error": "No enemies provided"}), 400
        
        coach = init_coach()
        
        # Get build recommendations
        build = coach.recommender.recommend_build(champion, enemies)
        
        # Get rune/spell recommendations
        rune_spells = coach.recommender.recommend_runes_and_spells(champion, enemies)
        
        return jsonify({
            "champion": champion,
            "build": build,
            "runes_spells": rune_spells
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# CHAMPION STATS & HISTORY
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/champion/<champion_name>', methods=['GET'])
def champion_details(champion_name):
    """Get detailed stats for a champion"""
    try:
        coach = init_coach()
        
        champions_stats = coach.stats.stats.get("champions", {})
        
        # Find champion (case-insensitive)
        champ_key = None
        for key in champions_stats:
            if key.lower() == champion_name.lower():
                champ_key = key
                break
        
        if not champ_key:
            return jsonify({"error": f"Champion {champion_name} not found"}), 404
        
        champ_stats = champions_stats[champ_key]
        games = champ_stats.get('games', 0)
        wins = champ_stats.get('wins', 0)
        wr = (wins / games * 100) if games > 0 else 0
        
        # Get builds
        builds = coach.stats.get_best_builds(champ_key, min_games=1)
        
        # Get playstyle
        playstyle = coach.stats.get_playstyle_analysis(champ_key)
        
        return jsonify({
            "champion": champ_key,
            "games": games,
            "wins": wins,
            "winrate": round(wr, 1),
            "kda": round((champ_stats.get('kills', 0) + champ_stats.get('assists', 0)) / max(champ_stats.get('deaths', 1), 1), 2),
            "builds": builds,
            "playstyle": playstyle,
            "matchups": champ_stats.get('matchups', {})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/champions', methods=['GET'])
def all_champions():
    """Get list of all played champions with basic stats"""
    try:
        coach = init_coach()
        champions_stats = coach.stats.stats.get("champions", {})
        
        result = []
        for champ, stats in champions_stats.items():
            games = stats.get('games', 0)
            if games > 0:
                wins = stats.get('wins', 0)
                result.append({
                    "name": champ,
                    "games": games,
                    "wins": wins,
                    "winrate": round((wins / games * 100), 1)
                })
        
        result.sort(key=lambda x: x['winrate'], reverse=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# LIVE GAME DETECTION
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/live-game', methods=['GET'])
def live_game():
    """Check if player is in a live game and get recommendations"""
    try:
        coach = init_coach()
        
        game = coach.api.get_current_game(coach.puuid)

        if not game:
            return jsonify({"ingame": False})

        # If we returned a local phase (champ_select / in_game) from LCU,
        # prefer that structured response.
        phase = game.get('phase')

        # Champ select via LCU (our get_local_champ_select returns my_team/enemy_team lists)
        if phase == 'champ_select':
            return jsonify({
                "ingame": True,
                "phase": "champ_select",
                "my_team": game.get('my_team', []),
                "enemy_team": game.get('enemy_team', []),
                "is_ranked": game.get('is_ranked', False),
                "recommendations": game.get('recommendations', [])
            })

        # In-game via Live Client Data
        if phase == 'in_game' and game.get('participants'):
            participants = game.get('participants')

            # Try to find local player and build team lists
            my_team = []
            enemy_team = []
            my_champion = None
            my_team_id = None

            summ_name = coach.summoner_name
            for p in participants:
                # p may contain 'name' and 'champion' directly (from liveclient)
                name = p.get('name')
                champ = p.get('champion') or p.get('championName')
                team_id = p.get('teamId') or p.get('team')

                if name and summ_name and name.lower() == summ_name.lower():
                    my_team_id = team_id
                    my_champion = champ

            for p in participants:
                champ = p.get('champion') or p.get('championName')
                team_id = p.get('teamId') or p.get('team')
                if team_id == my_team_id:
                    if champ and champ != my_champion:
                        my_team.append(champ)
                else:
                    if champ:
                        enemy_team.append(champ)

            if my_champion:
                # Pass live_game and my_team_id to recommender so it can adapt
                build_reco = coach.recommender.recommend_build(my_champion, enemy_team, live_game=game, my_team_id=my_team_id)
                rune_spell_reco = coach.recommender.recommend_runes_and_spells(my_champion, enemy_team)

                return jsonify({
                    "ingame": True,
                    "phase": "in_game",
                    "my_champion": my_champion,
                    "my_team": my_team,
                    "enemy_team": enemy_team,
                    "game_time_seconds": game.get('gameTime', 0),
                    "build": build_reco,
                    "runes_spells": rune_spell_reco
                })
            else:
                return jsonify({
                    "ingame": True,
                    "phase": "in_game",
                    "error": "Could not find your champion in live data"
                })

        # Fallback: spectator / Riot API response handling (existing behavior)
        queue_id = game.get("gameQueueConfigId", 0)
        game_length = game.get("gameLength", 0)
        is_ranked = queue_id in [420, 440]

        my_team = []
        enemy_team = []
        my_champion = None
        my_team_id = None

        for p in game.get("participants", []):
            champ_name = coach.api.get_champion_name(p.get("championId"))

            if p.get("puuid") == coach.puuid:
                my_team_id = p.get("teamId")
                my_champion = champ_name

        for p in game.get("participants", []):
            champ_name = coach.api.get_champion_name(p.get("championId"))
            if p.get("teamId") == my_team_id:
                if champ_name != my_champion:
                    my_team.append(champ_name)
            else:
                enemy_team.append(champ_name)

        is_champ_select = game_length == 0

        if is_champ_select:
            # Get recommendations for champion select
            recommendations = coach.recommender.recommend_champion(
                enemy_team,
                my_team
            )

            return jsonify({
                "ingame": True,
                "phase": "champ_select",
                "my_team": my_team,
                "enemy_team": enemy_team,
                "is_ranked": is_ranked,
                "recommendations": recommendations[:5]  # Top 5
            })

        else:
            # In-game: get live recommendations
            if my_champion:
                build_reco = coach.recommender.recommend_build(my_champion, enemy_team)
                rune_spell_reco = coach.recommender.recommend_runes_and_spells(my_champion, enemy_team)

                return jsonify({
                    "ingame": True,
                    "phase": "in_game",
                    "my_champion": my_champion,
                    "my_team": my_team,
                    "enemy_team": enemy_team,
                    "game_time_seconds": game_length,
                    "build": build_reco,
                    "runes_spells": rune_spell_reco
                })
            else:
                return jsonify({
                    "ingame": True,
                    "phase": "in_game",
                    "error": "Could not find your champion in game"
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# SYNC & DATA MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/sync', methods=['POST'])
def sync_stats():
    """Sync latest games"""
    try:
        data = request.json or {}
        count = data.get('count', 30)
        
        coach = init_coach()
        analyzed = coach.sync_stats(count)
        
        return jsonify({
            "status": "synced",
            "games_analyzed": analyzed,
            "total_games": len(coach.stats.stats.get("analyzed_matches", []))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# SERVE STATIC FILES
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve the web UI"""
    return send_file('static/index.html')

if __name__ == '__main__':
    import socket
    import os
    
    def get_network_ip():
        """Detecte l'adresse IP du reseau connecte (WiFi/Ethernet)"""
        try:
            # Methode 1: Connexion a Google DNS (pas d'envoi reel)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                # Methode 2: Utiliser le hostname
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except Exception:
                # Fallback
                return "127.0.0.1"
    
    network_ip = get_network_ip()
    
    print("\n" + "="*70)
    print(" "*15 + "LoL Coach AI - API Server")
    print("="*70)
    print()
    print("[PC] Acces depuis cet ordinateur:")
    print("     -> http://localhost:5000")
    print()
    print("[Mobile/Autre PC] Acces sur le meme reseau WiFi/Ethernet:")
    print(f"     -> http://{network_ip}:5000")
    print()
    print("Utilisation sur Telephone/Tablette:")
    print(f"     1. Connecte-toi au meme WiFi que ce PC")
    print(f"     2. Ouvre ton navigateur")
    print(f"     3. Tape l'adresse: http://{network_ip}:5000")
    print()
    print("="*70)
    print("[*] Serveur en cours de demarrage...")
    print("="*70)
    print()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[*] Serveur arrete (CTRL+C)")
        exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n[!] Erreur: Le port 5000 est deja utilise")
            print("[!] Essaie de fermer l'autre instance ou change le port")
        else:
            print(f"\n[!] Erreur au demarrage: {e}")
        exit(1)
    except Exception as e:
        print(f"\n[!] Erreur inattendue: {e}")
        exit(1)
