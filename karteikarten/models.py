"""Models for Karteikarten application."""
import json
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User


class Schulfach(models.Model):
    """School subject (Deutsch, Mathematik, etc.)."""

    name = models.CharField(max_length=50, unique=True)
    beschreibung = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Schulfach'
        verbose_name_plural = 'Schulfächer'

    def __str__(self):
        return self.name


class Jahrgangsstufe(models.Model):
    """Grade level (5-13)."""

    stufe = models.IntegerField(unique=True)
    bezeichnung = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['stufe']
        verbose_name = 'Jahrgangsstufe'
        verbose_name_plural = 'Jahrgangsstufen'

    def __str__(self):
        if self.bezeichnung:
            return f"{self.stufe}. Klasse ({self.bezeichnung})"
        return f"{self.stufe}. Klasse"


class Lehrwerk(models.Model):
    """A textbook/course book (e.g., À plus!, Green Line, Access)."""

    name = models.CharField(max_length=100)
    band = models.CharField(max_length=20, blank=True, help_text="Band/Ausgabe (z.B. '2', 'Oberstufe')")
    verlag = models.CharField(max_length=100, blank=True)
    schulfach = models.ForeignKey(
        Schulfach,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lehrwerke'
    )
    jahrgangsstufe = models.ForeignKey(
        Jahrgangsstufe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lehrwerke'
    )
    sprachen = models.JSONField(
        default=list,
        blank=True,
        help_text="Sprachen [Fremdsprache, Muttersprache]"
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'band']
        verbose_name = 'Lehrwerk'
        verbose_name_plural = 'Lehrwerke'
        unique_together = ['name', 'band']

    def __str__(self):
        if self.band:
            return f"{self.name} Band {self.band}"
        return self.name

    @property
    def anzahl_units(self):
        return self.units.count()

    @property
    def anzahl_karten(self):
        return sum(block.anzahl_karten for unit in self.units.all() for block in unit.lernbloecke.all())


class LehrwerkUnit(models.Model):
    """A unit/chapter within a textbook (e.g., Unité 1, Unit 4)."""

    lehrwerk = models.ForeignKey(
        Lehrwerk,
        on_delete=models.CASCADE,
        related_name='units'
    )
    name = models.CharField(max_length=100, help_text="z.B. 'Unité 1', 'Unit 4', 'Kapitel 3'")
    beschreibung = models.TextField(blank=True)
    reihenfolge = models.IntegerField(default=0, help_text="Sortierreihenfolge")

    class Meta:
        ordering = ['lehrwerk', 'reihenfolge', 'name']
        verbose_name = 'Lehrwerk-Unit'
        verbose_name_plural = 'Lehrwerk-Units'
        unique_together = ['lehrwerk', 'name']

    def __str__(self):
        return f"{self.lehrwerk} - {self.name}"

    @property
    def anzahl_bloecke(self):
        return self.lernbloecke.count()

    @property
    def anzahl_karten(self):
        return sum(block.anzahl_karten for block in self.lernbloecke.all())


class Lernblock(models.Model):
    """A collection of flashcards on a specific topic."""

    name = models.CharField(max_length=100)
    beschreibung = models.TextField(blank=True)
    thema = models.CharField(
        max_length=100,
        blank=True,
        help_text="Übergeordnetes Thema (z.B. Gedichtsinterpretation)"
    )

    # Legacy fields (for backwards compatibility)
    schulfach = models.ForeignKey(
        Schulfach,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lernbloecke'
    )
    jahrgangsstufe = models.ForeignKey(
        Jahrgangsstufe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lernbloecke'
    )
    lehrbuch = models.CharField(
        max_length=200,
        blank=True,
        help_text="Legacy: Angabe des Lehrbuchs (deprecated, use lehrwerk_unit)"
    )

    # New hierarchical structure
    lehrwerk_unit = models.ForeignKey(
        LehrwerkUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lernbloecke',
        help_text="Zugehörige Unit im Lehrwerk"
    )

    bidirektional = models.BooleanField(
        default=False,
        help_text="Auch rückwärts lernen (Definition → Begriff)"
    )

    # Field customization (stored as JSON)
    feld_konfiguration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Anpassung der Feldbezeichnungen"
    )

    # Import tracking
    import_quelle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Quelldatei des Imports"
    )
    import_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA256-Hash der Quelldatei für Duplikaterkennung"
    )

    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Lernblock'
        verbose_name_plural = 'Lernblöcke'

    def __str__(self):
        if self.lehrwerk_unit:
            return f"{self.lehrwerk_unit.lehrwerk} - {self.lehrwerk_unit.name} - {self.name}"
        return self.name

    @property
    def anzahl_karten(self):
        """Total number of cards in this block."""
        return self.karten.count()

    @property
    def faellige_karten(self):
        """Number of cards due for review today."""
        return self.karten.filter(naechste_wiederholung__lte=date.today()).count()

    def karten_pro_fach(self):
        """Distribution of cards across Leitner boxes."""
        result = {i: 0 for i in range(1, 6)}
        for karte in self.karten.all():
            result[karte.fach] += 1
        return result

    @property
    def vorderseite_label(self):
        """Label for the front of cards."""
        return self.feld_konfiguration.get('vorderseite', 'Begriff')

    @property
    def rueckseite_label(self):
        """Label for the back of cards."""
        return self.feld_konfiguration.get('rueckseite', 'Definition')

    # Computed properties for display
    @property
    def display_schulfach(self):
        """Get Schulfach from unit hierarchy or direct link."""
        if self.lehrwerk_unit and self.lehrwerk_unit.lehrwerk.schulfach:
            return self.lehrwerk_unit.lehrwerk.schulfach
        return self.schulfach

    @property
    def display_jahrgangsstufe(self):
        """Get Jahrgangsstufe from unit hierarchy or direct link."""
        if self.lehrwerk_unit and self.lehrwerk_unit.lehrwerk.jahrgangsstufe:
            return self.lehrwerk_unit.lehrwerk.jahrgangsstufe
        return self.jahrgangsstufe

    @property
    def display_seiten(self):
        """Get page range from cards (e.g., '192-194')."""
        seiten = self.karten.exclude(seite='').values_list('seite', flat=True)
        if not seiten:
            return None
        # Parse page numbers and find min/max
        alle_seiten = []
        for s in seiten:
            # Handle ranges like "192-194" and single pages like "192"
            if '-' in s:
                try:
                    start, end = s.split('-')
                    alle_seiten.extend(range(int(start.strip()), int(end.strip()) + 1))
                except (ValueError, AttributeError):
                    pass
            else:
                try:
                    alle_seiten.append(int(s.strip()))
                except (ValueError, AttributeError):
                    pass
        if not alle_seiten:
            return None
        min_seite = min(alle_seiten)
        max_seite = max(alle_seiten)
        if min_seite == max_seite:
            return str(min_seite)
        return f"{min_seite}-{max_seite}"


class Karteikarte(models.Model):
    """A single flashcard with front (Begriff) and back (Definition)."""

    LEITNER_INTERVALLE = {
        1: 1,   # Fach 1: täglich
        2: 2,   # Fach 2: alle 2 Tage
        3: 4,   # Fach 3: alle 4 Tage
        4: 7,   # Fach 4: alle 7 Tage
        5: 14,  # Fach 5: alle 14 Tage
    }

    lernblock = models.ForeignKey(
        Lernblock,
        on_delete=models.CASCADE,
        related_name='karten'
    )
    begriff = models.CharField(max_length=500)  # Increased for longer terms
    definition = models.TextField()

    # Flexible example storage (can be string or JSON object)
    beispiele = models.TextField(blank=True, help_text="Anwendungsbeispiele")
    beispiel_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Strukturierte Beispiele {fr: '...', de: '...'}"
    )

    # Legacy zusatz fields
    zusatz_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Name des Zusatzfeldes (z.B. 'Herkunft', 'Synonym')"
    )
    zusatz_wert = models.TextField(
        blank=True,
        help_text="Inhalt des Zusatzfeldes"
    )

    # New flexible zusatz as JSON
    zusatz_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Beliebige Zusatzinformationen als JSON"
    )

    # Tags for filtering
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags für Filterung"
    )

    # Book reference
    seite = models.CharField(
        max_length=20,
        blank=True,
        help_text="Seitenzahl im Lehrbuch"
    )

    fach = models.IntegerField(
        default=1,
        choices=[(i, f"Fach {i}") for i in range(1, 6)]
    )
    naechste_wiederholung = models.DateField(default=date.today)
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['begriff']
        verbose_name = 'Karteikarte'
        verbose_name_plural = 'Karteikarten'
        unique_together = ['lernblock', 'begriff']

    def __str__(self):
        return f"{self.begriff} ({self.lernblock.name})"

    def richtig_beantwortet(self):
        """Move card to next box (max 5) and update review date."""
        if self.fach < 5:
            self.fach += 1
        intervall = self.LEITNER_INTERVALLE[self.fach]
        self.naechste_wiederholung = date.today() + timedelta(days=intervall)
        self.save()

        # Record result
        Lernergebnis.objects.create(
            karte=self,
            richtig=True
        )

    def falsch_beantwortet(self):
        """Move card back to box 1 and set review for today (immediately available)."""
        self.fach = 1
        self.naechste_wiederholung = date.today()  # Sofort wieder verfuegbar
        self.save()

        # Record result
        Lernergebnis.objects.create(
            karte=self,
            richtig=False
        )

    @property
    def ist_faellig(self):
        """Check if card is due for review."""
        return self.naechste_wiederholung <= date.today()

    @property
    def beispiel_display(self):
        """Get display-ready example (from JSON or text)."""
        if self.beispiel_json:
            return self.beispiel_json
        return self.beispiele

    @property
    def zusatz_display(self):
        """Get all zusatz info (merged from legacy and JSON)."""
        result = dict(self.zusatz_json) if self.zusatz_json else {}
        if self.zusatz_label and self.zusatz_wert:
            result[self.zusatz_label] = self.zusatz_wert
        return result


class ImportLog(models.Model):
    """Log of imported JSON files."""

    STATUS_CHOICES = [
        ('success', 'Erfolgreich'),
        ('error', 'Fehler'),
        ('skipped', 'Übersprungen (bereits importiert)'),
    ]

    dateiname = models.CharField(max_length=255)
    dateipfad = models.CharField(max_length=500)
    datei_hash = models.CharField(max_length=64, help_text="SHA256-Hash der Datei")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    nachricht = models.TextField(blank=True)
    lehrwerk = models.ForeignKey(
        Lehrwerk,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_logs'
    )
    anzahl_karten = models.IntegerField(default=0)
    anzahl_bloecke = models.IntegerField(default=0)
    importiert_am = models.DateTimeField(auto_now_add=True)
    archiv_pfad = models.CharField(max_length=500, blank=True, help_text="Pfad zur archivierten Datei")

    class Meta:
        ordering = ['-importiert_am']
        verbose_name = 'Import-Log'
        verbose_name_plural = 'Import-Logs'

    def __str__(self):
        return f"{self.dateiname} ({self.status}) - {self.importiert_am}"


class Lernergebnis(models.Model):
    """Individual learning result for statistics."""

    MODUS_CHOICES = [
        ('klassisch', 'Klassisch'),
        ('rueckwaerts', 'Rückwärts'),
        ('multiple_choice', 'Multiple Choice'),
    ]

    benutzer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lernergebnisse',
        null=True,
        blank=True
    )
    karte = models.ForeignKey(
        Karteikarte,
        on_delete=models.CASCADE,
        related_name='ergebnisse'
    )
    modus = models.CharField(
        max_length=20,
        choices=MODUS_CHOICES,
        default='klassisch'
    )
    richtig = models.BooleanField()
    zeitstempel = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-zeitstempel']
        verbose_name = 'Lernergebnis'
        verbose_name_plural = 'Lernergebnisse'

    def __str__(self):
        status = "richtig" if self.richtig else "falsch"
        return f"{self.karte.begriff}: {status}"


class TagesStatistik(models.Model):
    """Daily statistics per learning block (per user)."""

    benutzer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tagesstatistiken',
        null=True,
        blank=True
    )
    lernblock = models.ForeignKey(
        Lernblock,
        on_delete=models.CASCADE,
        related_name='tagesstatistiken'
    )
    datum = models.DateField(default=date.today)
    gelernt = models.IntegerField(default=0)
    richtig = models.IntegerField(default=0)
    falsch = models.IntegerField(default=0)

    class Meta:
        ordering = ['-datum']
        verbose_name = 'Tagesstatistik'
        verbose_name_plural = 'Tagesstatistiken'
        unique_together = ['benutzer', 'lernblock', 'datum']

    def __str__(self):
        return f"{self.lernblock.name} - {self.datum}"

    @property
    def erfolgsquote(self):
        """Success rate as percentage."""
        total = self.richtig + self.falsch
        if total == 0:
            return 0
        return round((self.richtig / total) * 100)


class GlobaleStatistik(models.Model):
    """Global statistics (streak, etc.)."""

    letzter_lerntag = models.DateField(null=True, blank=True)
    streak = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Globale Statistik'
        verbose_name_plural = 'Globale Statistik'

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def update_streak(self):
        """Update streak based on learning activity."""
        heute = date.today()

        if self.letzter_lerntag is None:
            self.streak = 1
        elif self.letzter_lerntag == heute:
            pass  # Already learned today
        elif self.letzter_lerntag == heute - timedelta(days=1):
            self.streak += 1
        else:
            self.streak = 1  # Streak broken

        self.letzter_lerntag = heute
        self.save()


# =============================================================================
# User-specific models
# =============================================================================

class BenutzerLernblock(models.Model):
    """Junction table: which learning blocks a user has selected."""

    benutzer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lernbloecke'
    )
    lernblock = models.ForeignKey(
        Lernblock,
        on_delete=models.CASCADE,
        related_name='benutzer_zuordnungen'
    )
    hinzugefuegt_am = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['benutzer', 'lernblock']
        verbose_name = 'Benutzer-Lernblock'
        verbose_name_plural = 'Benutzer-Lernblöcke'

    def __str__(self):
        return f"{self.benutzer.username} → {self.lernblock.name}"


class BenutzerKarteStatus(models.Model):
    """Per-user card status for Leitner system."""

    LEITNER_INTERVALLE = {
        1: 1,   # Fach 1: täglich
        2: 2,   # Fach 2: alle 2 Tage
        3: 4,   # Fach 3: alle 4 Tage
        4: 7,   # Fach 4: alle 7 Tage
        5: 14,  # Fach 5: alle 14 Tage
    }

    benutzer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='karten_status'
    )
    karte = models.ForeignKey(
        Karteikarte,
        on_delete=models.CASCADE,
        related_name='benutzer_status'
    )
    fach = models.IntegerField(
        default=1,
        choices=[(i, f"Fach {i}") for i in range(1, 6)]
    )
    naechste_wiederholung = models.DateField(default=date.today)

    class Meta:
        unique_together = ['benutzer', 'karte']
        verbose_name = 'Benutzer-Kartenstatus'
        verbose_name_plural = 'Benutzer-Kartenstatus'

    def __str__(self):
        return f"{self.benutzer.username}: {self.karte.begriff} (Fach {self.fach})"

    @property
    def ist_faellig(self):
        """Check if card is due for review."""
        return self.naechste_wiederholung <= date.today()

    def richtig_beantwortet(self):
        """Move card to next box (max 5) and update review date."""
        if self.fach < 5:
            self.fach += 1
        intervall = self.LEITNER_INTERVALLE[self.fach]
        self.naechste_wiederholung = date.today() + timedelta(days=intervall)
        self.save()

    def falsch_beantwortet(self):
        """Move card back to box 1 and set review for today (immediately available)."""
        self.fach = 1
        self.naechste_wiederholung = date.today()  # Sofort wieder verfuegbar
        self.save()

    @classmethod
    def get_or_create_for_user(cls, benutzer, karte):
        """Get or create status for a user-card combination."""
        status, created = cls.objects.get_or_create(
            benutzer=benutzer,
            karte=karte,
            defaults={
                'fach': 1,
                'naechste_wiederholung': date.today()
            }
        )
        return status


class BenutzerStatistik(models.Model):
    """Per-user statistics and profile settings."""

    benutzer = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='statistik'
    )
    # Profile settings
    bevorzugte_jahrgangsstufe = models.ForeignKey(
        Jahrgangsstufe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='benutzer_bevorzugt',
        help_text="Wird als Standard-Filter vorausgewaehlt"
    )
    # Security
    muss_passwort_aendern = models.BooleanField(
        default=False,
        help_text="Benutzer muss beim naechsten Login sein Passwort aendern"
    )
    # Statistics
    letzter_lerntag = models.DateField(null=True, blank=True)
    streak = models.IntegerField(default=0)
    gesamt_gelernt = models.IntegerField(default=0)
    gesamt_richtig = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Benutzerstatistik'
        verbose_name_plural = 'Benutzerstatistiken'

    def __str__(self):
        return f"Statistik: {self.benutzer.username}"

    @classmethod
    def get_or_create_for_user(cls, benutzer):
        """Get or create statistics for a user."""
        stats, _ = cls.objects.get_or_create(benutzer=benutzer)
        return stats

    def update_streak(self):
        """Update streak based on learning activity."""
        heute = date.today()

        if self.letzter_lerntag is None:
            self.streak = 1
        elif self.letzter_lerntag == heute:
            pass  # Already learned today
        elif self.letzter_lerntag == heute - timedelta(days=1):
            self.streak += 1
        else:
            self.streak = 1  # Streak broken

        self.letzter_lerntag = heute
        self.save()

    @property
    def erfolgsquote(self):
        """Success rate as percentage."""
        if self.gesamt_gelernt == 0:
            return 0
        return round((self.gesamt_richtig / self.gesamt_gelernt) * 100)
