// LoL Coach AI - Web Frontend
// Détection automatique de parties en cours avec recommandations live

const API_BASE = '/api';

class LoLCoachUI {
    constructor() {
        this.currentGame = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        console.log('Initializing LoL Coach UI...');
        await this.loadStatus();
        this.setupEventListeners();
        this.startLiveGameDetection();
    }

    startLiveGameDetection() {
        // Vérifie les parties toutes les 3 secondes
        this.refreshInterval = setInterval(async () => {
            await this.detectAndShowLiveGame();
        }, 3000);
        
        this.detectAndShowLiveGame();
    }

    async request(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            
            if (data) options.body = JSON.stringify(data);
            
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (err) {
            console.error(`API Error: ${endpoint}`, err);
            throw err;
        }
    }

    async loadStatus() {
        try {
            const status = await this.request('/status');
            document.getElementById('summoner-name').textContent = status.summoner || 'Unknown';
            document.getElementById('games-count').textContent = status.games_analyzed || 0;
            
            const globalStats = await this.request('/stats/global');
            document.getElementById('winrate').textContent = `${globalStats.winrate?.toFixed(1)}%`;
            document.getElementById('wins-losses').textContent = `${globalStats.wins || 0}W / ${globalStats.losses || 0}L`;
        } catch (err) {
            this.showError('Erreur lors du chargement');
        }
    }

    async detectAndShowLiveGame() {
        try {
            const data = await this.request('/live-game');
            const statusEl = document.getElementById('game-detection-status');
            const section = document.getElementById('live-game-section');
            
            if (data.ingame) {
                this.currentGame = data;
                
                if (data.phase === 'champ_select') {
                    statusEl.textContent = '🎪 Champ Select détecté! Composition en cours...';
                    this.showChampSelectRecommendations(data);
                } else if (data.phase === 'in_game') {
                    const mins = Math.floor(data.game_time_seconds / 60);
                    const secs = String(data.game_time_seconds % 60).padStart(2, '0');
                    statusEl.textContent = `🎮 En Jeu - ${data.my_champion} | ${mins}:${secs}`;
                    this.showInGameRecommendations(data);
                }
                
                section.style.display = 'block';
            } else {
                statusEl.textContent = '🔍 En attente d\'une partie...';
                section.style.display = 'none';
                this.currentGame = null;
            }
        } catch (err) {
            document.getElementById('game-detection-status').textContent = '🔍 En attente d\'une partie...';
            document.getElementById('live-game-section').style.display = 'none';
        }
    }

    showChampSelectRecommendations(data) {
        const section = document.getElementById('live-game-section');
        
        let html = `
            <h2>🎪 Champ Select</h2>
            <div class="status-bar">
                <div class="status-card">
                    <h3>👥 Alliés</h3>
                    <div class="value">${data.my_team.length > 0 ? data.my_team.join(', ') : 'En sélection...'}</div>
                </div>
                <div class="status-card">
                    <h3>⚔️ Ennemis</h3>
                    <div class="value">${data.enemy_team.length > 0 ? data.enemy_team.join(', ') : 'En sélection...'}</div>
                </div>
            </div>
        `;
        
        if (data.recommendations && data.recommendations.length > 0) {
            html += '<h3>🎯 Champions recommandés:</h3>';
            html += data.recommendations.slice(0, 5).map((r, i) => `
                <div class="recommendation">
                    <h3>#${i + 1} - ${r.champion}</h3>
                    <div class="detail">📊 WR: <span class="wr">${r.winrate}%</span> (${r.games} parties)</div>
                    <div class="detail">📈 KDA: ${r.kda}</div>
                    ${r.reasons ? r.reasons.slice(0, 2).map(reason => `<div class="detail">• ${reason}</div>`).join('') : ''}
                </div>
            `).join('');
        }
        
        section.innerHTML = html;
    }

    showInGameRecommendations(data) {
        const section = document.getElementById('live-game-section');
        
        let html = `
            <h2>🎮 En Jeu - ${data.my_champion}</h2>
            <div class="status-bar">
                <div class="status-card">
                    <h3>⏱️ Temps</h3>
                    <div class="value">${Math.floor(data.game_time_seconds / 60)}:${String(data.game_time_seconds % 60).padStart(2, '0')}</div>
                </div>
                <div class="status-card">
                    <h3>👥 Alliés</h3>
                    <div class="value">${data.my_team.join(', ')}</div>
                </div>
                <div class="status-card">
                    <h3>⚔️ Ennemis</h3>
                    <div class="value">${data.enemy_team.join(', ')}</div>
                </div>
            </div>
        `;
        
        // Section Items
        if (data.build && data.build.your_best_items) {
            html += '<h3>📊 Items recommandés (adapté à la phase):</h3>';
            html += data.build.your_best_items.slice(0, 4).map(item => `
                <div class="recommendation">
                    <h3>${item.name}</h3>
                    <div class="detail">WR: <span class="wr">${item.winrate}%</span> | ${item.games} parties</div>
                    ${item.reasons ? `<div class="detail">${item.reasons.join(' - ')}</div>` : ''}
                </div>
            `).join('');
            
            if (data.build.anti_heal) {
                html += `<div class="recommendation"><h3>🩹 ${data.build.anti_heal.name}</h3><div class="detail">${data.build.anti_heal.why}</div></div>`;
            }
            if (data.build.boots) {
                html += `<div class="recommendation"><h3>🥾 ${data.build.boots.name}</h3><div class="detail">${data.build.boots.why}</div></div>`;
            }
        }
        
        // Section Runes
        if (data.runes_spells && (data.runes_spells.runes || data.runes_spells.spells)) {
            html += '<h3>⚡ Runes &amp; Spells:</h3>';
            if (data.runes_spells.runes && data.runes_spells.runes.keystone) {
                const r = data.runes_spells.runes.keystone;
                html += `<div class="recommendation"><h3>🔮 Keystone</h3><div class="detail">ID: ${r.id} - WR: ${r.wr}%</div></div>`;
            }
            if (data.runes_spells.spells) {
                const s = data.runes_spells.spells;
                html += `<div class="recommendation"><h3>📞 Spells</h3><div class="detail">${s.primary?.name || 'N/A'} / ${s.secondary?.name || 'N/A'}</div></div>`;
            }
        }
        
        section.innerHTML = html;
    }

    setupEventListeners() {
        document.getElementById('sync-btn')?.addEventListener('click', () => this.syncStats());
        document.getElementById('load-champs-btn')?.addEventListener('click', () => this.loadChampions());
    }

    async syncStats() {
        this.showLoading('Synchronisation en cours...');
        try {
            const result = await this.request('/sync', 'POST', { count: 30 });
            this.showSuccess(`${result.games_analyzed} parties! Total: ${result.total_games}`);
            await this.loadStatus();
        } catch (err) {
            this.showError(`Erreur: ${err.message}`);
        }
    }

    async loadChampions() {
        this.showLoading('Chargement...');
        try {
            const champs = await this.request('/champions');
            const grid = document.getElementById('champions-grid');
            grid.innerHTML = champs.map(c => `
                <div class="champion-card">
                    <h4>${c.name}</h4>
                    <div class="stat">WR: <span class="wr">${c.winrate}%</span></div>
                    <div class="stat">${c.wins}W / ${c.games - c.wins}L</div>
                </div>
            `).join('');
            this.showSuccess('Champions charges!');
        } catch (err) {
            this.showError(`Erreur: ${err.message}`);
        }
    }

    showLoading(message) {
        const alertBox = document.getElementById('alert-box');
        if (alertBox) {
            alertBox.innerHTML = `<div class="loading">${message}</div>`;
            alertBox.style.display = 'block';
        }
    }

    showError(message) {
        const alertBox = document.getElementById('alert-box');
        if (alertBox) {
            alertBox.innerHTML = `<div class="error">❌ ${message}</div>`;
            alertBox.style.display = 'block';
            setTimeout(() => alertBox.style.display = 'none', 5000);
        }
    }

    showSuccess(message) {
        const alertBox = document.getElementById('alert-box');
        if (alertBox) {
            alertBox.innerHTML = `<div class="success-msg">✅ ${message}</div>`;
            alertBox.style.display = 'block';
            setTimeout(() => alertBox.style.display = 'none', 3000);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new LoLCoachUI();
});
