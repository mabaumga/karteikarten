/**
 * Offline-Lernmodus für Karteikarten
 */

class OfflineLearning {
    constructor() {
        this.currentKarten = [];
        this.currentIndex = 0;
        this.stats = { gelernt: 0, richtig: 0, falsch: 0 };
        this.modus = 'klassisch';
        this.isOffline = !navigator.onLine;

        // Event Listener für Online/Offline
        window.addEventListener('online', () => {
            this.isOffline = false;
        });
        window.addEventListener('offline', () => {
            this.isOffline = true;
        });
    }

    async init(lernblockIds = null, modus = 'klassisch') {
        this.modus = modus;
        this.stats = { gelernt: 0, richtig: 0, falsch: 0 };

        // Fällige Karten laden
        this.currentKarten = await window.karteikartenDB.getFaelligeKarten(lernblockIds);
        this.currentIndex = 0;

        return this.currentKarten.length;
    }

    getCurrentKarte() {
        if (this.currentIndex >= this.currentKarten.length) {
            return null;
        }
        return this.currentKarten[this.currentIndex];
    }

    async antworten(richtig) {
        const current = this.getCurrentKarte();
        if (!current) return null;

        // Antwort speichern (lokal und ggf. Server)
        await window.karteikartenSync.saveAntwort(
            current.karte.id,
            richtig,
            this.modus
        );

        // Stats aktualisieren
        this.stats.gelernt++;
        if (richtig) {
            this.stats.richtig++;
        } else {
            this.stats.falsch++;
        }

        this.currentIndex++;

        return {
            verbleibend: this.currentKarten.length - this.currentIndex,
            stats: this.stats,
            fertig: this.currentIndex >= this.currentKarten.length
        };
    }

    getStats() {
        return this.stats;
    }

    getVerbleibend() {
        return this.currentKarten.length - this.currentIndex;
    }
}

// Globale Instanz
window.offlineLearning = new OfflineLearning();


/**
 * UI-Controller für Offline-Lernen
 */
class OfflineLearningUI {
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        this.learning = window.offlineLearning;
    }

    async start(lernblockIds = null, modus = 'klassisch') {
        const count = await this.learning.init(lernblockIds, modus);

        if (count === 0) {
            this.showFertig();
            return;
        }

        this.showKarte();
    }

    showKarte() {
        const data = this.learning.getCurrentKarte();
        if (!data) {
            this.showFertig();
            return;
        }

        const { karte, status } = data;
        const verbleibend = this.learning.getVerbleibend();
        const rueckwaerts = this.learning.modus === 'rueckwaerts';

        // Vorderseite (Begriff oder Definition je nach Modus)
        const vorderseite = rueckwaerts ? karte.definition : karte.begriff;
        const rueckseiteLabel = rueckwaerts ? 'Begriff' : 'Definition';
        const rueckseite = rueckwaerts ? karte.begriff : karte.definition;

        this.container.innerHTML = `
            <div class="mb-3 d-flex justify-content-between align-items-center">
                <span class="badge bg-primary">Fach ${status.fach}</span>
                <span class="text-muted">${verbleibend} Karte${verbleibend !== 1 ? 'n' : ''} übrig</span>
            </div>

            <div class="flashcard mb-4" id="flashcard" onclick="offlineLearningUI.flipCard()">
                <div class="card-front">
                    <div class="begriff">${this.escapeHtml(vorderseite)}</div>
                    <small class="text-muted mt-3">Tippen zum Umdrehen</small>
                </div>
                <div class="card-back" style="display: none;">
                    <div class="definition">${this.escapeHtml(rueckseite)}</div>
                    ${karte.beispiele ? `<div class="beispiele"><i class="bi bi-chat-quote me-1"></i>${this.escapeHtml(karte.beispiele)}</div>` : ''}
                    ${karte.zusatz_label && karte.zusatz_wert ? `<div class="zusatz"><span class="zusatz-label">${this.escapeHtml(karte.zusatz_label)}:</span> ${this.escapeHtml(karte.zusatz_wert)}</div>` : ''}
                </div>
            </div>

            <div class="answer-buttons" style="display: none;">
                <div class="d-grid gap-3">
                    <div class="row g-3">
                        <div class="col-6">
                            <button class="btn btn-danger btn-lg w-100" onclick="offlineLearningUI.antworten(false)">
                                <i class="bi bi-x-lg me-2"></i>Falsch
                            </button>
                        </div>
                        <div class="col-6">
                            <button class="btn btn-success btn-lg w-100" onclick="offlineLearningUI.antworten(true)">
                                <i class="bi bi-check-lg me-2"></i>Richtig
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    flipCard() {
        const front = this.container.querySelector('.card-front');
        const back = this.container.querySelector('.card-back');
        const buttons = this.container.querySelector('.answer-buttons');

        if (front && back && buttons) {
            front.style.display = 'none';
            back.style.display = 'block';
            buttons.style.display = 'block';
        }
    }

    async antworten(richtig) {
        const result = await this.learning.antworten(richtig);

        if (result.fertig) {
            this.showFertig();
        } else {
            this.showKarte();
        }
    }

    showFertig() {
        const stats = this.learning.getStats();
        const quote = stats.gelernt > 0
            ? Math.round((stats.richtig / stats.gelernt) * 100)
            : 0;

        this.container.innerHTML = `
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="bi bi-trophy-fill text-warning" style="font-size: 4rem;"></i>
                </div>
                <h2 class="mb-4">Fertig!</h2>

                <div class="row g-3 mb-4">
                    <div class="col-4">
                        <div class="card">
                            <div class="card-body">
                                <h3 class="text-primary mb-0">${stats.gelernt}</h3>
                                <small class="text-muted">Gelernt</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="card">
                            <div class="card-body">
                                <h3 class="text-success mb-0">${stats.richtig}</h3>
                                <small class="text-muted">Richtig</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="card">
                            <div class="card-body">
                                <h3 class="text-danger mb-0">${stats.falsch}</h3>
                                <small class="text-muted">Falsch</small>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="progress mb-4" style="height: 20px;">
                    <div class="progress-bar bg-success" style="width: ${quote}%">${quote}%</div>
                </div>

                <div class="d-grid gap-2">
                    <a href="/" class="btn btn-primary btn-lg">
                        <i class="bi bi-house me-2"></i>Zum Dashboard
                    </a>
                </div>
            </div>
        `;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Globale UI-Instanz
window.offlineLearningUI = null;

// Initialisierung wenn DOM geladen
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('#offline-learning-container');
    if (container) {
        window.offlineLearningUI = new OfflineLearningUI('#offline-learning-container');
    }
});
