/**
 * Synchronisations-Logik für Offline/Online-Betrieb
 */

class KarteikartenSync {
    constructor() {
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;

        // Online/Offline Event Listener
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Initiale Sync wenn online
        if (this.isOnline) {
            this.syncFromServer();
        }
    }

    handleOnline() {
        this.isOnline = true;
        console.log('Online - starte Synchronisation...');
        this.showStatus('online', 'Verbindung hergestellt - synchronisiere...');
        this.syncAll();
    }

    handleOffline() {
        this.isOnline = false;
        console.log('Offline - lokaler Modus aktiv');
        this.showStatus('offline', 'Offline-Modus aktiv');
    }

    showStatus(type, message) {
        // Status-Anzeige in der UI
        let statusEl = document.getElementById('sync-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'sync-status';
            statusEl.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 9999;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;
            document.body.appendChild(statusEl);
        }

        statusEl.className = type;
        statusEl.textContent = message;

        if (type === 'online') {
            statusEl.style.background = '#10B981';
            statusEl.style.color = 'white';
        } else if (type === 'offline') {
            statusEl.style.background = '#F59E0B';
            statusEl.style.color = 'white';
        } else if (type === 'syncing') {
            statusEl.style.background = '#3B82F6';
            statusEl.style.color = 'white';
        } else if (type === 'error') {
            statusEl.style.background = '#EF4444';
            statusEl.style.color = 'white';
        }

        // Auto-hide nach 3 Sekunden (außer bei offline)
        if (type !== 'offline' && type !== 'syncing') {
            setTimeout(() => {
                statusEl.style.opacity = '0';
                setTimeout(() => statusEl.remove(), 300);
            }, 3000);
        }
    }

    async syncAll() {
        if (this.syncInProgress || !this.isOnline) return;

        this.syncInProgress = true;
        this.showStatus('syncing', 'Synchronisiere...');

        try {
            // 1. Erst lokale Änderungen hochladen
            await this.pushToServer();

            // 2. Dann aktuelle Daten vom Server holen
            await this.syncFromServer();

            this.showStatus('online', 'Synchronisation abgeschlossen');
        } catch (error) {
            console.error('Sync-Fehler:', error);
            this.showStatus('error', 'Synchronisation fehlgeschlagen');
        } finally {
            this.syncInProgress = false;
        }
    }

    async syncFromServer() {
        if (!this.isOnline) return;

        try {
            const response = await fetch('/api/sync/pull/', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Daten lokal speichern
            if (data.lernbloecke) {
                await window.karteikartenDB.saveLernbloecke(data.lernbloecke);
            }
            if (data.karten) {
                await window.karteikartenDB.saveKarten(data.karten);
            }
            if (data.status) {
                await window.karteikartenDB.saveKartenStatus(data.status);
            }

            // Letzten Sync-Zeitpunkt speichern
            await window.karteikartenDB.setMeta('lastSync', Date.now());

            console.log('Sync vom Server abgeschlossen:', {
                lernbloecke: data.lernbloecke?.length || 0,
                karten: data.karten?.length || 0,
                status: data.status?.length || 0
            });

        } catch (error) {
            console.error('Fehler beim Sync vom Server:', error);
            throw error;
        }
    }

    async pushToServer() {
        if (!this.isOnline) return;

        const queue = await window.karteikartenDB.getSyncQueue();

        if (queue.length === 0) {
            console.log('Keine lokalen Änderungen zum Hochladen');
            return;
        }

        console.log(`${queue.length} Änderungen zum Hochladen...`);

        for (const item of queue) {
            try {
                const response = await fetch('/api/sync/push/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify(item)
                });

                if (response.ok) {
                    await window.karteikartenDB.removeSyncItem(item.id);
                    console.log('Sync-Item erfolgreich hochgeladen:', item.id);
                } else {
                    console.error('Fehler beim Hochladen von Sync-Item:', item.id, response.status);
                }
            } catch (error) {
                console.error('Netzwerk-Fehler beim Hochladen:', error);
                // Bei Netzwerk-Fehler abbrechen
                break;
            }
        }
    }

    getCSRFToken() {
        const cookie = document.cookie
            .split(';')
            .find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    // Antwort speichern (online oder offline)
    async saveAntwort(karteId, richtig, modus = 'klassisch') {
        // Lokalen Status aktualisieren
        const neuerStatus = await window.karteikartenDB.updateKarteStatus(karteId, richtig);

        if (this.isOnline) {
            // Direkt an Server senden
            try {
                const response = await fetch(`/api/karte/${karteId}/antwort/`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: `richtig=${richtig}&modus=${modus}`
                });

                if (!response.ok) {
                    throw new Error('Server-Fehler');
                }
            } catch (error) {
                // Bei Fehler in Queue speichern
                console.log('Server nicht erreichbar, speichere in Queue');
                await this.queueAntwort(karteId, richtig, modus);
            }
        } else {
            // Offline: In Queue speichern
            await this.queueAntwort(karteId, richtig, modus);
        }

        return neuerStatus;
    }

    async queueAntwort(karteId, richtig, modus) {
        await window.karteikartenDB.addToSyncQueue({
            type: 'antwort',
            karte_id: karteId,
            richtig: richtig,
            modus: modus,
            timestamp: Date.now()
        });
        console.log('Antwort in Sync-Queue gespeichert');
    }

    // Prüfen ob Offline-Daten verfügbar sind
    async hasOfflineData() {
        const karten = await window.karteikartenDB.getAllKarten();
        return karten.length > 0;
    }

    // Anzahl ausstehender Sync-Items
    async getPendingSyncCount() {
        const queue = await window.karteikartenDB.getSyncQueue();
        return queue.length;
    }
}

// Globale Instanz
window.karteikartenSync = new KarteikartenSync();
