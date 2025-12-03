"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗      ██████╗ ██╗          ██████╗ ██████╗  █████╗  ██████╗██╗  ██╗      ║
║   ██║     ██╔═══██╗██║         ██╔════╝██╔═══██╗██╔══██╗██╔════╝██║  ██║      ║
║   ██║     ██║   ██║██║         ██║     ██║   ██║███████║██║     ███████║      ║
║   ██║     ██║   ██║██║         ██║     ██║   ██║██╔══██║██║     ██╔══██║      ║
║   ███████╗╚██████╔╝███████╗    ╚██████╗╚██████╔╝██║  ██║╚██████╗██║  ██║      ║
║   ╚══════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝      ║
║                                                                               ║
║                   🤖 AI COACH - Version 4.0 ADVANCED 🤖                      ║
║                                                                               ║
║  ✨ FONCTIONNALITÉS:                                                         ║
║     • Tracking builds avec WR par item                                        ║
║     • Analyse Early/Mid/Late game                                             ║
║     • Synergies avec alliés                                                   ║
║     • Tendances récentes                                                      ║
║     • Prédiction de victoire                                                  ║
║     • Protection anti-doublons                                                ║
║     • Cache intelligent + sync parallèle                                      ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import requests
import urllib3
import base64
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
import os  # Pour les chemins de fichiers
import re  # Pour les expressions régulières
import time  # Pour le sleep (délai de retentative)
import psutil # Pour la recherche de processus (le fix principal)
# Assure-toi que tu importes bien LCU_LOCKFILE de config.py
from config import LCU_LOCKFILE

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Import config (use getattr to allow optional values)
try:
    import config as cfg
    API_KEY = getattr(cfg, 'API_KEY', '')
    SUMMONER_NAME = getattr(cfg, 'SUMMONER_NAME', '')
    TAG_LINE = getattr(cfg, 'TAG_LINE', '')
    REGION = getattr(cfg, 'REGION', 'euw1')
    REGION_ACCOUNT = getattr(cfg, 'REGION_ACCOUNT', 'europe')
    LCU_LOCKFILE = getattr(cfg, 'LCU_LOCKFILE', '')
except ImportError:
    print("❌ ERREUR: Fichier config.py non trouvé!")
    print("   Crée config.py avec: API_KEY, SUMMONER_NAME, TAG_LINE, REGION, REGION_ACCOUNT")
    sys.exit(1)

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                              CONSTANTES                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

DATA_DIR = "data"
STATS_FILE = "data/my_stats.json"
CHAMPIONS_CACHE = "data/champions_cache.json"
MY_CHAMPIONS_FILE = "data/my_champions.json"
MATCHES_CACHE = "data/matches_cache.json"
ITEMS_DATA = "data/items_cache.json"
GLOBAL_ITEM_STATS = "data/global_item_stats.json"

# When combining your personal stats with global item stats, this weight controls
# how much global stats influence your recommendations (0.0 = ignore global,
# 1.0 = treat global as equally weighted). Tweak as desired.
GLOBAL_ITEM_WEIGHT = 0.2

# Set True to print fuzzy-match debug info
DEBUG_NAME_MATCH = False

DDRAGON_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
DDRAGON_CHAMPIONS_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/champion.json"
DDRAGON_ITEMS_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR/item.json"
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                         GESTIONNAIRE D'ITEMS                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class ItemsDatabase:
    """Gère la base de données des items"""
    
    # Items mythiques/légendaires importants (IDs)
    MYTHIC_ITEMS = {
        6655: "Luden's Companion",
        6653: "Liandry's Torment", 
        6656: "Everfrost",
        6657: "Rod of Ages",
        3078: "Trinity Force",
        6631: "Stridebreaker",
        6630: "Goredrinker",
        6632: "Divine Sunderer",
        3190: "Locket of the Iron Solari",
        6662: "Iceborn Gauntlet",
        6664: "Hollow Radiance",
        6665: "Jak'Sho",
        6667: "Radiant Virtue",
        3084: "Heartsteel",
        6673: "Immortal Shieldbow",
        6672: "Kraken Slayer",
        6671: "Galeforce",
        6675: "Navori Quickblades",
        6676: "The Collector",
        6691: "Duskblade",
        6692: "Eclipse",
        6693: "Prowler's Claw",
        4005: "Imperial Mandate",
        4633: "Riftmaker",
        6620: "Echoes of Helia",
        6617: "Moonstone Renewer",
        6621: "Dawncore",
    }
    
    # Items anti-heal
    ANTIHEAL_ITEMS = {
        3123: "Executioner's Calling",
        3033: "Mortal Reminder",
        3076: "Bramble Vest",
        3075: "Thornmail",
        3165: "Morellonomicon",
        3011: "Chemtech Putrifier",
        6609: "Chempunk Chainsword",
    }
    
    # Items défensifs
    ARMOR_ITEMS = {
        3047: "Plated Steelcaps",
        3075: "Thornmail",
        3143: "Randuin's Omen",
        3110: "Frozen Heart",
        3742: "Dead Man's Plate",
        3157: "Zhonya's Hourglass",
    }
    
    MR_ITEMS = {
        3111: "Mercury's Treads",
        3194: "Adaptive Helm",
        3065: "Spirit Visage",
        4401: "Force of Nature",
        3102: "Banshee's Veil",
        3156: "Maw of Malmortius",
    }
    
    def __init__(self):
        self.items = {}
        self.items_by_name = {}
        self.global_item_stats = {}
        self.load_items()
        self.load_global_item_stats()

    def load_global_item_stats(self):
        """Charge des statistiques globales d'items depuis un fichier JSON optionnel.

        Format attendu: {"<item_id>": {"games": int, "wins": int}, ...}
        """
        if os.path.exists(GLOBAL_ITEM_STATS):
            try:
                with open(GLOBAL_ITEM_STATS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # normalize keys to int
                    self.global_item_stats = {int(k): v for k, v in data.items()}
                    return
            except Exception:
                self.global_item_stats = {}
        else:
            self.global_item_stats = {}
    
    def load_items(self):
        """Charge les items depuis Data Dragon"""
        if os.path.exists(ITEMS_DATA):
            try:
                with open(ITEMS_DATA, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    cache_date = datetime.fromisoformat(cache.get("updated", "2020-01-01"))
                    if datetime.now() - cache_date < timedelta(days=7):
                        self.items = {int(k): v for k, v in cache.get("items", {}).items()}
                        self.items_by_name = cache.get("items_by_name", {})
                        return
            except:
                pass
        
        print("📥 Téléchargement de la base d'items...")
        try:
            versions = requests.get(DDRAGON_VERSION_URL).json()
            version = versions[0]
            
            url = DDRAGON_ITEMS_URL.format(version=version)
            response = requests.get(url)
            data = response.json()
            
            for item_id, item_data in data.get("data", {}).items():
                self.items[int(item_id)] = {
                    "name": item_data["name"],
                    "tags": item_data.get("tags", []),
                    "stats": item_data.get("stats", {}),
                    "gold": item_data.get("gold", {}),
                    "description": item_data.get("plaintext", "")
                }
                self.items_by_name[item_data["name"]] = self.items[int(item_id)]
            
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(ITEMS_DATA, 'w', encoding='utf-8') as f:
                json.dump({
                    "items": {str(k): v for k, v in self.items.items()},
                    "items_by_name": self.items_by_name,
                    "updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ {len(self.items)} items chargés!")
        except Exception as e:
            print(f"   ⚠️ Erreur chargement items: {e}")
    
    def get_item_name(self, item_id):
        """Retourne le nom d'un item"""
        if item_id in self.items:
            return self.items[item_id].get("name", f"Item_{item_id}")
        return f"Item_{item_id}"
    
    def get_item_stats(self, item_id):
        """Retourne les stats d'un item"""
        return self.items.get(int(item_id), {}).get("stats", {})
    
    def is_mythic(self, item_id):
        """Vérifie si c'est un mythique"""
        return item_id in self.MYTHIC_ITEMS
    
    def is_antiheal(self, item_id):
        """Vérifie si c'est un item anti-heal"""
        return item_id in self.ANTIHEAL_ITEMS
    
    def is_armor_item(self, item_id):
        """Vérifie si un item donne de l'armure"""
        stats = self.get_item_stats(item_id)
        return stats.get("FlatArmorMod", 0) > 0 or item_id in self.ARMOR_ITEMS
    
    def is_mr_item(self, item_id):
        """Vérifie si un item donne de la MR"""
        stats = self.get_item_stats(item_id)
        return stats.get("FlatSpellBlockMod", 0) > 0 or item_id in self.MR_ITEMS
    
    def is_completed_item(self, item_id):
        """Vérifie si c'est un item complet (pas composant)"""
        item = self.items.get(item_id, {})
        gold = item.get("gold", {})
        return gold.get("total", 0) >= 2500

    def extract_item_stats(self, item_id):
        """Extract numeric stats from item (AD, AP, Armor, MR, AH, etc.)"""
        item = self.items.get(int(item_id), {})
        stats = item.get("stats", {})
        result = {
            "ad": float(stats.get("FlatPhysicalDamageMod", 0) or 0),
            "ap": float(stats.get("FlatMagicDamageMod", 0) or 0),
            "armor": float(stats.get("FlatArmorMod", 0) or 0),
            "mr": float(stats.get("FlatSpellBlockMod", 0) or 0),
            "hp": float(stats.get("FlatHPPoolMod", 0) or 0),
            "ah": float(stats.get("FlatCDRMod", 0) or 0) * 100,  # Convert to %
            "crit": float(stats.get("FlatCritChanceMod", 0) or 0) * 100,
            "as": float(stats.get("PercentAttackSpeedMod", 0) or 0) * 100,
            "ms": float(stats.get("FlatMovementSpeedMod", 0) or 0),
        }
        return result

    def get_item_passives(self, item_id):
        """Return passive/active abilities of an item as a list of tags"""
        # Manual classification of key items and their passives
        item_passives = {
            6672: ["pen", "crit"],  # Kraken Slayer
            6671: ["mobility"],  # Galeforce
            6673: ["shield", "lifesteal"],  # Immortal Shieldbow
            6675: ["crit", "ah"],  # Navori Quickblades
            6676: ["execut"],  # The Collector
            6691: ["ad", "lethality"],  # Duskblade
            6692: ["ad", "armor_pen"],  # Eclipse
            6693: ["lethality", "mobility"],  # Prowler's Claw
            3165: ["ap", "antiheal"],  # Morellonomicon
            3033: ["ad", "antiheal"],  # Mortal Reminder
            3157: ["ap", "survival"],  # Zhonya's Hourglass
            3156: ["mr", "mr_pen"],  # Maw of Malmortius
            3102: ["mr"],  # Banshee's Veil
            3075: ["armor", "antiheal"],  # Thornmail
            3047: ["armor"],  # Plated Steelcaps
            3111: ["mr"],  # Mercury's Treads
            3110: ["armor", "ah"],  # Frozen Heart
            3143: ["armor", "slow"],  # Randuin's Omen
            3190: ["support", "shield"],  # Locket
            3078: ["ad", "ah", "cleave"],  # Trinity Force
            6631: ["ad", "ah", "mobility"],  # Stridebreaker
            6630: ["ad", "lifesteal", "health"],  # Goredrinker
            6632: ["ad", "armor_pen"],  # Divine Sunderer
            3084: ["health", "armor", "mr"],  # Heartsteel
            6655: ["ap", "pen"],  # Luden's Companion
            6653: ["ap", "antiheal"],  # Liandry's Torment
            6656: ["ap", "cc"],  # Everfrost
        }
        return item_passives.get(int(item_id), [])
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                            API RIOT OPTIMISÉE                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class RiotAPI:
    """API Riot avec cache et rate limiting intelligent"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"X-Riot-Token": api_key}
        self.ddragon_version = None
        self.all_champions = {}
        self.champions_data = {}
        self.matches_cache = {}
        self.last_request_time = 0
        self.min_request_interval = 1.2
        # LCU diagnostics
        self.lcu_lockfile_path = None
        self.lcu_error = None
        self.lcu_detected = False
        self.liveclient_available = False
        # NOUVEAU: Variables LCU
        self.lcu_port = None
        self.lcu_token = None
        self.lcu_connected = False
        self.load_matches_cache()
        # NOUVEAU: Détection LCU au démarrage
        self._detect_lcu()
    
    def _rate_limit(self):
        """Gère le rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def load_matches_cache(self):
        """Charge le cache des matchs"""
        if os.path.exists(MATCHES_CACHE):
            try:
                with open(MATCHES_CACHE, 'r', encoding='utf-8') as f:
                    self.matches_cache = json.load(f)
            except:
                self.matches_cache = {}
    
    def save_matches_cache(self):
        """Sauvegarde le cache"""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MATCHES_CACHE, 'w', encoding='utf-8') as f:
            json.dump(self.matches_cache, f)
    def _detect_lcu(self):
        """Détecte et configure la connexion LCU au démarrage"""
        print("\n🔍 Détection LCU...")
        
        # 1. Vérifier si League est en cours d'exécution
        league_running = False
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in ['LeagueClient.exe', 'LeagueClientUx.exe']:
                    league_running = True
                    print(f"   ✅ Processus League détecté: {proc.info['name']}")
                    break
        except ImportError:
            print("   ⚠️ psutil non installé, impossible de vérifier les processus")
        except Exception as e:
            print(f"   ⚠️ Erreur vérification processus: {e}")
        
        if not league_running:
            print("   ⚪ League Client n'est pas lancé")
            return False
        
        # 2. Chercher le lockfile
        possible_paths = [
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Riot Games', 'League of Legends', 'lockfile'),
            os.path.join(os.getenv('PROGRAMFILES', ''), 'Riot Games', 'League of Legends', 'lockfile'),
            os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Riot Games', 'League of Legends', 'lockfile'),
        ]
        
        # Ajouter le chemin de config si défini
        if LCU_LOCKFILE:
            possible_paths.insert(0, LCU_LOCKFILE)
        
        # 3. Essayer de trouver via le processus (méthode avancée)
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'exe']):
                if proc.info['name'] in ['LeagueClient.exe', 'LeagueClientUx.exe']:
                    try:
                        exe_path = proc.info.get('exe')
                        if exe_path:
                            # Le lockfile est dans le même dossier que LeagueClient.exe
                            league_dir = os.path.dirname(exe_path)
                            lockfile_path = os.path.join(league_dir, 'lockfile')
                            if lockfile_path not in possible_paths:
                                possible_paths.insert(0, lockfile_path)
                                print(f"   📂 Chemin détecté: {league_dir}")
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
        except:
            pass
        
        # 4. Tentatives de lecture avec retry
        print(f"   🔄 Recherche du lockfile dans {len(possible_paths)} emplacements...")
        
        for attempt in range(3):  # 3 tentatives
            for path in possible_paths:
                if not path:
                    continue
                
                # Afficher le chemin testé (pour debug)
                if attempt == 0:
                    print(f"   📍 Test: {path}")
                
                if not os.path.exists(path):
                    if attempt == 0:
                        print(f"      ❌ Fichier inexistant")
                    continue
                
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content:
                        if attempt == 0:
                            print(f"      ⚠️ Fichier vide")
                        continue
                    
                    # Format: name:pid:port:password:protocol
                    parts = content.split(':')
                    if len(parts) < 5:
                        if attempt == 0:
                            print(f"      ⚠️ Format invalide: {len(parts)} parties")
                        continue
                    
                    self.lcu_port = parts[2]
                    self.lcu_token = parts[3]
                    self.lcu_lockfile_path = path
                    
                    # Test de connexion
                    print(f"   🔌 Test de connexion sur port {self.lcu_port}...")
                    if self._test_lcu_connection():
                        self.lcu_connected = True
                        print(f"   ✅ LCU connecté! (port {self.lcu_port})")
                        return True
                    else:
                        if attempt == 0:
                            print(f"      ❌ Connexion échouée")
                        
                except PermissionError:
                    if attempt == 0:
                        print(f"      ❌ Permission refusée")
                except Exception as e:
                    if attempt == 0:
                        print(f"      ❌ Erreur: {e}")
            
            # Attendre entre les tentatives
            if attempt < 2 and league_running:
                print(f"   ⏳ Nouvelle tentative dans 2 secondes...")
                time.sleep(2)
        
        # Si on arrive ici, la détection a échoué
        if league_running:
            print("   ⚠️ League est lancé mais le LCU n'est pas accessible")
            print("   💡 Causes possibles:")
            print("      • Mise à jour en cours (attends qu'elle se termine)")
            print("      • Client pas encore complètement démarré")
            print("      • Problème de permissions")
            print("\n   🔄 Le système réessayera automatiquement plus tard")
        else:
            print("   ⚪ LCU non détecté (League n'est pas lancé)")
        
        return False
    
    def _test_lcu_connection(self):
        """Test si la connexion LCU fonctionne"""
        if not self.lcu_port or not self.lcu_token:
            return False
        
        try:
            url = f"https://127.0.0.1:{self.lcu_port}/lol-summoner/v1/current-summoner"
            response = requests.get(
                url,
                auth=('riot', self.lcu_token),
                verify=False,
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def lcu_request(self, method, endpoint, data=None):
        """Effectue une requête vers le LCU avec retry automatique"""
        # Retry si LCU n'était pas détecté au démarrage
        if not self.lcu_connected:
            print("   🔄 LCU non connecté, nouvelle tentative de détection...")
            self._detect_lcu()
        
        if not self.lcu_connected:
            # Message plus informatif
            print("   ❌ LCU toujours inaccessible")
            return None
        
        url = f"https://127.0.0.1:{self.lcu_port}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(
                    url,
                    auth=('riot', self.lcu_token),
                    verify=False,
                    timeout=3
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    auth=('riot', self.lcu_token),
                    json=data,
                    verify=False,
                    timeout=3
                )
            else:
                raise ValueError(f"Méthode {method} non supportée")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"⚠️ LCU erreur {response.status_code}: {endpoint}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout LCU: {endpoint}")
            return None
        except Exception as e:
            print(f"❌ Erreur LCU: {e}")
            return None
            
    def _request(self, url):
        """Requête avec gestion d'erreurs"""
        self._rate_limit()
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("⏳ Rate limit, attente 10s...")
                time.sleep(10)
                return self._request(url)
            elif response.status_code == 401:
                print("❌ Clé API invalide!")
                return None
            elif response.status_code == 404:
                return None
            else:
                return None
        except Exception as e:
            return None
    
    def _request_no_auth(self, url):
        """Requête sans auth (Data Dragon)"""
        try:
            response = requests.get(url)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def load_all_champions(self):
        """Charge tous les champions"""
        print("📥 Chargement des champions...")
        
        versions = self._request_no_auth(DDRAGON_VERSION_URL)
        self.ddragon_version = versions[0] if versions else "14.10.1"
        
        url = DDRAGON_CHAMPIONS_URL.format(version=self.ddragon_version)
        data = self._request_no_auth(url)
        
        if data and "data" in data:
            for champ_name, champ_data in data["data"].items():
                champ_id = int(champ_data["key"])
                self.all_champions[champ_id] = champ_name
                self.champions_data[champ_name] = {
                    "id": champ_id,
                    "name": champ_data["name"],
                    "key": champ_name,
                    "tags": champ_data["tags"],
                    "info": champ_data["info"],
                }
            print(f"   ✅ {len(self.all_champions)} champions chargés!")
            self._save_champions_cache()
        else:
            self._load_champions_cache()
    
    def _save_champions_cache(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CHAMPIONS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "version": self.ddragon_version,
                "champions": self.all_champions,
                "champions_data": self.champions_data,
            }, f, ensure_ascii=False, indent=2)
    
    def _load_champions_cache(self):
        if os.path.exists(CHAMPIONS_CACHE):
            with open(CHAMPIONS_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                self.all_champions = {int(k): v for k, v in cache["champions"].items()}
                self.champions_data = cache["champions_data"]
    
    def get_champion_name(self, champion_id):
        """Retourne le nom d'un champion avec protection contre None"""
        if champion_id is None or champion_id == 0:
            return None
        try:
            return self.all_champions.get(int(champion_id), f"Champion_{champion_id}")
        except (ValueError, TypeError):
            return None
    
    def get_account(self, game_name, tag_line):
        url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return self._request(url)
    
    def get_summoner_by_puuid(self, puuid):
        url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._request(url)
    
    def get_match_history(self, puuid, count=50):
        url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        result = self._request(url)
        return result if result else []
    
    def get_match_details(self, match_id, use_cache=True):
        if use_cache and match_id in self.matches_cache:
            return self.matches_cache[match_id]
        
        url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        data = self._request(url)
        
        if data and use_cache:
            self.matches_cache[match_id] = data
        
        return data
    
    def get_current_game(self, puuid):
        """
        Détecte la partie en cours (champion select ou in-game)
        ORDRE: 1. LCU Champ Select, 2. Live Client API, 3. Spectator API
        """
        
        print("\n🔍 Recherche de partie en cours...")
        
        # 1. CHAMPION SELECT (via LCU)
        try:
            champ_select = self.get_local_champ_select()
            if champ_select:
                print("✅ Champion Select détecté (LCU)")
                return champ_select
        except Exception as e:
            print(f"⚠️ Champ select check: {e}")
        
        # 2. IN-GAME (via Live Client API port 2999)
        try:
            in_game = self.get_local_in_game()
            if in_game:
                print("✅ Partie en cours détectée (Live Client)")
                return in_game
        except Exception as e:
            print(f"⚠️ Live client check: {e}")
        
        # 3. SPECTATOR API (fallback)
        try:
            url = f"https://{REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
            data = self._request(url)
            
            if data:
                print("✅ Partie détectée (Spectator API)")
                return self._parse_spectator_game(data, puuid)
        except Exception as e:
            print(f"⚠️ Spectator API check: {e}")
        
        print("⚪ Aucune partie détectée")
        return None
    
    def _parse_spectator_game(self, game, puuid):
        """Parse les données de l'API Spectator"""
        my_team = []
        enemy_team = []
        my_champion = None
        my_team_id = None
        
        # Trouver le joueur
        for p in game.get("participants", []):
            champ_name = self.api.get_champion_name(p.get("championId"))
            
            if p.get("puuid") == self.puuid:
                my_team_id = p.get("teamId")
                my_champion = champ_name
        
        for p in game.get("participants", []):
            champ_name = self.api.get_champion_name(p.get("championId"))
            # Ignorer les champions None (pas encore sélectionnés)
            if champ_name:
                if p.get("teamId") == my_team_id:
                    if champ_name != my_champion:
                        my_team.append(champ_name)
                else:
                    enemy_team.append(champ_name)
        
        game_length = game.get("gameLength", 0)
        is_champ_select = game_length == 0
        
        return {
            'ingame': True,
            'phase': 'champ_select' if is_champ_select else 'in_game',
            'my_champion': my_champion,
            'my_team': my_team,
            'enemy_team': enemy_team,
            'game_time_seconds': game_length,
            'is_ranked': game.get("gameQueueConfigId") in [420, 440]
        }

    def get_local_champ_select(self):
        """Détecte le champion select via LCU"""
        try:
            session = self.lcu_request("GET", "/lol-champ-select/v1/session")
            
            if not session:
                return None
            
            print("🎪 Champion Select détecté!")
            
            my_team = []
            enemy_team = []
            
            # Parser myTeam
            for cell in session.get('myTeam', []):
                champ_id = cell.get('championId', 0)
                if champ_id > 0:
                    champ_name = self.get_champion_name(champ_id)
                    my_team.append(champ_name)
            
            # Parser theirTeam
            for cell in session.get('theirTeam', []):
                champ_id = cell.get('championId', 0)
                if champ_id > 0:
                    champ_name = self.get_champion_name(champ_id)
                    enemy_team.append(champ_name)
            
            return {
                'ingame': True,
                'phase': 'champ_select',
                'my_team': my_team,
                'enemy_team': enemy_team,
                'is_ranked': False,
                'raw_session': session
            }
            
        except Exception as e:
            print(f"⚠️ Erreur champ select: {e}")
            return None

    def get_local_in_game(self):
        """Détecte la partie en cours via Live Client API (port 2999)"""
        try:
            url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
            response = requests.get(url, verify=False, timeout=2)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            print("🎮 Partie en cours détectée!")
            
            my_team = []
            enemy_team = []
            my_champion = None
            my_team_id = None
            
            # Récupérer le nom du joueur local
            try:
                player_data = requests.get(
                    "https://127.0.0.1:2999/liveclientdata/activeplayername",
                    verify=False,
                    timeout=1
                ).text.strip().strip('"')
            except:
                player_data = None
            
            participants = []
            
            for player in data.get('allPlayers', []):
                summ_name = player.get('summonerName', '')
                champ_name = player.get('championName', '')
                team = player.get('team', '')
                
                # Identifier le joueur local
                if player_data and summ_name.lower() == player_data.lower():
                    my_team_id = team
                    my_champion = champ_name
                
                # Parser items
                items = []
                for item in player.get('items', []):
                    item_id = item.get('itemID', 0)
                    if item_id > 0:
                        items.append(item_id)
                
                # Construire participant
                p = {
                    'name': summ_name,
                    'champion': champ_name,
                    'championName': champ_name,
                    'team': team,
                    'teamId': 100 if team == 'ORDER' else 200,
                    'items': items,
                    'kills': player.get('scores', {}).get('kills', 0),
                    'deaths': player.get('scores', {}).get('deaths', 0),
                    'assists': player.get('scores', {}).get('assists', 0),
                    'goldEarned': player.get('currentGold', 0),
                }
                
                # Ajouter items individuels pour compatibilité
                for i in range(6):
                    p[f'item{i}'] = items[i] if i < len(items) else 0
                
                participants.append(p)
            
            # Séparer les équipes
            for p in participants:
                if my_team_id and p['team'] == my_team_id:
                    if p['champion'] != my_champion:
                        my_team.append(p['champion'])
                else:
                    enemy_team.append(p['champion'])
            
            # Récupérer le temps de jeu
            game_time = data.get('gameData', {}).get('gameTime', 0)
            
            return {
                'ingame': True,
                'phase': 'in_game',
                'my_champion': my_champion,
                'my_team': my_team,
                'enemy_team': enemy_team,
                'participants': participants,
                'gameTime': game_time,
                'game_time_seconds': int(game_time),
                'raw_liveclient': data
            }
            
        except requests.exceptions.ConnectionError:
            # Normal si pas en jeu
            return None
        except Exception as e:
            print(f"⚠️ Erreur live client: {e}")
            return None
    
    def get_champion_mastery(self, puuid):
        url = f"https://{REGION}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        return self._request(url)
    
    def get_free_rotation(self):
        url = f"https://{REGION}.api.riotgames.com/lol/platform/v3/champion-rotations"
        return self._request(url)
        # ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                         GESTION DES CHAMPIONS                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class ChampionManager:
    """Gère les champions disponibles"""
    
    def __init__(self, api):
        self.api = api
        self.owned_champions = set()
        self.free_rotation = set()
        self.mastery_data = {}
    
    def load_my_champions(self, puuid):
        print("\n📥 Chargement de tes champions...")
        
        rotation = self.api.get_free_rotation()
        if rotation:
            self.free_rotation = set(rotation.get("freeChampionIds", []))
            print(f"   ✅ Rotation: {len(self.free_rotation)} champions")
        
        mastery = self.api.get_champion_mastery(puuid)
        if mastery:
            for champ in mastery:
                champ_id = champ["championId"]
                self.owned_champions.add(champ_id)
                self.mastery_data[champ_id] = {
                    "level": champ["championLevel"],
                    "points": champ["championPoints"],
                }
            print(f"   ✅ Champions joués: {len(self.owned_champions)}")
        
        self._save()
    
    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MY_CHAMPIONS_FILE, 'w') as f:
            json.dump({
                "owned": list(self.owned_champions),
                "free_rotation": list(self.free_rotation),
                "mastery": {str(k): v for k, v in self.mastery_data.items()},
            }, f, indent=2)
    
    def get_available_champions(self):
        return self.owned_champions.union(self.free_rotation)
    
    def get_mastery_level(self, champion_id):
        return self.mastery_data.get(champion_id, {}).get("level", 0)


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    BASE DE DONNÉES RUNES                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class RuneDatabase:
    """Gère la base de données des runes et leurs efficacités"""
    
    # Runes principales par path
    RUNE_PATHS = {
        8000: "Precision",      # Conquéror, Lethal Tempo, etc.
        8100: "Domination",     # Dark Harvest, Electrocute, etc.
        8200: "Sorcery",        # Phase Rush, Aery, etc.
        8400: "Resolve",        # Grasp, Aftershock, etc.
        8300: "Inspiration"     # Glacial, Unsealed Spellbook, etc.
    }
    
    RUNE_STATS = {
        # Precision
        8005: {"name": "Conquéror", "path": 8000},
        8008: {"name": "Présence d'Esprit", "path": 8000},
        8021: {"name": "Légendaire: Alacrité", "path": 8000},
        8009: {"name": "Leçon de sang", "path": 8000},
        
        # Domination
        8112: {"name": "Dark Harvest", "path": 8100},
        8124: {"name": "Prédateur", "path": 8100},
        8128: {"name": "Coup assuré", "path": 8100},
        8134: {"name": "Trésor chasseur", "path": 8100},
        
        # Sorcery
        8214: {"name": "Tempête de rassemblement", "path": 8200},
        8229: {"name": "Moisson", "path": 8200},
        8230: {"name": "Arpenteur", "path": 8200},
        8237: {"name": "Brûlure", "path": 8200},
        
        # Resolve
        8437: {"name": "Poigne de l'immortel", "path": 8400},
        8439: {"name": "Coup de tonnerre", "path": 8400},
        8465: {"name": "Conditionnement", "path": 8400},
        8473: {"name": "Second souffle", "path": 8400},
        
        # Inspiration
        8326: {"name": "Cantrip glacial", "path": 8300},
        8347: {"name": "Carnet d'enchantement", "path": 8300},
        8359: {"name": "Quincaille cosmique", "path": 8300},
        8369: {"name": "Chaussée de Pierre", "path": 8300}
    }
    
    def __init__(self):
        self.rune_stats = self.RUNE_STATS.copy()
    
    def get_rune_name(self, rune_id):
        return self.rune_stats.get(rune_id, {}).get("name", f"Rune {rune_id}")
    
    def get_rune_path(self, rune_id):
        return self.rune_stats.get(rune_id, {}).get("path", 0)


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    BASE DE DONNÉES SPELLS (SUMMONERS)                          ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    BASE DE DONNÉES BUILDS                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class BuildDatabase:
    """Base de données des builds et runes"""
    
    ROLE_MAPPING = {
        "Assassin": "assassin",
        "Fighter": "fighter",
        "Mage": "mage",
        "Marksman": "adc",
        "Support": "support",
        "Tank": "tank"
    }
    
    HEALING_CHAMPIONS = [
        "Aatrox", "Soraka", "Yuumi", "Nami", "Sona", "Vladimir", "Sylas",
        "Warwick", "DrMundo", "Maokai", "Swain", "Fiddlesticks", "Illaoi",
        "Kayn", "Olaf", "Renekton", "Trundle", "Volibear", "Zac", "Senna",
        "Seraphine", "Briar", "Nilah"
    ]
    
    CC_HEAVY_CHAMPIONS = [
        "Leona", "Nautilus", "Thresh", "Morgana", "Sejuani", "Amumu",
        "Malzahar", "Lissandra", "Ashe", "Varus", "Rell", "Alistar",
        "Braum", "TahmKench", "Zac", "Ornn", "Sion", "Maokai", "Rammus"
    ]
    
    ENGAGE_CHAMPIONS = [
        "Malphite", "Zac", "Ornn", "JarvanIV", "Hecarim", "Rakan",
        "Alistar", "Leona", "Rell", "Diana", "Galio", "Sion", "Amumu"
    ]
    
    @classmethod
    def get_champion_damage_type(cls, champion_data):
        if not champion_data:
            return "ad"
        info = champion_data.get("info", {})
        return "ap" if info.get("magic", 0) > info.get("attack", 0) else "ad"
    
    @classmethod
    def get_champion_class(cls, champion_data):
        if not champion_data:
            return "fighter"
        tags = champion_data.get("tags", [])
        if tags:
            return cls.ROLE_MAPPING.get(tags[0], "fighter")
        return "fighter"


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    BASE DE DONNÉES RUNES                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class RuneDatabase:
    """Gère la base de données des runes (noms officiels Riot API)"""
    
    RUNE_STATS = {
        # Precision (8000) - Keystones et runes secondaires
        8005: {"name": "Conqueror", "path": 8000},
        8008: {"name": "Presence of Mind", "path": 8000},
        8009: {"name": "Legend: Alacrity", "path": 8000},
        8010: {"name": "Lethal Tempo", "path": 8000},
        8012: {"name": "Triumph", "path": 8000},
        8014: {"name": "Legend: Tenacity", "path": 8000},
        8017: {"name": "Legend: Bloodline", "path": 8000},
        8021: {"name": "Coup de Grace", "path": 8000},
        
        # Domination (8100)
        8112: {"name": "Dark Harvest", "path": 8100},
        8124: {"name": "Predator", "path": 8100},
        8128: {"name": "Cheap Shot", "path": 8100},
        8134: {"name": "Treasure Hunter", "path": 8100},
        8135: {"name": "Sudden Impact", "path": 8100},
        8136: {"name": "Eyeball Collection", "path": 8100},
        8138: {"name": "Relentless Hunter", "path": 8100},
        8139: {"name": "Ultimate Hunter", "path": 8100},
        
        # Sorcery (8200)
        8210: {"name": "Phase Rush", "path": 8200},
        8213: {"name": "Aery", "path": 8200},
        8214: {"name": "Summon Aery", "path": 8200},
        8224: {"name": "Manaflow Band", "path": 8200},
        8226: {"name": "Celerity", "path": 8200},
        8229: {"name": "Gathering Storm", "path": 8200},
        8230: {"name": "Waterwalking", "path": 8200},
        8237: {"name": "Absolute Focus", "path": 8200},
        
        # Resolve (8400)
        8401: {"name": "Guardian", "path": 8400},
        8410: {"name": "Demolish", "path": 8400},
        8429: {"name": "Overgrowth", "path": 8400},
        8430: {"name": "Revitalize", "path": 8400},
        8437: {"name": "Grasp of the Undying", "path": 8400},
        8439: {"name": "Aftershock", "path": 8400},
        8465: {"name": "Conditioning", "path": 8400},
        8473: {"name": "Second Wind", "path": 8400},
        
        # Inspiration (8300)
        8312: {"name": "Magical Footwear", "path": 8300},
        8321: {"name": "Perfect Timing", "path": 8300},
        8326: {"name": "Glacial Augment", "path": 8300},
        8347: {"name": "Unsealed Spellbook", "path": 8300},
        8359: {"name": "Cosmic Insight", "path": 8300},
        8369: {"name": "Hextech Flashtraption", "path": 8300}
    }
    
    def __init__(self):
        self.rune_stats = self.RUNE_STATS.copy()
    
    def get_rune_name(self, rune_id):
        return self.rune_stats.get(rune_id, {}).get("name", f"Rune {rune_id}")
    
    def get_rune_path(self, rune_id):
        return self.rune_stats.get(rune_id, {}).get("path", 0)


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    BASE DE DONNÉES SPELLS (SUMMONERS)                          ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class SpellDatabase:
    """Gère la base de données des spells d'invocateur (noms officiels Riot API)"""
    
    SPELLS = {
        1: {"name": "Smite", "emoji": "🔴"},
        3: {"name": "Smite", "emoji": "🔴"},  # Official Smite
        4: {"name": "Ignite", "emoji": "🔥"},  # Official
        5: {"name": "Teleport", "emoji": "📍"},  # Alternate ID
        6: {"name": "Ghost", "emoji": "👻"},  # Official
        7: {"name": "Heal", "emoji": "💚"},  # Official
        12: {"name": "Teleport", "emoji": "📍"},  # Official
        13: {"name": "Exhaust", "emoji": "❄️"},  # Official
        14: {"name": "Clarity", "emoji": "💧"},  # Official
        21: {"name": "Barrier", "emoji": "🛡️"},  # Official
        30: {"name": "To the King!", "emoji": "👑"},
        31: {"name": "Surrender@20", "emoji": "⏹️"}
    }
    
    def __init__(self):
        self.spells = self.SPELLS.copy()
    
    def get_spell_name(self, spell_id):
        return self.spells.get(spell_id, {}).get("name", f"Spell {spell_id}")
    
    def get_spell_emoji(self, spell_id):
        return self.spells.get(spell_id, {}).get("emoji", "")


        # ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║              STATS MANAGER V4 - APPRENTISSAGE AVANCÉ ✨                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class AdvancedStatsManager:
    """
    Gestionnaire de stats avancé avec:
    - Tracking des builds
    - Analyse early/mid/late game
    - Synergies alliés
    - Tendances récentes
    - Protection anti-doublons
    """
    
    def __init__(self, items_db):
        self.items_db = items_db
        self.stats = self._load()
    
    def _get_default_stats(self):
        """Retourne la structure de stats par défaut"""
        return {
            "champions": {},
            "games_analyzed": 0,
            "wins": 0,
            "losses": 0,
            "analyzed_matches": [],
            "last_update": None,
            "builds_history": {},
            "phase_stats": {},
            "ally_synergies": {},
            "recent_games": [],
            "monthly_progress": {},
            "matchups": {}
        }
    
    def _load(self):
        """Charge les stats depuis le fichier ET ajoute les clés manquantes"""
        default = self._get_default_stats()
        
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    
                    # Fusion: Ajouter les clés manquantes
                    for key, value in default.items():
                        if key not in loaded:
                            loaded[key] = value
                    
                    return loaded
            except Exception as e:
                print(f"   ⚠️ Erreur chargement stats: {e}")
                return default
        
        return default
    
    def save(self):
        """Sauvegarde les stats"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.stats["last_update"] = datetime.now().isoformat()
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def is_match_analyzed(self, match_id):
        """Vérifie si un match a déjà été analysé"""
        return match_id in self.stats.get("analyzed_matches", [])
    
    def add_game_advanced(self, match_data, my_stats, match_id, allies, enemies, my_role):
        """Ajoute une game avec TOUTES les données avancées"""
        
        # Protection anti-doublons
        if self.is_match_analyzed(match_id):
            return False
        
        champion = my_stats["championName"]
        won = my_stats["win"]
        duration_sec = match_data["info"]["gameDuration"]
        duration_min = duration_sec / 60
        
        # 1. STATS DE BASE
        if champion not in self.stats["champions"]:
            self.stats["champions"][champion] = {
                "games": 0, "wins": 0,
                "kills": 0, "deaths": 0, "assists": 0,
                "cs": 0, "damage": 0, "vision": 0, "gold": 0,
                "total_duration": 0,
                "roles": {},
                "matchups": {}
            }
        
        c = self.stats["champions"][champion]
        c["games"] += 1
        c["wins"] += 1 if won else 0
        c["kills"] += my_stats["kills"]
        c["deaths"] += my_stats["deaths"]
        c["assists"] += my_stats["assists"]
        c["cs"] += my_stats["totalMinionsKilled"] + my_stats.get("neutralMinionsKilled", 0)
        c["damage"] += my_stats["totalDamageDealtToChampions"]
        c["vision"] += my_stats.get("visionScore", 0)
        c["gold"] += my_stats["goldEarned"]
        c["total_duration"] += duration_min
        
        if my_role:
            if my_role not in c["roles"]:
                c["roles"][my_role] = {"games": 0, "wins": 0}
            c["roles"][my_role]["games"] += 1
            c["roles"][my_role]["wins"] += 1 if won else 0
        
        enemy_laner = self._find_enemy_laner(match_data, my_stats, my_role)
        if enemy_laner:
            if enemy_laner not in c["matchups"]:
                c["matchups"][enemy_laner] = {"games": 0, "wins": 0}
            c["matchups"][enemy_laner]["games"] += 1
            c["matchups"][enemy_laner]["wins"] += 1 if won else 0
        
        self.stats["games_analyzed"] += 1
        self.stats["wins"] += 1 if won else 0
        self.stats["losses"] += 0 if won else 1
        
        # 2. TRACKING DES BUILDS
        items_bought = []
        for i in range(6):
            item_id = my_stats.get(f"item{i}", 0)
            if item_id > 0:
                items_bought.append(item_id)
        
        if champion not in self.stats["builds_history"]:
            self.stats["builds_history"][champion] = {
                "items": {},
                "first_items": {},
                "item_combos": {}
            }
        
        builds = self.stats["builds_history"][champion]
        
        for item_id in items_bought:
            if not self.items_db.is_completed_item(item_id):
                continue
            
            item_key = str(item_id)
            if item_key not in builds["items"]:
                builds["items"][item_key] = {
                    "games": 0, 
                    "wins": 0, 
                    "name": self.items_db.get_item_name(item_id)
                }
            
            builds["items"][item_key]["games"] += 1
            if won:
                builds["items"][item_key]["wins"] += 1
        
        # Premier item
        first_completed = None
        for item_id in items_bought:
            if self.items_db.is_mythic(item_id) or self.items_db.is_completed_item(item_id):
                first_completed = item_id
                break
        
        if first_completed:
            first_key = str(first_completed)
            if first_key not in builds["first_items"]:
                builds["first_items"][first_key] = {
                    "games": 0, 
                    "wins": 0,
                    "name": self.items_db.get_item_name(first_completed)
                }
            builds["first_items"][first_key]["games"] += 1
            if won:
                builds["first_items"][first_key]["wins"] += 1
        
        # Combo d'items
        completed_items = [i for i in items_bought if self.items_db.is_completed_item(i)]
        if len(completed_items) >= 2:
            combo_key = "_".join(str(i) for i in sorted(completed_items[:3]))
            if combo_key not in builds["item_combos"]:
                builds["item_combos"][combo_key] = {
                    "games": 0, 
                    "wins": 0,
                    "items": [self.items_db.get_item_name(i) for i in completed_items[:3]]
                }
            builds["item_combos"][combo_key]["games"] += 1
            if won:
                builds["item_combos"][combo_key]["wins"] += 1
        
        # TRACKING DES RUNES ET SPELLS
        if champion not in self.stats["builds_history"][champion]:
            self.stats["builds_history"][champion]["runes"] = {}
            self.stats["builds_history"][champion]["spells"] = {}
        
        # Extraire les runes (keystone + autres)
        perks = my_stats.get("perks", {})
        if perks and "selections" in perks:
            # Keystone est généralement le premier
            for i, perk_selection in enumerate(perks.get("selections", [])):
                rune_id = perk_selection.get("perk", 0)
                if rune_id > 0:
                    rune_key = str(rune_id)
                    if rune_key not in self.stats["builds_history"][champion]["runes"]:
                        self.stats["builds_history"][champion]["runes"][rune_key] = {
                            "games": 0,
                            "wins": 0,
                            "name": "Rune"
                        }
                    self.stats["builds_history"][champion]["runes"][rune_key]["games"] += 1
                    if won:
                        self.stats["builds_history"][champion]["runes"][rune_key]["wins"] += 1
        
        # Extraire les spells d'invocateur
        summoner1 = my_stats.get("summoner1Id", 0)
        summoner2 = my_stats.get("summoner2Id", 0)
        
        for spell_id in [summoner1, summoner2]:
            if spell_id > 0:
                spell_key = str(spell_id)
                if spell_key not in self.stats["builds_history"][champion]["spells"]:
                    self.stats["builds_history"][champion]["spells"][spell_key] = {
                        "games": 0,
                        "wins": 0,
                        "name": "Spell"
                    }
                self.stats["builds_history"][champion]["spells"][spell_key]["games"] += 1
                if won:
                    self.stats["builds_history"][champion]["spells"][spell_key]["wins"] += 1
        
        # 3. STATS PAR PHASE DE JEU
        if champion not in self.stats["phase_stats"]:
            self.stats["phase_stats"][champion] = {
                "early_wins": 0,
                "mid_wins": 0,
                "late_wins": 0,
                "early_games": 0,
                "mid_games": 0,
                "late_games": 0,
                "total_cs_per_min": 0,
                "total_gold_per_min": 0,
                "total_damage_share": 0,
                "games_for_avg": 0
            }
        
        ps = self.stats["phase_stats"][champion]
        
        if duration_min < 25:
            ps["early_games"] += 1
            if won:
                ps["early_wins"] += 1
        elif duration_min < 35:
            ps["mid_games"] += 1
            if won:
                ps["mid_wins"] += 1
        else:
            ps["late_games"] += 1
            if won:
                ps["late_wins"] += 1
        
        cs_per_min = (my_stats["totalMinionsKilled"] + my_stats.get("neutralMinionsKilled", 0)) / max(duration_min, 1)
        gold_per_min = my_stats["goldEarned"] / max(duration_min, 1)
        
        team_damage = sum(
            p["totalDamageDealtToChampions"] 
            for p in match_data["info"]["participants"] 
            if p["teamId"] == my_stats["teamId"]
        )
        damage_share = (my_stats["totalDamageDealtToChampions"] / team_damage * 100) if team_damage > 0 else 0
        
        n = ps.get("games_for_avg", 0)
        ps["total_cs_per_min"] = ((ps.get("total_cs_per_min", 0) * n) + cs_per_min) / (n + 1)
        ps["total_gold_per_min"] = ((ps.get("total_gold_per_min", 0) * n) + gold_per_min) / (n + 1)
        ps["total_damage_share"] = ((ps.get("total_damage_share", 0) * n) + damage_share) / (n + 1)
        ps["games_for_avg"] = n + 1
        
        # 4. SYNERGIES AVEC ALLIÉS
        for ally in allies:
            if ally == champion:
                continue
            
            synergy_key = f"{champion}+{ally}"
            
            if synergy_key not in self.stats["ally_synergies"]:
                self.stats["ally_synergies"][synergy_key] = {
                    "my_champ": champion,
                    "ally_champ": ally,
                    "games": 0,
                    "wins": 0
                }
            
            self.stats["ally_synergies"][synergy_key]["games"] += 1
            if won:
                self.stats["ally_synergies"][synergy_key]["wins"] += 1
        
        # 5. TENDANCES RÉCENTES
        kda = (my_stats["kills"] + my_stats["assists"]) / max(my_stats["deaths"], 1)
        
        recent_entry = {
            "match_id": match_id,
            "champion": champion,
            "won": won,
            "kda": round(kda, 2),
            "cs_per_min": round(cs_per_min, 1),
            "damage_share": round(damage_share, 1),
            "duration": round(duration_min, 1),
            "role": my_role,
            "date": datetime.now().isoformat(),
            "kills": my_stats["kills"],
            "deaths": my_stats["deaths"],
            "assists": my_stats["assists"]
        }
        
        self.stats["recent_games"].append(recent_entry)
        
        if len(self.stats["recent_games"]) > 100:
            self.stats["recent_games"] = self.stats["recent_games"][-100:]
        
        # 6. PROGRÈS MENSUEL
        month_key = datetime.now().strftime("%Y-%m")
        
        if month_key not in self.stats["monthly_progress"]:
            self.stats["monthly_progress"][month_key] = {
                "games": 0,
                "wins": 0,
                "champions_played": [],
                "avg_kda": 0
            }
        
        mp = self.stats["monthly_progress"][month_key]
        mp["games"] += 1
        if won:
            mp["wins"] += 1
        
        if champion not in mp["champions_played"]:
            mp["champions_played"].append(champion)
        
        n = mp["games"] - 1
        mp["avg_kda"] = ((mp.get("avg_kda", 0) * n) + kda) / mp["games"] if mp["games"] > 0 else kda
        
        # 7. MATCHUPS GLOBAUX
        for enemy in enemies:
            matchup_key = f"{champion}_vs_{enemy}"
            
            if matchup_key not in self.stats["matchups"]:
                self.stats["matchups"][matchup_key] = {
                    "my_champ": champion,
                    "enemy_champ": enemy,
                    "games": 0,
                    "wins": 0
                }
            
            self.stats["matchups"][matchup_key]["games"] += 1
            if won:
                self.stats["matchups"][matchup_key]["wins"] += 1
        
        self.stats["analyzed_matches"].append(match_id)
        
        return True
    
    def _find_enemy_laner(self, match_data, my_stats, my_role):
        """Trouve l'adversaire direct"""
        if not my_role:
            return None
        
        for p in match_data["info"]["participants"]:
            if p["teamId"] != my_stats["teamId"] and p.get("teamPosition") == my_role:
                return p["championName"]
        return None
            # Suite de la classe AdvancedStatsManager...
    def _bayesian_winrate(self, wins, games, prior_games=3, prior_rate=0.5):
        """Return smoothed winrate as percentage using a simple Bayesian prior.

        wins/games can be floats (for combined/global weighting). prior_games
        sets the strength of the prior (higher = stronger pull to prior_rate).
        """
        try:
            prior_wins = prior_games * prior_rate
            smoothed = (wins + prior_wins) / (games + prior_games) if (games + prior_games) > 0 else prior_rate
            return smoothed * 100
        except Exception:
            return prior_rate * 100

    def _reliability_tag(self, games):
        """Return reliability tag string for a given sample size."""
        if games <= 0:
            return "NONE"
        if games < 5:
            return "LOW"
        if games < 10:
            return "MEDIUM"
        if games < 30:
            return "HIGH"
        return "RELIABLE"
    
    def get_winrate(self, champion):
        """Retourne le winrate d'un champion"""
        if champion in self.stats.get("champions", {}):
            c = self.stats["champions"][champion]
            if c["games"] > 0:
                return self._bayesian_winrate(c.get("wins", 0), c.get("games", 0), prior_games=5)
        return 0
    
    def get_kda(self, champion):
        """Retourne le KDA moyen d'un champion"""
        if champion in self.stats.get("champions", {}):
            c = self.stats["champions"][champion]
            if c["games"] > 0:
                avg_k = c["kills"] / c["games"]
                avg_d = c["deaths"] / c["games"]
                avg_a = c["assists"] / c["games"]
                return (avg_k + avg_a) / max(avg_d, 1)
        return 0
    
    def get_matchup_winrate(self, my_champion, enemy_champion):
        """Retourne le WR d'un matchup spécifique"""
        key = f"{my_champion}_vs_{enemy_champion}"
        if key in self.stats.get("matchups", {}):
            m = self.stats["matchups"][key]
            if m["games"] > 0:
                return self._bayesian_winrate(m.get("wins", 0), m.get("games", 0)), m.get("games", 0)
        
        if my_champion in self.stats.get("champions", {}):
            matchups = self.stats["champions"][my_champion].get("matchups", {})
            if enemy_champion in matchups:
                m = matchups[enemy_champion]
                if m["games"] > 0:
                    return self._bayesian_winrate(m.get("wins", 0), m.get("games", 0)), m.get("games", 0)
        
        return None, 0
    
    def get_best_champions(self, min_games=2, available_champions=None):
        """Retourne les meilleurs champions triés par score"""
        result = []
        
        for champ, data in self.stats.get("champions", {}).items():
            if data["games"] < min_games:
                continue
            
            if available_champions and champ not in available_champions:
                continue
            
            wr = (data["wins"] / data["games"]) * 100
            kda = (data["kills"] + data["assists"]) / max(data["deaths"], 1) / data["games"]
            
            score = wr * 0.5 + min(kda * 10, 30) + min(data["games"] * 2, 20)
            
            result.append({
                "champion": champ,
                "games": data["games"],
                "wins": data["wins"],
                "winrate": wr,
                "kda": kda,
                "score": score,
                "roles": data.get("roles", {}),
                "matchups": data.get("matchups", {})
            })
        
        return sorted(result, key=lambda x: x["score"], reverse=True)
    
    def get_global_stats(self):
        """Stats globales"""
        total = self.stats.get("games_analyzed", 0)
        if total == 0:
            return None
        
        wins = self.stats.get("wins", 0)
        return {
            "total_games": total,
            "wins": wins,
            "losses": total - wins,
            "winrate": (wins / total) * 100
        }
    
    def get_best_builds(self, champion, min_games=2):
        """Retourne les items avec le meilleur WR pour un champion"""
        builds_history = self.stats.get("builds_history", {})
        
        if champion not in builds_history:
            return None
        
        builds = builds_history[champion]
        
        result = {
            "best_items": [],
            "worst_items": [],
            "best_first_item": None,
            "best_combo": None
        }
        
        # Meilleurs items individuels (ajoute smoothing bayésien et option global stats)
        items = []
        for item_id, data in builds.get("items", {}).items():
            user_games = data.get("games", 0)
            user_wins = data.get("wins", 0)

            # get global stats if available
            global_stats = self.items_db.global_item_stats.get(int(item_id), {}) if hasattr(self.items_db, 'global_item_stats') else {}
            global_games = global_stats.get('games', 0)
            global_wins = global_stats.get('wins', 0)

            # combine with a lightweight weight for global stats
            combined_games = user_games + (GLOBAL_ITEM_WEIGHT * global_games)
            combined_wins = user_wins + (GLOBAL_ITEM_WEIGHT * global_wins)

            # Compute smoothed winrate
            smoothed_wr = self._bayesian_winrate(combined_wins, combined_games, prior_games=3)

            reliability = self._reliability_tag(user_games)

            # Only include if meets min_games threshold (based on user's own games)
            if user_games >= min_games:
                items.append({
                    "item_id": int(item_id),
                    "name": data.get("name", self.items_db.get_item_name(int(item_id))),
                    "games": user_games,
                    "wins": user_wins,
                    "global_games": global_games,
                    "global_wins": global_wins,
                    "winrate": round(smoothed_wr, 1),
                    "reliability": reliability
                })
        
        items.sort(key=lambda x: x["winrate"], reverse=True)
        result["best_items"] = items[:5]
        result["worst_items"] = items[-3:] if len(items) >= 3 else []
        
        # Meilleur premier item (apply smoothing with optional global stats)
        first_items = []
        for item_id, data in builds.get("first_items", {}).items():
            user_games = data.get("games", 0)
            user_wins = data.get("wins", 0)

            global_stats = self.items_db.global_item_stats.get(int(item_id), {}) if hasattr(self.items_db, 'global_item_stats') else {}
            global_games = global_stats.get('games', 0)
            global_wins = global_stats.get('wins', 0)

            combined_games = user_games + (GLOBAL_ITEM_WEIGHT * global_games)
            combined_wins = user_wins + (GLOBAL_ITEM_WEIGHT * global_wins)

            smoothed_wr = self._bayesian_winrate(combined_wins, combined_games, prior_games=3)

            if user_games >= 2:
                first_items.append({
                    "item_id": int(item_id),
                    "name": data.get("name", self.items_db.get_item_name(int(item_id))),
                    "games": user_games,
                    "winrate": round(smoothed_wr, 1),
                    "reliability": self._reliability_tag(user_games)
                })
        
        if first_items:
            first_items.sort(key=lambda x: x["winrate"], reverse=True)
            result["best_first_item"] = first_items[0]
        
        # Meilleur combo
        combos = []
        for combo_key, data in builds.get("item_combos", {}).items():
            if data.get("games", 0) >= 2:
                wr = (data["wins"] / data["games"]) * 100
                combos.append({
                    "items": data.get("items", []),
                    "games": data["games"],
                    "winrate": round(wr, 1)
                })
        
        if combos:
            combos.sort(key=lambda x: x["winrate"], reverse=True)
            result["best_combo"] = combos[0]
        
        return result
    
    def get_playstyle_analysis(self, champion):
        """Analyse si tu es early/mid/late game player"""
        phase_stats = self.stats.get("phase_stats", {})
        
        if champion not in phase_stats:
            return None
        
        ps = phase_stats[champion]
        
        total_games = ps.get("early_games", 0) + ps.get("mid_games", 0) + ps.get("late_games", 0)
        if total_games < 5:
            return None
        
        early_wr = (ps.get("early_wins", 0) / ps["early_games"] * 100) if ps.get("early_games", 0) > 0 else 0
        mid_wr = (ps.get("mid_wins", 0) / ps["mid_games"] * 100) if ps.get("mid_games", 0) > 0 else 0
        late_wr = (ps.get("late_wins", 0) / ps["late_games"] * 100) if ps.get("late_games", 0) > 0 else 0
        
        best_phase = max([(early_wr, "EARLY"), (mid_wr, "MID"), (late_wr, "LATE")], key=lambda x: x[0])
        worst_phase = min([(early_wr, "EARLY"), (mid_wr, "MID"), (late_wr, "LATE")], key=lambda x: x[0])
        
        if best_phase[0] - worst_phase[0] < 10:
            playstyle = "BALANCED"
            tip = "Tu es régulier sur toutes les phases de jeu."
        elif best_phase[1] == "EARLY":
            playstyle = "EARLY GAME"
            tip = "Tu domines en early! Snowball agressivement et ferme les games vite."
        elif best_phase[1] == "MID":
            playstyle = "MID GAME"
            tip = "Tu brilles en mid-game. Focus les objectifs (Drake, Baron) entre 15-30min."
        else:
            playstyle = "LATE GAME"
            tip = "Tu scale mieux que tes adversaires. Farm safe early, évite les fights inutiles."
        
        return {
            "playstyle": playstyle,
            "early_wr": round(early_wr, 1),
            "mid_wr": round(mid_wr, 1),
            "late_wr": round(late_wr, 1),
            "early_games": ps.get("early_games", 0),
            "mid_games": ps.get("mid_games", 0),
            "late_games": ps.get("late_games", 0),
            "avg_cs_per_min": round(ps.get("total_cs_per_min", 0), 1),
            "avg_gold_per_min": round(ps.get("total_gold_per_min", 0), 0),
            "avg_damage_share": round(ps.get("total_damage_share", 0), 1),
            "tip": tip
        }
    
    def get_ally_synergies(self, my_champion, min_games=2):
        """Retourne les meilleurs/pires alliés pour un champion"""
        synergies = self.stats.get("ally_synergies", {})
        
        allies = []
        for key, data in synergies.items():
            if data.get("my_champ") == my_champion and data.get("games", 0) >= min_games:
                wr = (data["wins"] / data["games"]) * 100
                allies.append({
                    "ally": data["ally_champ"],
                    "games": data["games"],
                    "wins": data["wins"],
                    "winrate": round(wr, 1)
                })
        
        allies.sort(key=lambda x: x["winrate"], reverse=True)
        
        return {
            "best_allies": allies[:5],
            "worst_allies": allies[-3:] if len(allies) >= 3 else []
        }
    
    def get_recent_trend(self, champion=None, last_n=20):
        """Analyse les tendances récentes"""
        all_recent = self.stats.get("recent_games", [])
        
        if champion:
            recent = [g for g in all_recent if g.get("champion") == champion]
        else:
            recent = all_recent
        
        if len(recent) < 5:
            return None
        
        last_games = recent[-last_n:]
        older_games = recent[:-last_n] if len(recent) > last_n else []
        
        recent_wins = sum(1 for g in last_games if g.get("won"))
        recent_wr = (recent_wins / len(last_games)) * 100
        recent_kda = sum(g.get("kda", 0) for g in last_games) / len(last_games)
        
        if older_games:
            old_wins = sum(1 for g in older_games if g.get("won"))
            old_wr = (old_wins / len(older_games)) * 100 if older_games else 50
            trend = recent_wr - old_wr
        else:
            trend = 0
        
        last_5 = recent[-5:]
        last_5_wins = sum(1 for g in last_5 if g.get("won"))
        hot_streak = last_5_wins >= 4
        tilt_alert = last_5_wins <= 1
        
        if trend > 15:
            trend_text = "🔥 EN FEU!"
        elif trend > 5:
            trend_text = "📈 En progression"
        elif trend < -15:
            trend_text = "📉 En chute (prends une pause?)"
        elif trend < -5:
            trend_text = "📉 Légère baisse"
        else:
            trend_text = "➡️ Stable"
        
        return {
            "recent_games": len(last_games),
            "recent_wr": round(recent_wr, 1),
            "recent_kda": round(recent_kda, 2),
            "trend": round(trend, 1),
            "trend_text": trend_text,
            "hot_streak": hot_streak,
            "tilt_alert": tilt_alert,
            "last_5": f"{last_5_wins}W/{5-last_5_wins}L"
        }
    
    def get_monthly_progress(self):
        """Retourne le progrès par mois"""
        monthly = self.stats.get("monthly_progress", {})
        
        result = []
        for month, data in sorted(monthly.items(), reverse=True):
            if data.get("games", 0) > 0:
                wr = (data["wins"] / data["games"]) * 100
                result.append({
                    "month": month,
                    "games": data["games"],
                    "wins": data["wins"],
                    "winrate": round(wr, 1),
                    "avg_kda": round(data.get("avg_kda", 0), 2),
                    "champions_played": len(data.get("champions_played", []))
                })
        
        return result
    
    def predict_win_chance(self, my_champion, ally_champions, enemy_champions):
        """Prédit les chances de victoire basé sur TON historique"""
        base_score = 50
        factors = {}
        recommendations = []
        confidence_points = 0
        
        # 1. Ton WR global sur ce champion
        wr = self.get_winrate(my_champion)
        games = self.stats.get("champions", {}).get(my_champion, {}).get("games", 0)
        
        if games > 0:
            wr_adjustment = (wr - 50) * 0.4
            base_score += wr_adjustment
            factors["your_wr"] = f"{wr:.0f}% ({games} games)"
            confidence_points += min(games, 20)
        
        # 2. Matchups contre les ennemis
        matchup_adjustments = []
        for enemy in enemy_champions:
            if not enemy:
                continue
            wr_vs, games_vs = self.get_matchup_winrate(my_champion, enemy)
            if wr_vs is not None and games_vs >= 2:
                adj = (wr_vs - 50) * 0.3
                matchup_adjustments.append((enemy, wr_vs, games_vs, adj))
                confidence_points += min(games_vs, 5)
        
        if matchup_adjustments:
            total_adj = sum(m[3] for m in matchup_adjustments) / len(matchup_adjustments)
            base_score += total_adj
            
            best = max(matchup_adjustments, key=lambda x: x[1])
            worst = min(matchup_adjustments, key=lambda x: x[1])
            
            factors["best_matchup"] = f"vs {best[0]}: {best[1]:.0f}% WR"
            factors["worst_matchup"] = f"vs {worst[0]}: {worst[1]:.0f}% WR"
            
            if worst[1] < 40:
                recommendations.append(f"⚠️ Attention au matchup vs {worst[0]}!")
        
        # 3. Synergies avec alliés
        synergy_adjustments = []
        synergies = self.stats.get("ally_synergies", {})
        
        for ally in ally_champions:
            if not ally:
                continue
            key = f"{my_champion}+{ally}"
            if key in synergies and synergies[key].get("games", 0) >= 2:
                s = synergies[key]
                wr_with = (s["wins"] / s["games"]) * 100
                adj = (wr_with - 50) * 0.2
                synergy_adjustments.append((ally, wr_with, s["games"], adj))
                confidence_points += min(s["games"], 3)
        
        if synergy_adjustments:
            total_syn = sum(s[3] for s in synergy_adjustments) / len(synergy_adjustments)
            base_score += total_syn
            
            best_syn = max(synergy_adjustments, key=lambda x: x[1])
            factors["best_synergy"] = f"avec {best_syn[0]}: {best_syn[1]:.0f}% WR"
        
        # 4. Tendance récente
        trend = self.get_recent_trend(my_champion)
        if trend:
            if trend["hot_streak"]:
                base_score += 5
                factors["momentum"] = "🔥 Hot streak!"
            elif trend["tilt_alert"]:
                base_score -= 5
                factors["momentum"] = "⚠️ Losing streak"
                recommendations.append("💡 Considère prendre une pause ou jouer un autre champion")
        
        # 5. Playstyle
        playstyle = self.get_playstyle_analysis(my_champion)
        if playstyle:
            factors["playstyle"] = f"{playstyle['playstyle']} player"
        
        if confidence_points >= 30:
            confidence = "HIGH"
        elif confidence_points >= 15:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        final_score = max(20, min(80, base_score))
        
        if final_score >= 60:
            recommendations.append("✅ Bon pick! Tu as l'avantage statistique")
        elif final_score <= 40:
            recommendations.append("⚠️ Matchup difficile. Considère un autre pick si possible")
        
        return {
            "win_chance": round(final_score, 1),
            "confidence": confidence,
            "confidence_points": confidence_points,
            "factors": factors,
            "recommendations": recommendations
        }
        # ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    SYNC MANAGER OPTIMISÉ                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class OptimizedSyncManager:
    """Synchronisation parallèle avec extraction avancée"""
    
    def __init__(self, api, stats_manager, puuid):
        self.api = api
        self.stats = stats_manager
        self.puuid = puuid
    
    def sync_matches(self, count=30, max_workers=3):
        """Synchronise les matchs avec toutes les données avancées"""
        
        print(f"\n📊 Synchronisation de {count} games...")
        print("   ⚡ Mode parallèle activé")
        
        match_ids = self.api.get_match_history(self.puuid, count)
        
        if not match_ids:
            print("❌ Aucune game trouvée")
            return 0
        
        to_analyze = [mid for mid in match_ids if not self.stats.is_match_analyzed(mid)]
        already = len(match_ids) - len(to_analyze)
        
        if already > 0:
            print(f"   ✅ {already} games déjà analysées")
        
        if not to_analyze:
            print(f"\n   ℹ️  Toutes les games sont déjà analysées!")
            return 0
        
        print(f"   📥 {len(to_analyze)} nouvelles games à analyser")
        
        to_fetch = [mid for mid in to_analyze if mid not in self.api.matches_cache]
        
        if to_fetch:
            print(f"   ⬇️  Téléchargement de {len(to_fetch)} matchs...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self.api.get_match_details, mid, True): mid for mid in to_fetch}
                
                done = 0
                for future in as_completed(futures):
                    done += 1
                    pct = done * 100 // len(to_fetch)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    print(f"\r   [{bar}] {pct}%", end="", flush=True)
            
            print()
            self.api.save_matches_cache()
        
        print(f"\n   🔍 Analyse des nouvelles games...")
        
        analyzed = 0
        skipped = 0
        
        for i, match_id in enumerate(to_analyze):
            pct = (i + 1) * 100 // len(to_analyze)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r   [{bar}] {pct}% - Analyse...", end="", flush=True)
            
            match = self.api.matches_cache.get(match_id)
            if not match:
                skipped += 1
                continue
            
            queue_id = match["info"].get("queueId", 0)
            if queue_id in [0, 830, 840, 850]:
                skipped += 1
                continue
            
            my_stats = None
            allies = []
            enemies = []
            my_role = ""
            
            for p in match["info"]["participants"]:
                if p["puuid"] == self.puuid:
                    my_stats = p
                    my_role = p.get("teamPosition", "")
            
            if not my_stats:
                skipped += 1
                continue
            
            for p in match["info"]["participants"]:
                if p["teamId"] == my_stats["teamId"]:
                    if p["puuid"] != self.puuid:
                        allies.append(p["championName"])
                else:
                    enemies.append(p["championName"])
            
            added = self.stats.add_game_advanced(
                match_data=match,
                my_stats=my_stats,
                match_id=match_id,
                allies=allies,
                enemies=enemies,
                my_role=my_role
            )
            
            if added:
                analyzed += 1
        
        self.stats.save()
        
        print(f"\n\n   ✅ {analyzed} nouvelles games analysées!")
        if skipped > 0:
            print(f"   ⏭️  {skipped} games ignorées")
        
        total = len(self.stats.stats.get("analyzed_matches", []))
        print(f"\n   📊 Total dans ta base: {total} games uniques")
        
        return analyzed


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    SYSTÈME DE RECOMMANDATION V4                                ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class AIRecommender:
    """Système de recommandation avec toutes les données avancées"""
    
    def __init__(self, api, stats_manager, champion_manager, items_db):
        self.api = api
        self.stats = stats_manager
        self.champ_mgr = champion_manager
        self.items_db = items_db
    
    def score_item_for_composition(self, item_id, my_champion, enemy_analysis, my_dmg_type):
        """Score an item based on enemy composition and item properties.
        
        Returns score between 0-100.
        """
        score = 50  # baseline
        item_stats = self.items_db.extract_item_stats(item_id)
        item_passives = self.items_db.get_item_passives(item_id)
        
        # 1. If champion needs AD and item gives AD, bonus
        if my_dmg_type == "ad" and item_stats["ad"] > 0:
            score += min(item_stats["ad"] / 50, 15)  # cap at +15
        elif my_dmg_type == "ap" and item_stats["ap"] > 0:
            score += min(item_stats["ap"] / 30, 15)
        
        # 2. Defensive stats vs enemy composition
        if enemy_analysis["ad_damage"] >= 2 and item_stats["armor"] > 0:
            score += min(item_stats["armor"] / 30, 20)
        if enemy_analysis["ap_damage"] >= 2 and item_stats["mr"] > 0:
            score += min(item_stats["mr"] / 30, 20)
        
        # 3. Passives vs enemy threats
        if enemy_analysis["healing_threat"] and "antiheal" in item_passives:
            score += 25
        if enemy_analysis["cc_heavy"] and "mr" in item_passives:
            score += 15
        if enemy_analysis["tank_count"] >= 2:
            if "armor_pen" in item_passives or "pen" in item_passives:
                score += 20
        if enemy_analysis["assassin_count"] >= 2:
            if "survival" in item_passives or "armor" in item_passives or "mr" in item_passives:
                score += 20
        
        # 4. Utility bonuses
        if "ah" in item_passives:
            score += 5
        if "mobility" in item_passives:
            score += 3
        
        return min(score, 100)
    
    def analyze_enemy_composition(self, enemy_champions):
        """Analyse la compo ennemie"""
        analysis = {
            "tank_count": 0,
            "assassin_count": 0,
            "mage_count": 0,
            "adc_count": 0,
            "fighter_count": 0,
            "ap_damage": 0.0,
            "ad_damage": 0.0,
            "healing_threat": False,
            "cc_heavy": False,
            "engage_threat": False,
            "champions": enemy_champions,
            "healing_champions": [],
            "cc_champions": [],
            "engage_champions": []
        }
        # Build a case-insensitive lookup for champion keys
        champ_map = {k.lower(): k for k in (self.api.champions_data or {}).keys()}

        for champ in enemy_champions:
            if not champ:
                continue

            raw = champ.strip()
            key = raw.lower()

            # Try exact case-insensitive match, then fuzzy match as fallback
            canonical = champ_map.get(key)
            if not canonical:
                # fuzzy match using difflib
                candidates = difflib.get_close_matches(key, list(champ_map.keys()), n=1, cutoff=0.7)
                if candidates:
                    canonical = champ_map[candidates[0]]

            # Optional debug output to inspect matching decisions
            if DEBUG_NAME_MATCH:
                if canonical:
                    if canonical.lower() == key:
                        print(f"[DEBUG] Exact match: '{raw}' -> '{canonical}'")
                    else:
                        print(f"[DEBUG] Fuzzy match: '{raw}' -> '{canonical}'")
                else:
                    print(f"[DEBUG] No match for: '{raw}'")

            if canonical and canonical in self.api.champions_data:
                data = self.api.champions_data[canonical]
                tags = data.get("tags", [])

                for tag in tags:
                    if tag == "Tank":
                        analysis["tank_count"] += 1
                    elif tag == "Assassin":
                        analysis["assassin_count"] += 1
                    elif tag == "Mage":
                        analysis["mage_count"] += 1
                    elif tag == "Marksman":
                        analysis["adc_count"] += 1
                    elif tag == "Fighter":
                        analysis["fighter_count"] += 1

                # Weight AP/AD contribution proportionally (handles hybrids)
                info = data.get("info", {})
                magic = float(info.get("magic", 0) or 0)
                attack = float(info.get("attack", 0) or 0)
                total = magic + attack
                if total > 0:
                    analysis["ap_damage"] += magic / total
                    analysis["ad_damage"] += attack / total
                else:
                    # fallback to type helper
                    dmg_type = BuildDatabase.get_champion_damage_type(data)
                    if dmg_type == "ap":
                        analysis["ap_damage"] += 1.0
                    else:
                        analysis["ad_damage"] += 1.0

            # Also check canonical-insensitive membership for special lists
            check_name = canonical if canonical else raw
            # Normalize check_name once for efficiency
            check_name_lower = check_name.lower()
            
            if any(c.lower() == check_name_lower for c in BuildDatabase.HEALING_CHAMPIONS):
                analysis["healing_threat"] = True
                analysis["healing_champions"].append(check_name)
            if any(c.lower() == check_name_lower for c in BuildDatabase.CC_HEAVY_CHAMPIONS):
                analysis["cc_heavy"] = True
                analysis["cc_champions"].append(check_name)
            if any(c.lower() == check_name_lower for c in BuildDatabase.ENGAGE_CHAMPIONS):
                analysis["engage_threat"] = True
                analysis["engage_champions"].append(check_name)
        
        return analysis
    
    def recommend_champion(self, enemy_champions, ally_champions=None):
        """Recommande les meilleurs champions avec prédiction de victoire"""
        
        enemy_analysis = self.analyze_enemy_composition(enemy_champions)
        
        available_ids = self.champ_mgr.get_available_champions()
        available_names = {self.api.get_champion_name(cid) for cid in available_ids}
        
        my_best = self.stats.get_best_champions(min_games=1, available_champions=available_names)
        
        if not my_best:
            return []
        
        recommendations = []
        
        for champ_stats in my_best[:20]:
            champ_name = champ_stats["champion"]
            score = champ_stats["score"]
            reasons = []
            
            champ_data = self.api.champions_data.get(champ_name)
            if not champ_data:
                continue
            
            if champ_stats["winrate"] >= 55:
                score += 30
                reasons.append(f"🔥 {champ_stats['winrate']:.0f}% WR sur {champ_stats['games']} games")
            elif champ_stats["winrate"] >= 50:
                score += 15
                reasons.append(f"✅ {champ_stats['winrate']:.0f}% WR")
            elif champ_stats["winrate"] < 45:
                score -= 20
                reasons.append(f"⚠️ {champ_stats['winrate']:.0f}% WR (risqué)")
            
            matchup_bonus = 0
            for enemy in enemy_champions:
                if enemy:
                    wr, games = self.stats.get_matchup_winrate(champ_name, enemy)
                    if wr is not None and games >= 2:
                        if wr >= 60:
                            matchup_bonus += 20
                            reasons.append(f"💪 {wr:.0f}% vs {enemy}")
                        elif wr <= 40:
                            matchup_bonus -= 15
                            reasons.append(f"⚠️ {wr:.0f}% vs {enemy}")
            
            score += matchup_bonus
            
            if ally_champions:
                synergy_data = self.stats.get_ally_synergies(champ_name, min_games=2)
                for ally in ally_champions:
                    for s in synergy_data.get("best_allies", []):
                        if s["ally"] == ally and s["winrate"] >= 55:
                            score += 15
                            reasons.append(f"🤝 {s['winrate']:.0f}% avec {ally}")
            
            trend = self.stats.get_recent_trend(champ_name)
            if trend:
                if trend["hot_streak"]:
                    score += 10
                    reasons.append("🔥 Hot streak!")
                elif trend["tilt_alert"]:
                    score -= 15
                    reasons.append("😰 Losing streak")
            
            playstyle = self.stats.get_playstyle_analysis(champ_name)
            if playstyle:
                reasons.append(f"🎯 {playstyle['playstyle']} player")
            
            champ_class = BuildDatabase.get_champion_class(champ_data)
            champ_dmg = BuildDatabase.get_champion_damage_type(champ_data)
            
            if enemy_analysis["tank_count"] >= 2:
                if champ_name in ["Vayne", "Fiora", "Gwen", "Kog'Maw"]:
                    score += 20
                    reasons.append("🛡️ Tank killer")
            
            if ally_champions:
                ally_analysis = self.analyze_enemy_composition(ally_champions)
                if ally_analysis["ap_damage"] == 0 and champ_dmg == "ap":
                    score += 15
                    reasons.append("🔮 Seul AP de l'équipe")
            
            recommendations.append({
                "champion": champ_name,
                "score": score,
                "winrate": champ_stats["winrate"],
                "games": champ_stats["games"],
                "kda": champ_stats["kda"],
                "reasons": reasons,
                "class": champ_class,
                "damage_type": champ_dmg
            })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]
    
    def recommend_build(self, my_champion, enemy_champions, live_game=None, my_team_id=None):
        """Recommande un build basé sur TES stats + composition ennemie + stats items"""
        
        enemy_analysis = self.analyze_enemy_composition(enemy_champions)
        champ_data = self.api.champions_data.get(my_champion)
        
        if not champ_data:
            return {"error": f"Champion {my_champion} non trouvé"}
        
        champ_class = BuildDatabase.get_champion_class(champ_data)
        champ_dmg = BuildDatabase.get_champion_damage_type(champ_data)
        
        build = {
            "champion": my_champion,
            "boots": {"name": "", "why": ""},
            "your_best_items": [],
            "recommended_first": None,
            "best_combo": None,
            "situational": [],
            "anti_heal": None,
            "warnings": [],
            "item_reasons": {}  # NEW: raisons mathématiques pour chaque item
        }
        
        # Get personal build stats (min_games=3 for higher confidence)
        your_builds = self.stats.get_best_builds(my_champion, min_games=3)
        
        if your_builds:
            best_items = your_builds.get("best_items", [])
            
            # Score each item based on composition
            scored_items = []
            for item in best_items:
                item_id = item.get('item_id', 0)
                personal_wr = item.get('winrate', 50)
                composition_score = self.score_item_for_composition(item_id, my_champion, enemy_analysis, champ_dmg)
                
                # Combine: 60% personal WR + 40% composition fit
                combined_score = (personal_wr * 0.6) + (composition_score * 0.4)
                
                item_stats = self.items_db.extract_item_stats(item_id)
                item_passives = self.items_db.get_item_passives(item_id)
                
                # Generate reason
                reasons = []
                if item.get('games', 0) >= 3:
                    reasons.append(f"Ton WR: {personal_wr}% ({item.get('games')}g)")
                if item_stats["ad"] > 0 and champ_dmg == "ad":
                    reasons.append(f"+{item_stats['ad']:.0f} AD")
                if item_stats["ap"] > 0 and champ_dmg == "ap":
                    reasons.append(f"+{item_stats['ap']:.0f} AP")
                if enemy_analysis["healing_threat"] and "antiheal" in item_passives:
                    reasons.append("Anti-heal (vs heal threat)")
                if enemy_analysis["tank_count"] >= 2 and ("armor_pen" in item_passives or "pen" in item_passives):
                    reasons.append(f"Pen ({enemy_analysis['tank_count']} tanks)")
                if enemy_analysis["ad_damage"] >= 2 and item_stats["armor"] > 0:
                    reasons.append(f"+{item_stats['armor']:.0f} Armor (vs {enemy_analysis['ad_damage']} AD)")
                
                scored_items.append({
                    **item,
                    "composition_score": round(composition_score, 1),
                    "combined_score": round(combined_score, 1),
                    "reasons": reasons
                })
            
            # Sort by combined score
            scored_items.sort(key=lambda x: x['combined_score'], reverse=True)
            
            build["your_best_items"] = scored_items[:5]
            build["recommended_first"] = your_builds.get("best_first_item")
            build["best_combo"] = your_builds.get("best_combo")
            
            worst = your_builds.get("worst_items", [])
            if worst:
                build["warnings"].append("❌ Items à éviter (mauvais WR pour toi):")
                for item in worst:
                    build["warnings"].append(f"   • {item.get('name', 'Unknown')}: {item.get('winrate', 0)}%")
        
        if enemy_analysis["cc_heavy"] or enemy_analysis["ap_damage"] >= 3:
            build["boots"] = {
                "name": "Mercury's Treads",
                "why": f"{'CC Heavy' if enemy_analysis['cc_heavy'] else ''} {enemy_analysis['ap_damage']} AP ennemis"
            }
        elif enemy_analysis["ad_damage"] >= 3:
            build["boots"] = {
                "name": "Plated Steelcaps",
                "why": f"{enemy_analysis['ad_damage']} AD ennemis"
            }
        elif champ_class == "adc":
            build["boots"] = {"name": "Berserker's Greaves", "why": "ADC standard"}
        elif champ_dmg == "ap":
            build["boots"] = {"name": "Sorcerer's Shoes", "why": "Pen magique"}
        else:
            build["boots"] = {"name": "Ionian Boots", "why": "Ability Haste"}
        
        # ANTI-HEAL: Vérifier si c'est vraiment utile pour TON champion
        if enemy_analysis["healing_threat"]:
            # Évaluer si anti-heal est pertinent pour ce champion
            anti_heal_useful = self._should_build_anti_heal(my_champion, champ_dmg, champ_class)
            
            if anti_heal_useful:
                build["anti_heal"] = {
                    "name": "Mortal Reminder" if champ_dmg == "ad" else "Morellonomicon",
                    "why": "Heal champions détectés: " + ", ".join(enemy_analysis["healing_champions"]),
                    "when": "Après 1er item"
                }
                build["warnings"].insert(0, "🩹 ANTI-HEAL RECOMMANDÉ!")
            else:
                # Signaler que anti-heal existe mais ce n'est pas prioritaire
                build["anti_heal"] = {
                    "name": "Mortal Reminder" if champ_dmg == "ad" else "Morellonomicon",
                    "why": "Heal champions détectés: " + ", ".join(enemy_analysis["healing_champions"]),
                    "when": "Optionnel - Pas prioritaire pour " + my_champion
                }
        
        if enemy_analysis["tank_count"] >= 2:
            if champ_dmg == "ad":
                build["situational"].append({
                    "name": "Lord Dominik's Regards",
                    "why": f"{enemy_analysis['tank_count']} tanks détectés"
                })
            else:
                build["situational"].append({
                    "name": "Void Staff",
                    "why": f"{enemy_analysis['tank_count']} tanks détectés"
                })
        
        if enemy_analysis["assassin_count"] >= 2:
            build["situational"].append({
                "name": "Zhonya's Hourglass" if champ_dmg == "ap" else "Guardian Angel",
                "why": f"{enemy_analysis['assassin_count']} assassins (survie)"
            })
        
        # Build prioritized sequence: 1st item → anti-heal → boots → pen/dmg → defensive
        build["priority_sequence"] = []
        
        # 1. First item from your best builds
        if build.get("recommended_first"):
            build["priority_sequence"].append({
                "step": 1,
                "item": build["recommended_first"].get("name", "First Item"),
                "reason": "1er item avec meilleur WR pour toi"
            })
        
        # 2. Anti-heal if needed AND useful for this champion
        if build.get("anti_heal") and "RECOMMANDÉ" in build["warnings"][0] if build["warnings"] else False:
            build["priority_sequence"].append({
                "step": 2,
                "item": build["anti_heal"].get("name", "Anti-Heal"),
                "reason": build["anti_heal"].get("why", "Heal threat")
            })
        
        # 3. Boots
        if build.get("boots") and build["boots"].get("name"):
            build["priority_sequence"].append({
                "step": 3,
                "item": build["boots"].get("name", "Boots"),
                "reason": build["boots"].get("why", "Standard")
            })
        
        # 4. Defensive if needed (assassins, cc, etc.)
        defensive_added = False
        for sit in build.get("situational", []):
            if "assassin" in sit.get("why", "").lower() or "survie" in sit.get("why", "").lower():
                if not defensive_added:
                    build["priority_sequence"].append({
                        "step": 4,
                        "item": sit.get("name", "Defensive"),
                        "reason": sit.get("why", "")
                    })
                    defensive_added = True
        
        # 5. Pen/Dmg for tanks
        for sit in build.get("situational", []):
            if "tank" in sit.get("why", "").lower():
                build["priority_sequence"].append({
                    "step": 5,
                    "item": sit.get("name", "Tank Counter"),
                    "reason": sit.get("why", "")
                })
        
        # If live game data is provided, analyze enemy items/gold and adapt build
        if live_game and my_team_id is not None:
            try:
                enemy_items_analysis = self._analyze_enemy_items(live_game, my_team_id)
                adaptive_build = self._adapt_build_to_game_state(build, enemy_items_analysis, my_champion)
                # Propagate original item reasons if present
                if 'your_best_items' in build:
                    adaptive_build.setdefault('your_best_items', build['your_best_items'])
                return adaptive_build
            except Exception:
                # On error, fallback to base build
                return build

        return build
    
    def recommend_runes_and_spells(self, my_champion, enemy_champions):
        """Recommande les meilleures runes et spells basés sur TES stats + composition ennemie"""
        
        recommendations = {
            "champion": my_champion,
            "runes": {
                "keystone": None,
                "secondaries": [],
                "explanation": ""
            },
            "spells": {
                "primary": None,
                "secondary": None,
                "explanation": ""
            }
        }
        
        # Récupérer tes meilleures runes avec ce champion
        builds_data = self.stats.stats.get("builds_history", {}).get(my_champion, {})
        runes_data = builds_data.get("runes", {})
        spells_data = builds_data.get("spells", {})
        
        # Recommander les meilleures runes par WR
        if runes_data:
            rune_list = []
            for rune_id_str, rune_info in runes_data.items():
                games = rune_info.get("games", 0)
                if games >= 2:  # Min 2 games de confiance
                    wins = rune_info.get("wins", 0)
                    wr = (wins / games * 100) if games > 0 else 0
                    rune_list.append({
                        "id": int(rune_id_str),
                        "wr": wr,
                        "games": games,
                        "wins": wins
                    })
            
            if rune_list:
                rune_list.sort(key=lambda x: x["wr"], reverse=True)
                best_rune = rune_list[0]
                recommendations["runes"]["keystone"] = {
                    "id": best_rune["id"],
                    "wr": round(best_rune["wr"], 1),
                    "games": best_rune["games"]
                }
                recommendations["runes"]["explanation"] = f"Ton meilleur keystone: {best_rune['wr']:.1f}% WR ({best_rune['games']} games)"
        
        # Recommander les meilleurs spells par WR
        if spells_data:
            spell_list = []
            for spell_id_str, spell_info in spells_data.items():
                games = spell_info.get("games", 0)
                if games >= 3:
                    wins = spell_info.get("wins", 0)
                    wr = (wins / games * 100) if games > 0 else 0
                    spell_list.append({
                        "id": int(spell_id_str),
                        "wr": wr,
                        "games": games,
                        "wins": wins
                    })
            
            if spell_list:
                spell_list.sort(key=lambda x: x["wr"], reverse=True)
                primary_spell = spell_list[0]
                secondary_spell = spell_list[1] if len(spell_list) > 1 else spell_list[0]
                
                recommendations["spells"]["primary"] = {
                    "id": primary_spell["id"],
                    "wr": round(primary_spell["wr"], 1),
                    "games": primary_spell["games"]
                }
                recommendations["spells"]["secondary"] = {
                    "id": secondary_spell["id"],
                    "wr": round(secondary_spell["wr"], 1),
                    "games": secondary_spell["games"]
                }
                recommendations["spells"]["explanation"] = f"Ton combo préféré basé sur ton WR perso"
        
        return recommendations
    
    def _should_build_anti_heal(self, champion, dmg_type, champ_class):
        """Évalue si l'anti-heal est vraiment utile pour ce champion"""
        # Champions qui n'ont pas vraiment besoin d'anti-heal (contrôle à distance limité)
        no_anti_heal = ["Amumu", "Sejuani", "Zac", "Rammus", "Malphite", "Evelynn"]
        
        # Champions qui bénéficient beaucoup d'anti-heal (attaques fréquentes)
        high_benefit = ["Vayne", "Draven", "Ashe", "Caitlyn", "Leona", "Pyke", "Renekton", "Darius"]
        
        if champion in no_anti_heal:
            # Ces champions font rarement des attaques rapides (surtout tanks AP)
            return False
        
        if champion in high_benefit:
            # Ces champions ont des attaques fréquentes/pénétrantes
            return True
        
        # Heuristique: Les ADCs et les bruisers bénéficient d'anti-heal
        if champ_class in ["adc", "fighter", "marksman"]:
            return True
        
        # Les mages AP purs n'en ont pas vraiment besoin
        if dmg_type == "ap" and champ_class == "mage":
            return False
        
        # Par défaut, support/tanks → utile (souvent des attaques régulières)
        if champ_class in ["support", "tank"]:
            return True
        
        return False
        # ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    APPLICATION PRINCIPALE                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

class LoLCoachAI:
    """Application principale V4 avec apprentissage avancé"""
    
    def __init__(self):
        self.clear_screen()
        self.print_banner()
        
        os.makedirs(DATA_DIR, exist_ok=True)
        
        print("\n🔧 Initialisation...")
        self.items_db = ItemsDatabase()
        self.runes_db = RuneDatabase()
        self.spells_db = SpellDatabase()
        self.api = RiotAPI(API_KEY)
        self.stats = AdvancedStatsManager(self.items_db)
        self.champ_mgr = ChampionManager(self.api)
        self.recommender = AIRecommender(self.api, self.stats, self.champ_mgr, self.items_db)
        
        self.puuid = None
        self.summoner_id = None
        self.summoner_name = None
        self.region = REGION
        self.sync_manager = None
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗      ██████╗ ██╗          ██████╗ ██████╗  █████╗  ██████╗██╗  ██╗      ║
║   ██║     ██╔═══██╗██║         ██╔════╝██╔═══██╗██╔══██╗██╔════╝██║  ██║      ║
║   ██║     ██║   ██║██║         ██║     ██║   ██║███████║██║     ███████║      ║
║   ██║     ██║   ██║██║         ██║     ██║   ██║██╔══██║██║     ██╔══██║      ║
║   ███████╗╚██████╔╝███████╗    ╚██████╗╚██████╔╝██║  ██║╚██████╗██║  ██║      ║
║   ╚══════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝      ║
║                                                                               ║
║                   🤖 AI COACH - Version 4.0 ADVANCED 🤖                      ║
║                                                                               ║
║  ✨ NOUVEAU DANS V4:                                                          ║
║     • Tracking des builds avec WR par item                                    ║
║     • Analyse Early/Mid/Late game                                             ║
║     • Synergies avec alliés                                                   ║
║     • Tendances récentes + détection tilt                                     ║
║     • Prédiction de victoire basée sur TON historique                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """)
    
    def connect(self):
        """Connexion au compte Riot"""
        print(f"\n🔗 Connexion à {SUMMONER_NAME}#{TAG_LINE}...")
        
        self.api.load_all_champions()
        
        account = self.api.get_account(SUMMONER_NAME, TAG_LINE)
        if not account:
            print("\n❌ Impossible de se connecter!")
            print("   Vérifie:")
            print("   - Ta clé API dans config.py")
            print("   - Ton pseudo et tag")
            print("   - Que la clé n'a pas expiré (24h)")
            return False
        
        self.puuid = account.get("puuid")
        self.summoner_name = account.get("gameName")
        print(f"✅ Connecté: {self.summoner_name}")
        
        summoner = self.api.get_summoner_by_puuid(self.puuid)
        if summoner:
            self.summoner_id = summoner.get("id")
            print(f"   Niveau: {summoner.get('summonerLevel')}")
        
        self.champ_mgr.load_my_champions(self.puuid)
        self.sync_manager = OptimizedSyncManager(self.api, self.stats, self.puuid)
        
        total = len(self.stats.stats.get("analyzed_matches", []))
        if total > 0:
            print(f"   📊 {total} games déjà dans ta base de données")
        
        # Affiche l'état de l'API au démarrage
        print("\n" + "="*70)
        print(f"🔌 API Riot: ✅ Connecté - {self.summoner_name} ({self.region})")
        print("="*70)
        
        return True
    
    def sync_stats(self, count=30):
        """Synchronisation des stats"""
        return self.sync_manager.sync_matches(count, max_workers=3)
    
    def show_champion_details(self):
        """Analyse détaillée d'un champion spécifique"""
        self.clear_screen()
        self.print_banner()
        
        print("\n" + "═" * 80)
        print("                    🔍 ANALYSE DÉTAILLÉE D'UN CHAMPION")
        print("═" * 80)
        
        champion_input = input("\n👉 Quel champion? ").strip()

        if not champion_input:
            return

        # Normalize / canonicalize champion name to match stored stats keys
        champions_stats = self.stats.stats.get("champions", {})
        champ_key = None

        # Exact match first
        if champion_input in champions_stats:
            champ_key = champion_input
        else:
            # Case-insensitive match
            lower = champion_input.lower()
            for k in champions_stats.keys():
                if k.lower() == lower:
                    champ_key = k
                    break

        # Fuzzy fallback using difflib against known champion keys
        if not champ_key:
            try:
                candidates = difflib.get_close_matches(champion_input, list(champions_stats.keys()), n=1, cutoff=0.7)
                if candidates:
                    champ_key = candidates[0]
            except Exception:
                champ_key = None

        if not champ_key:
            print(f"\n⚠️ Champion '{champion_input}' non trouvé dans tes stats.")
            return

        # Load analyses using canonical key
        playstyle = self.stats.get_playstyle_analysis(champ_key)
        # Use advanced build with scoring (requires enemy composition for full scoring)
        # For now, use basic builds and note that full scoring requires enemy selection
        builds = self.stats.get_best_builds(champ_key, min_games=1)
        synergies = self.stats.get_ally_synergies(champ_key, min_games=2)

        champ_stats = champions_stats.get(champ_key, {})
        games_played = champ_stats.get('games', 0)
        wins = champ_stats.get('wins', 0)
        winrate = (wins / games_played * 100) if games_played > 0 else 0
        kda = (champ_stats.get('kills', 0) + champ_stats.get('assists', 0)) / max(champ_stats.get('deaths', 1), 1) if games_played > 0 else 0
        
        if not playstyle and not builds and games_played < 1:
            print(f"\n⚠️ Pas assez de données pour {champ_key}. Joue plus de games!")
            return

        print(f"\n{'═' * 80}")
        print(f"📊 {champ_key.upper()} — {games_played} games | {winrate:.1f}% WR | KDA {kda:.2f}")
        print(f"{'═' * 80}")
        
        if playstyle:
            print(f"\n🎯 PLAYSTYLE: {playstyle['playstyle']}")
            print(f"   {playstyle['tip']}")
            print(f"\n   Early WR: {playstyle['early_wr']}% ({playstyle['early_games']} games)")
            print(f"   Mid WR: {playstyle['mid_wr']}% ({playstyle['mid_games']} games)")
            print(f"   Late WR: {playstyle['late_wr']}% ({playstyle['late_games']} games)")
            print(f"\n   Avg CS/min: {playstyle['avg_cs_per_min']}")
            print(f"   Avg Gold/min: {playstyle['avg_gold_per_min']}")
        
        if builds:
            print(f"\n💎 BUILDS OPTIMAUX:")
            if builds.get("best_items"):
                print(f"")
                for item in builds["best_items"][:5]:
                    games = item.get('games', 0)
                    global_games = item.get('global_games', 0)
                    reliability = item.get('reliability', 'UNKNOWN')
                    wr = item.get('winrate', 0)
                    
                    # Main line with WR as simplified score
                    star = "⭐" if wr >= 55 else ""
                    print(f"   • {item.get('name')}: {wr}% {star}")
                    
                    # Reasons line
                    global_note = f" + {global_games} global" if global_games > 0 else ""
                    print(f"      └─ Ton WR: {wr}% ({games}g{global_note}) [{reliability}]")
                    print()
            
            if builds.get("best_first_item"):
                first_item = builds['best_first_item']
                first_games = first_item.get('games', 0)
                first_reliability = first_item.get('reliability', 'UNKNOWN')
                print(f"\n   1er item recommandé: {first_item.get('name')} ({first_games}g) [{first_reliability}]")
        
        if synergies:
            print(f"\n🤝 SYNERGIES:")
            if synergies.get("best_allies"):
                print(f"   Meilleurs alliés:")
                for ally in synergies["best_allies"][:3]:
                    print(f"      • {ally.get('ally')}: {ally.get('winrate')}% WR")

        # Matchups / Counters
        matchups = champ_stats.get('matchups', {})
        if matchups:
            pairs = []
            for enemy, m in matchups.items():
                g = m.get('games', 0)
                w = m.get('wins', 0)
                wrm = (w / g * 100) if g > 0 else 0
                pairs.append({'enemy': enemy, 'games': g, 'wins': w, 'wr': wrm})

            # Separate confident matchups (>=2 games) from low-sample (1 game)
            confident = [p for p in pairs if p['games'] >= 2]
            low_sample = [p for p in pairs if p['games'] < 2]

            confident_desc = sorted(confident, key=lambda x: x['wr'], reverse=True)
            confident_asc = sorted(confident, key=lambda x: x['wr'])

            low_desc = sorted(low_sample, key=lambda x: x['wr'], reverse=True)
            low_asc = sorted(low_sample, key=lambda x: x['wr'])

            top = confident_desc[:5]
            # if not enough confident, fill with low-sample (marked)
            fill_from_low = 5 - len(top)
            if fill_from_low > 0:
                top += low_desc[:fill_from_low]

            top_enemies = {p['enemy'] for p in top}

            worst = confident_asc[:5]
            # exclude any in top_enemies and, if too few, fill from low_asc
            worst = [p for p in worst if p['enemy'] not in top_enemies][:5]
            if len(worst) < 5:
                worst += [p for p in low_asc if p['enemy'] not in top_enemies][:5 - len(worst)]

            def gtext(n):
                return f"{n} game" if n == 1 else f"{n} games"

            print(f"\n🔁 MATCHUPS ({len(pairs)}):")

            if top:
                print("   Meilleurs matchups (pour toi):")
                for p in top:
                    reliability = self.stats._reliability_tag(p['games'])
                    note = " (low sample)" if p['games'] < 2 else ""
                    print(f"      • {p['enemy']}: {p['wr']:.1f}% WR ({gtext(p['games'])}) [{reliability}]{note}")

            if worst:
                print("\n   Pires matchups (pour toi):")
                for p in worst:
                    reliability = self.stats._reliability_tag(p['games'])
                    note = " (low sample)" if p['games'] < 2 else ""
                    print(f"      • {p['enemy']}: {p['wr']:.1f}% WR ({gtext(p['games'])}) [{reliability}]{note}")

            # Quick summary: only show counters where we have >=2 games (confidence)
            countered = [p['enemy'] for p in confident if p['wr'] >= 55]
            weak_against = [p['enemy'] for p in confident if p['wr'] <= 45]

            if countered:
                print(f"\n✅ Tu counter: {', '.join(countered[:10])}")
            if weak_against:
                print(f"\n⚠️ Tu es faible contre: {', '.join(weak_against[:10])}")
    
    def show_stats(self):
        self.clear_screen()
        self.print_banner()
    
        print("\n" + "═" * 80)
        print("                           📊 TES STATISTIQUES")
        print("═" * 80)
    
        global_stats = self.stats.get_global_stats()
        if not global_stats:
            print("\n⚠️ Aucune donnée. Lance 'Synchroniser' d'abord!")
            return
    
        total_games = global_stats['total_games']
    
        # ════════════════════════════════════════════════════════════
        # 📊 STATS GLOBALES
        # ════════════════════════════════════════════════════════════
        
        print(f"\n📈 VUE D'ENSEMBLE:")
        print(f"   Total: {total_games} games | {global_stats['winrate']:.1f}% WR")
        print(f"   Victoires: {global_stats['wins']} | Défaites: {global_stats['losses']}")
        
        # ════════════════════════════════════════════════════════════
        # 🔥 TENDANCE RÉCENTE (si assez de games)
        # ════════════════════════════════════════════════════════════
        
        # --- Début: Trend ---
        trend = self.stats.get_recent_trend()
        if trend and total_games >= 10:
            print(f"\n🔄 FORME ACTUELLE ({trend['recent_games']} dernières games):")
            print(f"   {trend['trend_text']}")
            print(f"   WR: {trend['recent_wr']:.1f}% | KDA: {trend['recent_kda']:.2f} | {trend['last_5']}")
        
        if trend['hot_streak']:
            print("   🔥 HOT STREAK! Continue comme ça!")
        elif trend['tilt_alert']:
            print("   ⚠️ LOSING STREAK - Prends une pause de 10min!")

        # ════════════════════════════════════════════════════════════
        # 🏆 TES CHAMPIONS (adaptation selon le nombre)
        # ════════════════════════════════════════════════════════════

        best = self.stats.get_best_champions(min_games=1)
        if not best:
            print("\n⚠️ Aucun champion joué. Synchronise tes games!")
            return

        # Stats globales
        total_games = sum(c.get('games', 0) for c in best)
        total_wins = sum(c.get('wins', 0) for c in best)
        global_stats = {
            'winrate': (total_wins / total_games * 100) if total_games > 0 else 0
        }

        # Optional trend
        trend = None
        if hasattr(self.stats, 'get_recent_trend'):
            try:
                trend = self.stats.get_recent_trend()
            except:
                pass

        total_champs = len(best)

        # --- Affichage dynamique ---
        if total_champs <= 5:
            print(f"\n🏆 TES {total_champs} CHAMPION{'S' if total_champs > 1 else ''}:")
            display_count = total_champs
            show_details = True

        elif total_champs <= 15:
            print(f"\n🏆 TES {total_champs} CHAMPIONS:")
            display_count = total_champs
            show_details = False

        else:
            print(f"\n🏆 TON POOL DE CHAMPIONS ({total_champs} champions):")
            if total_games < 50:
                display_count = 10
            elif total_games < 100:
                display_count = 15
            else:
                display_count = 20
                show_details = False

        # --- Affichage détaillé ---
        if show_details:
            for i, c in enumerate(best[:display_count], 1):
                games = c.get('games', 0)
                wins = c.get('wins', 0)
                winrate = c.get('winrate', 0)
                wr_icon = "🟢" if winrate >= 52 else "🟡" if winrate >= 48 else "🔴"

                print(f"\n   {i}. {c.get('champion','Unknown')}")
                print(f"      {wr_icon} {winrate:.1f}% WR ({wins}W/{max(games-wins,0)}L)")
                print(f"      KDA: {c.get('kda', 0):.2f}")

                roles = c.get('roles', {})
                if roles:
                    try:
                        main_role = max(roles.items(), key=lambda x: x[1].get('games', 0))
                        rg = main_role[1].get('games', 0)
                        rw = main_role[1].get('wins', 0)
                        rwr = (rw / rg * 100) if rg > 0 else 0
                        print(f"      Rôle: {main_role[0]} ({rg} games, {rwr:.0f}% WR)")
                    except:
                        pass

        # --- Affichage compact ---
        else:
            print()
            champions_by_perf = {"main": [], "joués": [], "essayés": []}

            for c in best:
                g = c.get('games', 0)
                if g >= 10:
                    champions_by_perf["main"].append(c)
                elif g >= 5:
                    champions_by_perf["joués"].append(c)
                else:
                    champions_by_perf["essayés"].append(c)

            # MAIN
            if champions_by_perf["main"]:
                print(f"\n   💎 TES MAINS ({len(champions_by_perf['main'])} champions):")
                print(f"      {'Champion':<20} {'Games':<7} {'WR':<10} {'KDA':<8}")
                print("      " + "─" * 50)

                for c in champions_by_perf["main"][:10]:
                    wr = c.get('winrate', 0)
                    wr_icon = "🟢" if wr >= 52 else "🟡" if wr >= 48 else "🔴"
                    print(f"      {c.get('champion'):<20} {c.get('games'):<7} {wr_icon} {wr:.1f}%   {c.get('kda'):.2f}")

            # JOUÉS
            if champions_by_perf["joués"]:
                print(f"\n   ⚡ JOUÉS RÉGULIÈREMENT ({len(champions_by_perf['joués'])} champions):")
                champs_str = []
                for c in champions_by_perf["joués"]:
                    wr = c.get('winrate', 0)
                    wr_icon = "🟢" if wr >= 50 else "🔴"
                    champs_str.append(f"{c.get('champion')} ({c.get('games')}g, {wr_icon}{wr:.0f}%)")

                for i in range(0, len(champs_str), 3):
                    print("      " + " | ".join(champs_str[i:i+3]))

            # ESSAYÉS
            if champions_by_perf["essayés"] and total_games >= 30:
                print(f"\n   🔍 ESSAYÉS ({len(champions_by_perf['essayés'])} champions):")
                names = [c.get('champion') for c in champions_by_perf["essayés"][:20]]
                print(f"      {', '.join(names)}")

        # --- Progression ---
        if total_games >= 20:
            monthly = self.stats.get_monthly_progress() if hasattr(self.stats, 'get_monthly_progress') else None
            if monthly and len(monthly) >= 2:
                print(f"\n📅 ÉVOLUTION:")
                cur = monthly[0]
                last = monthly[1]

                print(f"   Ce mois: {cur.get('winrate'):.1f}% WR ({cur.get('games')} games) | KDA {cur.get('avg_kda'):.2f}")
                diff = cur.get('winrate', 0) - last.get('winrate', 0)
                trend_icon = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"

                print(f"   Mois dernier: {last.get('winrate'):.1f}% WR ({last.get('games')} games)")
                print(f"   {trend_icon} {diff:+.1f}% de différence")

        # --- CONSEILS ---
        print("\n" + "─" * 80)
        print("💡 CONSEILS:")

        if total_games < 30:
            print("   • Joue encore 20+ games pour des recommandations précises")

        if total_champs > 20:
            print("   • Tu joues trop de champions différents!")
            print(f"   • Focus sur tes 5 meilleurs ({', '.join([c.get('champion') for c in best[:5]])})")
        elif total_champs <= 3 and total_games >= 30:
            print("   • Bon focus sur ton pool de champions!")

        if global_stats["winrate"] >= 55:
            print("   • 🔥 Excellent winrate! Continue à spam ranked!")
        elif global_stats["winrate"] <= 45:
            print("   • Focus sur 2-3 champions max et améliore ton macro")

        if trend:
            if trend.get('tilt_alert'):
                print("   • ⚠️ STOP! Prends une pause avant de continuer")
            elif trend.get('hot_streak'):
                print("   • 🚀 Profite de ta série, spam ranked maintenant!")

        print("─" * 80)

        # --- ACTIONS ---
        print("\n💡 ACTIONS RAPIDES:")
        print("   • Option 3 → Analyse détaillée d'un champion")
        print("   • Option 4 → Recommandations de pick")
        if total_games < 50:
            print("   • Option 1 → Sync plus de games pour + de précision")

        # --- VERDICT FINAL ---
        print("\n" + "═" * 80)
        print("💡 VERDICT:")

        # On prend le champion le plus joué
        main_champ = best[0]
        champion = main_champ.get("champion")
        games = main_champ.get("games", 0)
        wr = main_champ.get("winrate", 0)

        if games < 10:
            print(f"   ⏳ Joue encore {10 - games} games pour un avis fiable")
        elif wr >= 55:
            print(f"   ✅ SPAM {champion.upper()} en ranked!")
        elif wr >= 50:
            print(f"   ✅ Continue à jouer {champion}, tu es rentable")
        elif wr >= 45:
            print(f"   ⚠️ Améliore-toi avant de le spam en ranked")
        else:
            print(f"   ❌ Évite {champion} en ranked pour le moment")

    
    print(f"{'═' * 80}")
    
    def get_recommendations(self):
        """Obtient des recommandations avec prédiction de victoire"""
        self.clear_screen()
        self.print_banner()
        
        print("\n" + "═" * 80)
        print("                    🎯 RECOMMANDATIONS DE PICK")
        print("═" * 80)
        
        print("\n📝 Entre les champions ennemis (séparés par virgules)")
        print("   Exemple: Zed, Jinx, Leona, Lee Sin, Ahri")
        
        enemies_input = input("\n👉 Champions ennemis: ").strip()
        if not enemies_input:
            print("❌ Entre au moins un ennemi!")
            return
        
        enemy_list = [e.strip() for e in enemies_input.split(",") if e.strip()]
        
        print("\n📝 Champions alliés (optionnel, Entrée pour skip):")
        allies_input = input("👉 Alliés: ").strip()
        ally_list = [a.strip() for a in allies_input.split(",") if a.strip()] if allies_input else []
        
        print("\n" + "─" * 80)
        print("📊 ANALYSE COMPOSITION ENNEMIE")
        print("─" * 80)
        
        analysis = self.recommender.analyze_enemy_composition(enemy_list)
        
        print(f"\n   Composition:")
        print(f"   • Tanks: {analysis['tank_count']} | Assassins: {analysis['assassin_count']} | Mages: {analysis['mage_count']}")
        print(f"   • Dégâts: {int(round(analysis['ap_damage']))} AP / {int(round(analysis['ad_damage']))} AD")
        
        threats = []
        if analysis['healing_threat']:
            threats.append("🩹 HEAL - Anti-heal obligatoire!")
        if analysis['cc_heavy']:
            threats.append("🔒 CC Heavy - Mercury's Treads")
        if analysis['engage_threat']:
            threats.append("🚀 Engage fort - Positionne-toi bien")
        
        if threats:
            print(f"\n   ⚠️ Menaces:")
            for t in threats:
                print(f"   • {t}")
        
        print("\n" + "─" * 80)
        print("🏆 TOP 5 CHAMPIONS POUR TOI")
        print("─" * 80)
        
        reco = self.recommender.recommend_champion(enemy_list, ally_list)
        
        if not reco:
            print("\n⚠️ Pas assez de données. Joue plus de games et resync!")
            return
        
        for i, r in enumerate(reco, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            print(f"\n{emoji} {r['champion'].upper()}")
            print(f"   📊 {r['winrate']:.0f}% WR sur {r['games']} games | KDA {r['kda']:.2f}")
            
            for reason in r['reasons'][:4]:
                print(f"   {reason}")
            
            prediction = self.stats.predict_win_chance(r['champion'], ally_list, enemy_list)
            confidence_icon = "🟢" if prediction['confidence'] == "HIGH" else "🟡" if prediction['confidence'] == "MEDIUM" else "🔴"
            print(f"\n   🔮 Prédiction: {prediction['win_chance']:.0f}% de chances de victoire {confidence_icon}")
            
            if prediction['factors']:
                for key, value in list(prediction['factors'].items())[:2]:
                    print(f"      • {key}: {value}")
            
            if prediction['recommendations']:
                for rec in prediction['recommendations'][:1]:
                    print(f"   {rec}")
        
        if reco:
            best_champ = reco[0]['champion']
            
            print(f"\n{'═' * 80}")
            print(f"🔨 BUILD RECOMMANDÉ POUR {best_champ.upper()}")
            print("═" * 80)
            
            build = self.recommender.recommend_build(best_champ, enemy_list)
            
            if build.get('warnings'):
                print(f"\n⚠️ ALERTES IMPORTANTES:")
                for w in build['warnings']:
                    print(f"   {w}")
            
            # Show prioritized build sequence
            if build.get('priority_sequence'):
                print(f"\n📋 ORDRE DE BUILD (séquence prioritaire):")
                for seq in build['priority_sequence']:
                    print(f"   {seq['step']}. {seq['item']}")
                    print(f"      └─ {seq['reason']}")
            
            boots = build.get('boots', {})
            if boots and boots.get('name'):
                print(f"\n🥾 BOTTES: {boots.get('name', 'N/A')}")
                print(f"   → {boots.get('why', 'Standard')}")
            
            your_best_items = build.get('your_best_items', [])
            if your_best_items:
                print(f"\n📊 TES ITEMS AVEC LE MEILLEUR WR SUR {best_champ.upper()}:")
                print()
                for item in your_best_items[:4]:
                    combined_score = item.get('combined_score', 0)
                    reasons = item.get('reasons', [])
                    reliability = item.get('reliability', 'UNKNOWN')
                    
                    # Main line with score
                    star = "⭐" if combined_score >= 70 else ""
                    print(f"   • {item.get('name', 'Unknown')}: {combined_score}pts {star}")
                    
                    # Reasons line
                    reasons_text = ", ".join(reasons) if reasons else f"{item.get('winrate')}% WR ({item.get('games', 0)}g)"
                    print(f"      └─ {reasons_text} [{reliability}]")
                    print()
            else:
                print(f"\n📊 ITEMS:")
                print(f"   ⚠️ Pas assez de données de build pour {best_champ}")
            
            recommended_first = build.get('recommended_first')
            if recommended_first:
                print(f"\n🎯 1ER ITEM RECOMMANDÉ: {recommended_first.get('name', 'Unknown')}")
                print(f"   → {recommended_first.get('winrate', 0)}% WR quand tu rush cet item")
            
            best_combo = build.get('best_combo')
            if best_combo:
                combo_items = best_combo.get('items', [])
                if combo_items:
                    print(f"\n💎 TON MEILLEUR COMBO:")
                    print(f"   {' → '.join(combo_items)}")
                    print(f"   → {best_combo.get('winrate', 0)}% WR")
            
            anti_heal = build.get('anti_heal')
            if anti_heal:
                when_text = anti_heal.get('when', 'Quand nécessaire')
                if "Optionnel" in when_text:
                    print(f"\n🟡 ANTI-HEAL (optionnel): {anti_heal.get('name', 'N/A')}")
                    print(f"   → {anti_heal.get('why', '')}")
                    print(f"   ⏰ {when_text}")
                else:
                    print(f"\n🩹 ANTI-HEAL: {anti_heal.get('name', 'N/A')}")
                    print(f"   → {anti_heal.get('why', '')}")
                    print(f"   ⏰ Acheter: {when_text}")
            
            situational = build.get('situational', [])
            if situational:
                print(f"\n🔄 ITEMS SITUATIONNELS:")
                for item in situational:
                    print(f"   • {item.get('name', 'Unknown')}: {item.get('why', '')}")
            
            # RUNES ET SPELLS RECOMMENDATIONS
            print(f"\n{'═' * 80}")
            print(f"⚡ RUNES & SPELLS RECOMMANDÉS")
            print("═" * 80)
            
            rune_spell_reco = self.recommender.recommend_runes_and_spells(best_champ, enemy_list)
            
            if rune_spell_reco.get('runes', {}).get('keystone'):
                keystone = rune_spell_reco['runes']['keystone']
                print(f"\n🔮 KEYSTONE: ID {keystone['id']}")
                print(f"   → {keystone['wr']}% WR ({keystone['games']} games)")
                print(f"   → {rune_spell_reco['runes']['explanation']}")
            
            if rune_spell_reco.get('spells', {}).get('primary'):
                primary = rune_spell_reco['spells']['primary']
                secondary = rune_spell_reco['spells']['secondary']
                print(f"\n📞 SPELLS D'INVOCATEUR:")
                print(f"   Primary: ID {primary['id']} ({primary['wr']}% WR, {primary['games']}g)")
                print(f"   Secondary: ID {secondary['id']} ({secondary['wr']}% WR, {secondary['games']}g)")
                print(f"   → {rune_spell_reco['spells']['explanation']}")
    
    def check_live_game(self):
        """Vérifie si une game est en cours (champ select ou en jeu) et donne des recommandations"""
        self.clear_screen()
        self.print_banner()
        
        print("\n" + "═" * 80)
        print("                      🎮 DÉTECTION CHAMP SELECT / GAME EN COURS")
        print("═" * 80)
        
        print("\n🔍 Vérification...")
        
        game = self.api.get_current_game(self.puuid)
        
        if not game:
            print("\n⚪ Tu n'es pas en game actuellement")
            print("\n💡 Astuce: Lance cette fonction pendant le champ select ou en game!")
            return
        
        queue_id = game.get("gameQueueConfigId", 0)
        game_length = game.get("gameLength", 0)
        is_ranked = queue_id in [420, 440]
        
        my_team = []
        enemy_team = []
        my_champion = None
        my_team_id = None
        
        for p in game.get("participants", []):
            champ_name = self.api.get_champion_name(p.get("championId"))
            
            if p.get("puuid") == self.puuid:
                my_team_id = p.get("teamId")
                my_champion = champ_name
        
        for p in game.get("participants", []):
            champ_name = self.api.get_champion_name(p.get("championId"))
            if p.get("teamId") == my_team_id:
                my_team.append(champ_name)
            else:
                enemy_team.append(champ_name)
        
        # Détecter si c'est champ select ou game en cours
        is_champ_select = game_length == 0
        
        if is_champ_select:
            print(f"\n🎪 CHAMP SELECT DÉTECTÉ!")
            print(f"   Mode: {'RANKED' if is_ranked else 'Normal'}")
            
            # Afficher la compo ennemie connue (si dispo)
            enemy_picks = [e for e in enemy_team if e]
            if enemy_picks:
                print(f"\n   👹 Ennemis ({len(enemy_picks)}/5): {', '.join(enemy_picks)}")
            else:
                print(f"\n   👹 Ennemis: En attente des picks...")
            
            # Afficher la compo alliée
            ally_picks = [t for t in my_team if t]
            if ally_picks:
                print(f"   👥 Alliés ({len(ally_picks)}/4): {', '.join(ally_picks)}")
            else:
                print(f"   👥 Alliés: En attente des picks...")
            
            # Afficher la compo alliée
            if any(t for t in my_team if t):
                print(f"   👥 Votre équipe: {', '.join([t for t in my_team if t])}")
            
            # Recommandations de champions
            if any(e for e in enemy_team):
                print("\n" + "─" * 80)
                print("🎯 CHAMPIONS RECOMMANDÉS")
                print("─" * 80)
                
                reco = self.recommender.recommend_champion(enemy_team, [t for t in my_team if t])
                
                if reco:
                    for i, r in enumerate(reco[:3], 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        print(f"\n{emoji} {r['champion'].upper()}")
                        print(f"   📊 {r['winrate']:.0f}% WR sur {r['games']} games")
                        
                        for reason in r['reasons'][:3]:
                            print(f"   {reason}")
                        
                        # Runes recommandées pour ce champion
                        print(f"\n   🔮 RUNES SUGGÉRÉES:")
                        runes = self._get_suggested_runes(r['champion'], enemy_team)
                        if runes:
                            print(f"      Primaire: {runes.get('primary', 'Standard')}")
                            print(f"      Secondaire: {runes.get('secondary', 'Flex')}")
                        else:
                            print(f"      Adapt selon la compo!")
            else:
                print("\n⏳ En attente de picks ennemis...")
        else:
            print(f"\n🔴 TU ES EN GAME!")
            print(f"   Mode: {'RANKED' if is_ranked else 'Normal'}")
            print(f"   Durée: {game_length // 60}:{game_length % 60:02d}")
            
            print(f"\n   🎮 Tu joues: {my_champion}")
            print(f"   👥 Ton équipe: {', '.join(my_team)}")
            print(f"   👹 Ennemis: {', '.join(enemy_team)}")
            
            prediction = self.stats.predict_win_chance(my_champion, my_team, enemy_team)
            
            print(f"\n{'─' * 80}")
            print(f"🔮 PRÉDICTION DE VICTOIRE")
            print(f"{'─' * 80}")
            
            confidence_icon = "🟢" if prediction['confidence'] == "HIGH" else "🟡" if prediction['confidence'] == "MEDIUM" else "🔴"
            print(f"\n   {prediction['win_chance']:.0f}% de chances de victoire {confidence_icon}")
            print(f"   Confiance: {prediction['confidence']}")
            
            if prediction['factors']:
                print(f"\n   Facteurs:")
                for key, value in prediction['factors'].items():
                    print(f"   • {key}: {value}")
            
            if prediction['recommendations']:
                print(f"\n   Conseils:")
                for rec in prediction['recommendations']:
                    print(f"   {rec}")
            
            print(f"\n{'─' * 80}")
            print(f"⚡ RECOMMANDATIONS BUILD (adaptive)")
            print(f"{'─' * 80}")
            
            build = self.recommender.recommend_build(my_champion, enemy_team)
            
            # Analyser les items ennemis actuels pour adapter les recommandations
            enemy_items_analysis = self._analyze_enemy_items(game, my_team_id)
            
            # Afficher l'analyse des items ennemis
            if enemy_items_analysis["key_threats"]:
                print(f"\n⚠️ MENACES ENNEMIES ACTUELLES:")
                for threat in enemy_items_analysis["key_threats"]:
                    print(f"   • {threat}")
            
            if enemy_items_analysis["fed_enemies"]:
                print(f"\n🔥 ENNEMIS FED:")
                for enemy in enemy_items_analysis["fed_enemies"]:
                    print(f"   • {enemy}")
            
            # Adapter la recommandation de build
            adaptive_build = self._adapt_build_to_game_state(
                build, 
                enemy_items_analysis,
                my_champion
            )
            
            if adaptive_build.get('updated_notes'):
                print(f"\n📝 AJUSTEMENTS SELON LE JEU:")
                for note in adaptive_build['updated_notes']:
                    print(f"   {note}")
            
            if adaptive_build.get('warnings'):
                print(f"\n⚠️ ALERTES MISES À JOUR:")
                for w in adaptive_build['warnings']:
                    print(f"   {w}")
            
            # Show prioritized build sequence
            if adaptive_build.get('priority_sequence'):
                print(f"\n📋 ORDRE DE BUILD (adapté au jeu actuel):")
                for seq in adaptive_build['priority_sequence']:
                    print(f"   {seq['step']}. {seq['item']}")
                    print(f"      └─ {seq['reason']}")
            
            boots = adaptive_build.get('boots', {})
            if boots and boots.get('name'):
                print(f"\n🥾 BOTTES: {boots.get('name', 'N/A')}")
                print(f"   → {boots.get('why', 'Standard')}")
            
            if adaptive_build.get('your_best_items'):
                print(f"\n📊 Tes items avec le meilleur WR sur {my_champion}:")
                for item in adaptive_build['your_best_items'][:3]:
                    print(f"      • {item.get('name', 'Unknown')}: {item.get('winrate', 0)}%")
            
            anti_heal = adaptive_build.get('anti_heal')
            if anti_heal:
                when_text = anti_heal.get('when', 'Quand nécessaire')
                if "Optionnel" in when_text:
                    print(f"\n🟡 ANTI-HEAL (optionnel): {anti_heal.get('name', 'N/A')}")
                    print(f"   → {anti_heal.get('why', '')}")
                    print(f"   ⏰ {when_text}")
                else:
                    print(f"\n🩹 ANTI-HEAL: {anti_heal.get('name', 'N/A')}")
                    print(f"   → {anti_heal.get('why', '')}")
                    print(f"   ⏰ Acheter: {when_text}")
            
            playstyle = self.stats.get_playstyle_analysis(my_champion)
            if playstyle:
                print(f"\n   🎯 Rappel: Tu es {playstyle['playstyle']} player sur {my_champion}")
                print(f"   💡 {playstyle['tip']}")
    
    def _get_suggested_runes(self, champion, enemy_champions):
        """Retourne les runes suggérées basées sur la composition ennemie"""
        # Heuristiques de runes basiques
        runes = {
            "primary": "Conqueror",
            "secondary": "Precision"
        }
        
        # Analyse simple de la compo ennemie
        if enemy_champions:
            enemy_analysis = self.recommender.analyze_enemy_composition(enemy_champions)
            
            # Si bcp de CC, préférer Unflinching
            if enemy_analysis["cc_heavy"]:
                runes["secondary"] = "Unflinching + Legend: Tenacity"
            
            # Si bcp d'assassins, préférer défensif
            if enemy_analysis["assassin_count"] >= 2:
                runes["primary"] = "Fleet Footwork"
            
            # Si bcp d'AP, Magic Resist
            if enemy_analysis["ap_damage"] >= 3:
                runes["secondary"] = "Conditioning / Mirror Shell"
        
        return runes
    
    def _analyze_enemy_items(self, game, my_team_id):
        """Analyse les items actuels des ennemis et détecte les menaces"""
        analysis = {
            "key_threats": [],
            "fed_enemies": [],
            "enemy_builds": {},
            "gold_deficit": 0
        }
        
        my_total_gold = 0
        enemy_total_gold = 0
        
        # Analyser items et or pour chaque ennemi
        for p in game.get("participants", []):
            if p.get("teamId") == my_team_id:
                my_total_gold += p.get("goldEarned", 0)
            else:
                champion = self.api.get_champion_name(p.get("championId"))
                gold = p.get("goldEarned", 0)
                enemy_total_gold += gold
                
                # Items de l'ennemi
                items = []
                for i in range(6):
                    item_id = p.get(f"item{i}", 0)
                    if item_id > 0:
                        items.append(item_id)
                
                analysis["enemy_builds"][champion] = {
                    "items": items,
                    "gold": gold,
                    "kills": p.get("kills", 0),
                    "deaths": p.get("deaths", 0)
                }
                
                # Détecter si ennemi est fed
                if p.get("kills", 0) >= 5:
                    analysis["fed_enemies"].append(f"{champion} ({p.get('kills')}K/{p.get('deaths')}D)")
                
                # Détecter les menaces principales (items dangereux)
                if items:
                    # Vérifier items offensifs key
                    if 6672 in items or 6673 in items:  # Kraken/Shieldbow
                        analysis["key_threats"].append(f"{champion} a Kraken/Shieldbow → Dégâts massifs")
                    if 3031 in items:  # Infinity Edge
                        analysis["key_threats"].append(f"{champion} a Infinity Edge → Crits dévastateurs")
                    if 3089 in items:  # Rapid Firecannon
                        analysis["key_threats"].append(f"{champion} a RFC → Range étendue")
                    if 6662 in items:  # Iceborn
                        analysis["key_threats"].append(f"{champion} a Iceborn → CC + dégâts")
        
        # Calculer le déficit d'or
        analysis["gold_deficit"] = my_total_gold - enemy_total_gold
        
        return analysis
    
    def _adapt_build_to_game_state(self, base_build, enemy_analysis, my_champion):
        """Adapte les recommandations en fonction de l'état actuel du jeu"""
        adaptive_build = dict(base_build)
        adaptive_build["updated_notes"] = []
        adaptive_build["warnings"] = list(base_build.get("warnings", []))
        
        # 1. Si en déficit d'or → priorité survie
        if enemy_analysis["gold_deficit"] < -1000:
            adaptive_build["updated_notes"].append("⚠️ Déficit d'or détecté! Priorité défense!")
            # Modifier la séquence de priorité
            adaptive_build["priority_sequence"] = self._reorder_priority_defensive(
                adaptive_build.get("priority_sequence", [])
            )
        
        # 2. Si beaucoup d'ennemis fed → items défensifs prioritaires
        if len(enemy_analysis["fed_enemies"]) >= 2:
            adaptive_build["updated_notes"].append("🔥 Plusieurs ennemis fed! Build défensif!")
            adaptive_build["warnings"].insert(0, "⚠️ PRIORITÉ À LA SURVIE - Ennemis trop fed!")
        
        # 3. Si enemies ont items offensifs majeurs → anti-items spécifiques
        for enemy, build_info in enemy_analysis["enemy_builds"].items():
            items = build_info.get("items", [])
            
            # Si enemy a Zhonyas → moins important d'avoir Zhonyas toi-même
            if 3157 in items:  # Zhonyas
                adaptive_build["updated_notes"].append(f"💡 {enemy} a Zhonyas → Adapte tes timings d'engage")
            
            # Si enemy a DCap → MR prioritaire
            if 3089 in items:  # DCap
                adaptive_build["updated_notes"].append(f"🔮 {enemy} a Deathcap → MR important!")
            
            # Si enemy a plusieurs items AD → Armor prioritaire
            if sum(1 for i in items if i in [6672, 3031, 6673]) >= 2:
                adaptive_build["updated_notes"].append(f"🛡️ {enemy} stack AD → Priorité Armor!")
        
        return adaptive_build
    
    def _reorder_priority_defensive(self, priority_sequence):
        """Réordonne la priorité pour mettre les items défensifs en avant"""
        defensive_items = []
        offensive_items = []
        
        for seq in priority_sequence:
            item_name = seq.get("item", "").lower()
            if any(x in item_name for x in ["boots", "treads", "cloak", "guardian", "zhonya", "banshee", "spirit", "adaptive"]):
                defensive_items.append(seq)
            else:
                offensive_items.append(seq)
        
        # Réordonner: defensive d'abord, puis offensive
        reordered = defensive_items + offensive_items
        
        # Re-numéroter les steps
        for i, seq in enumerate(reordered, 1):
            seq["step"] = i
        
        return reordered
    def reset_stats(self):
        """Reset les stats avec confirmation"""
        print("\n⚠️  ATTENTION: Cela va SUPPRIMER toutes tes stats!")
        print("   Tes données d'apprentissage seront perdues.")

        confirm = input("\n   Tape 'RESET' pour confirmer: ").strip()

        if confirm == "RESET":
            if os.path.exists(STATS_FILE):
                os.remove(STATS_FILE)
            self.stats = AdvancedStatsManager(self.items_db)
            print("\n✅ Stats réinitialisées!")
        else:
            print("\n❌ Annulé")
    
    def main_menu(self):
        """Menu principal"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            print("\n" + "═" * 80)
            print("                            MENU PRINCIPAL")
            print("═" * 80)
            
            print(f"\n   👤 Connecté: {self.summoner_name}")
            
            total_games = len(self.stats.stats.get("analyzed_matches", []))
            print(f"   📊 Games analysées: {total_games}")
            
            global_stats = self.stats.get_global_stats()
            if global_stats:
                print(f"   🏆 Winrate: {global_stats['winrate']:.1f}% ({global_stats['wins']}W/{global_stats['losses']}L)")
            
            trend = self.stats.get_recent_trend()
            if trend:
                print(f"   📈 Tendance: {trend['trend_text']} | Last 5: {trend['last_5']}")
            
            print("\n   ╔════════════════════════════════════════════════════════════════╗")
            print("   ║  1. 📊 Synchroniser mes stats                                  ║")
            print("   ║  2. 🏆 Voir mes statistiques globales                          ║")
            print("   ║  3. 🔍 Analyse détaillée d'un champion ✨ NOUVEAU              ║")
            print("   ║  4. 🎯 Recommandations de pick + Prédiction                    ║")
            print("   ║  5. 🔴 Détection game en cours + Conseils live                 ║")
            print("   ║  6. 🔄 Rafraîchir mes champions                                ║")
            print("   ║  7. 🗑️  Reset mes stats                                        ║")
            print("   ║  8. 🌐 État de connexion & URLs d'accès Web                    ║")
            print("   ║  9. 🔧 Diagnostic LCU (test de détection)                      ║")
            print("   ║  0. ❌ Quitter                                                 ║")
            print("   ╚════════════════════════════════════════════════════════════════╝")
            
            choice = input("\n👉 Ton choix: ").strip()
            
            if choice == "1":
                count = input("\nCombien de games? (défaut: 30, max: 100): ").strip()
                count = int(count) if count.isdigit() else 30
                count = min(count, 100)
                self.sync_stats(count)
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "2":
                self.show_stats()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "3":
                self.show_champion_details()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "4":
                self.get_recommendations()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "5":
                self.check_live_game()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "6":
                self.champ_mgr.load_my_champions(self.puuid)
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "7":
                self.reset_stats()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "8":
                self.show_connection_status()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "9":
                test_lcu_detection()
                input("\n[Appuie sur Entrée pour continuer...]")
                
            elif choice == "0":
                print("\n👋 GL HF on the Rift!")
                print("   Plus tu joues, plus les recommandations seront précises! 🚀")
                break
            
            else:
                print("❌ Choix invalide")
                time.sleep(1)
    
    def show_connection_status(self):
        """Affiche les URLs d'accès à l'interface Web"""
        import socket
        
        def get_network_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                try:
                    hostname = socket.gethostname()
                    ip = socket.gethostbyname(hostname)
                    return ip
                except Exception:
                    return "127.0.0.1"
        
        network_ip = get_network_ip()
        
        print("\n" + "="*70)
        print(" "*15 + "ACCES WEB - Interface & Mobile")
        print("="*70)
        print()
        
        print("📱 Sur ce PC:")
        print("   http://localhost:5000")
        print()
        print("📱 Sur le même réseau WiFi/Ethernet:")
        print(f"   http://{network_ip}:5000")
        print()
        print("📱 Depuis un téléphone/tablette:")
        print("   1. Connecte-toi au même WiFi")
        print(f"   2. Ouvre: http://{network_ip}:5000")
        print()
        print("🚀 Pour démarrer le serveur:")
        print("   Exécute: python app.py")
        print()
        print("="*70)
    
    def run(self):
        """Lance l'application"""
        if self.connect():
            self.main_menu()


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                              LANCEMENT                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
def test_lcu_detection():
    """Fonction de test pour diagnostiquer les problèmes LCU"""
    print("\n" + "="*70)
    print("🔧 DIAGNOSTIC LCU")
    print("="*70)
    
    api = RiotAPI(API_KEY)
    api.load_all_champions()
    
    print("\n1️⃣ Test détection LCU...")
    print(f"   Port: {api.lcu_port}")
    print(f"   Token: {api.lcu_token[:10]}..." if api.lcu_token else "   Token: None")
    print(f"   Connecté: {'✅' if api.lcu_connected else '❌'}")
    
    if not api.lcu_connected:
        print("\n   ⚠️ LCU non détecté. Assure-toi que:")
        print("      1. League Client est lancé")
        print("      2. Tu es connecté à ton compte")
        print("      3. Le lockfile existe dans le dossier d'installation")
        return
    
    print("\n2️⃣ Test Champion Select...")
    champ_select = api.get_local_champ_select()
    if champ_select:
        print("   ✅ Champion Select actif!")
        print(f"   Alliés: {champ_select.get('my_team', [])}")
        print(f"   Ennemis: {champ_select.get('enemy_team', [])}")
    else:
        print("   ⚪ Pas en champion select")
    
    print("\n3️⃣ Test Live Client (port 2999)...")
    in_game = api.get_local_in_game()
    if in_game:
        print("   ✅ Partie en cours!")
        print(f"   Champion: {in_game.get('my_champion')}")
        print(f"   Temps: {in_game.get('game_time_seconds')}s")
    else:
        print("   ⚪ Pas en partie")
    
    print("\n4️⃣ Test complet get_current_game()...")
    game = api.get_current_game(None)
    if game:
        print(f"   ✅ Détecté: {game.get('phase')}")
    else:
        print("   ⚪ Aucune partie détectée")
    
    print("\n" + "="*70)
    
if __name__ == "__main__":
    try:
        app = LoLCoachAI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Programme interrompu. À plus!")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        print("\n📧 Si le problème persiste, vérifie:")
        print("   1. Ta clé API (expire toutes les 24h)")
        print("   2. Ton pseudo/tag dans config.py")
        print("   3. Ta connexion internet")
        input("\n[Appuie sur Entrée pour quitter...]")

def find_and_read_lockfile(max_retries=10, delay_sec=0.5):
    """
    Tente de trouver et de lire le lockfile LCU avec des retentatives
    pour contrer les problèmes de timing (Champion Select).
    
    Retourne (port, token) ou lève une exception si non trouvé.
    """
    
    # 1. Tentative de trouver le chemin du lockfile via les processus en cours
    lockfile_path = None
    
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.name() == 'LeagueClientUx.exe':
            # On cherche le dossier d'installation dans la ligne de commande
            try:
                for part in proc.cmdline():
                    if 'LeagueClient' in part and 'lockfile' not in part:
                        # Exemple: 'C:\Riot Games\League of Legends\LeagueClient.exe'
                        base_dir = os.path.dirname(os.path.dirname(part.replace('"', '')))
                        lockfile_path = os.path.join(base_dir, 'lockfile')
                        break
            except (psutil.AccessDenied, IndexError):
                continue
        if lockfile_path:
            break
            
    # 2. Si le chemin est toujours inconnu, on ne peut pas continuer
    if not lockfile_path:
        # Si LCU_LOCKFILE est renseigné dans config.py, on utilise ça
        if LCU_LOCKFILE:
            lockfile_path = LCU_LOCKFILE
        else:
            raise FileNotFoundError("Impossible de localiser le processus ou le chemin du lockfile LCU.")


    # 3. Boucle de Retentative (le fix pour le Champion Select)
    for i in range(max_retries):
        try:
            with open(lockfile_path, 'r') as f:
                content = f.read()
            
            # Le format est "NomProcessus:PID:Port:Token:Protocole"
            match = re.match(r'^.+?:.+?:(\d+):([a-zA-Z0-9_-]+):.+?$', content)
            
            if match:
                port = match.group(1)
                token = match.group(2)
                return port, token
                
        except FileNotFoundError:
            # Le fichier n'existe pas encore ou a été supprimé temporairement.
            pass
        except Exception as e:
            # Erreur de lecture, etc.
            print(f"Erreur de lecture LCU (Tentative {i+1}): {e}")
        
        # Attendre avant la prochaine tentative (essentiel pour le Pick/Ban)
        time.sleep(delay_sec)
        
    raise Exception(f"Impossible de lire le lockfile LCU après {max_retries} tentatives.")