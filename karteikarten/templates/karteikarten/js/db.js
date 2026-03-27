/**
 * IndexedDB Wrapper für Karteikarten Offline-Speicherung
 */

const DB_NAME = 'karteikarten-db';
const DB_VERSION = 1;

class KarteikartenDB {
    constructor() {
        this.db = null;
        this.ready = this.init();
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Lernblöcke
                if (!db.objectStoreNames.contains('lernbloecke')) {
                    const lernbloeckeStore = db.createObjectStore('lernbloecke', { keyPath: 'id' });
                    lernbloeckeStore.createIndex('name', 'name', { unique: false });
                }

                // Karteikarten
                if (!db.objectStoreNames.contains('karten')) {
                    const kartenStore = db.createObjectStore('karten', { keyPath: 'id' });
                    kartenStore.createIndex('lernblock_id', 'lernblock_id', { unique: false });
                }

                // Benutzer-Karten-Status (Lernfortschritt)
                if (!db.objectStoreNames.contains('kartenstatus')) {
                    const statusStore = db.createObjectStore('kartenstatus', { keyPath: 'karte_id' });
                    statusStore.createIndex('naechste_wiederholung', 'naechste_wiederholung', { unique: false });
                }

                // Sync-Queue für Offline-Antworten
                if (!db.objectStoreNames.contains('sync_queue')) {
                    const syncStore = db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Metadaten (letzter Sync, etc.)
                if (!db.objectStoreNames.contains('meta')) {
                    db.createObjectStore('meta', { keyPath: 'key' });
                }
            };
        });
    }

    async ensureReady() {
        if (!this.db) {
            await this.ready;
        }
        return this.db;
    }

    // === LERNBLÖCKE ===

    async saveLernbloecke(lernbloecke) {
        const db = await this.ensureReady();
        const tx = db.transaction('lernbloecke', 'readwrite');
        const store = tx.objectStore('lernbloecke');

        for (const block of lernbloecke) {
            store.put(block);
        }

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async getLernbloecke() {
        const db = await this.ensureReady();
        const tx = db.transaction('lernbloecke', 'readonly');
        const store = tx.objectStore('lernbloecke');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getLernblock(id) {
        const db = await this.ensureReady();
        const tx = db.transaction('lernbloecke', 'readonly');
        const store = tx.objectStore('lernbloecke');

        return new Promise((resolve, reject) => {
            const request = store.get(id);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // === KARTEIKARTEN ===

    async saveKarten(karten) {
        const db = await this.ensureReady();
        const tx = db.transaction('karten', 'readwrite');
        const store = tx.objectStore('karten');

        for (const karte of karten) {
            store.put(karte);
        }

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async getKartenByLernblock(lernblockId) {
        const db = await this.ensureReady();
        const tx = db.transaction('karten', 'readonly');
        const store = tx.objectStore('karten');
        const index = store.index('lernblock_id');

        return new Promise((resolve, reject) => {
            const request = index.getAll(lernblockId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getKarte(id) {
        const db = await this.ensureReady();
        const tx = db.transaction('karten', 'readonly');
        const store = tx.objectStore('karten');

        return new Promise((resolve, reject) => {
            const request = store.get(id);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllKarten() {
        const db = await this.ensureReady();
        const tx = db.transaction('karten', 'readonly');
        const store = tx.objectStore('karten');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // === KARTEN-STATUS ===

    async saveKartenStatus(statusList) {
        const db = await this.ensureReady();
        const tx = db.transaction('kartenstatus', 'readwrite');
        const store = tx.objectStore('kartenstatus');

        for (const status of statusList) {
            store.put(status);
        }

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async getKarteStatus(karteId) {
        const db = await this.ensureReady();
        const tx = db.transaction('kartenstatus', 'readonly');
        const store = tx.objectStore('kartenstatus');

        return new Promise((resolve, reject) => {
            const request = store.get(karteId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateKarteStatus(karteId, richtig) {
        const db = await this.ensureReady();
        let status = await this.getKarteStatus(karteId);

        const heute = new Date().toISOString().split('T')[0];

        if (!status) {
            status = {
                karte_id: karteId,
                fach: 1,
                naechste_wiederholung: heute
            };
        }

        // Leitner-System: Fächer 1-5
        const intervalle = [1, 2, 4, 7, 14]; // Tage pro Fach

        if (richtig) {
            status.fach = Math.min(5, status.fach + 1);
        } else {
            status.fach = 1;
        }

        // Nächste Wiederholung berechnen
        const naechsteDatum = new Date();
        naechsteDatum.setDate(naechsteDatum.getDate() + intervalle[status.fach - 1]);
        status.naechste_wiederholung = naechsteDatum.toISOString().split('T')[0];

        const tx = db.transaction('kartenstatus', 'readwrite');
        const store = tx.objectStore('kartenstatus');
        store.put(status);

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve(status);
            tx.onerror = () => reject(tx.error);
        });
    }

    async getFaelligeKarten(lernblockIds = null) {
        const db = await this.ensureReady();
        const heute = new Date().toISOString().split('T')[0];

        // Alle Karten und Status laden
        let karten = await this.getAllKarten();

        if (lernblockIds && lernblockIds.length > 0) {
            karten = karten.filter(k => lernblockIds.includes(k.lernblock_id));
        }

        const faellige = [];

        for (const karte of karten) {
            const status = await this.getKarteStatus(karte.id);
            const naechsteWiederholung = status?.naechste_wiederholung || '1970-01-01';

            if (naechsteWiederholung <= heute) {
                faellige.push({
                    karte,
                    status: status || { fach: 1, naechste_wiederholung: heute }
                });
            }
        }

        // Zufällig mischen
        return faellige.sort(() => Math.random() - 0.5);
    }

    // === SYNC QUEUE ===

    async addToSyncQueue(action) {
        const db = await this.ensureReady();
        const tx = db.transaction('sync_queue', 'readwrite');
        const store = tx.objectStore('sync_queue');

        action.timestamp = Date.now();
        store.add(action);

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async getSyncQueue() {
        const db = await this.ensureReady();
        const tx = db.transaction('sync_queue', 'readonly');
        const store = tx.objectStore('sync_queue');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async clearSyncQueue() {
        const db = await this.ensureReady();
        const tx = db.transaction('sync_queue', 'readwrite');
        const store = tx.objectStore('sync_queue');
        store.clear();

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async removeSyncItem(id) {
        const db = await this.ensureReady();
        const tx = db.transaction('sync_queue', 'readwrite');
        const store = tx.objectStore('sync_queue');
        store.delete(id);

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    // === METADATEN ===

    async setMeta(key, value) {
        const db = await this.ensureReady();
        const tx = db.transaction('meta', 'readwrite');
        const store = tx.objectStore('meta');
        store.put({ key, value });

        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }

    async getMeta(key) {
        const db = await this.ensureReady();
        const tx = db.transaction('meta', 'readonly');
        const store = tx.objectStore('meta');

        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result?.value);
            request.onerror = () => reject(request.error);
        });
    }

    // === UTILITIES ===

    async clearAll() {
        const db = await this.ensureReady();
        const stores = ['lernbloecke', 'karten', 'kartenstatus', 'sync_queue', 'meta'];

        for (const storeName of stores) {
            const tx = db.transaction(storeName, 'readwrite');
            tx.objectStore(storeName).clear();
            await new Promise((resolve) => { tx.oncomplete = resolve; });
        }
    }
}

// Globale Instanz
window.karteikartenDB = new KarteikartenDB();
