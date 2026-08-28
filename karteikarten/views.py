"""Views for Karteikarten application."""

import csv
import io
import random
from datetime import date
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from .services.antwortpruefung import FAST, RICHTIG, pruefe_antwort
from .services.statistik import (
    block_fortschritt,
    gegliederter_fortschritt,
    kurzfortschritt,
)
from .models import (
    Jahrgangsstufe,
    Lehrwerk,
    LehrwerkUnit,
    Lernblock,
    Schulfach,
    Karteikarte,
    TagesStatistik,
    Lernergebnis,
    BenutzerLernblock,
    BenutzerKarteStatus,
    BenutzerStatistik,
)


def staff_required(view_func):
    """Decorator that requires user to be staff."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


# Farben fuer die Fachmarke links an jeder Blockzeile. Fest zugeordnet ueber den
# Namen: dasselbe Fach soll auf jedem Geraet dieselbe Farbe haben.
def _gewaehlte_bloecke(user):
    """Die Bloecke, die der Benutzer sich ausgesucht hat — sonst keine.

    Einzige Antwort auf diese Frage; Startseite, Fortschritt und "alles zusammen"
    haben sie vorher jeweils selbst gestellt.
    """
    return [
        zuordnung.lernblock
        for zuordnung in BenutzerLernblock.objects.filter(benutzer=user).select_related(
            "lernblock"
        )
    ]


# Umfang des Fortschrittsrings (2 * pi * r bei r = 21) — das Template kann nicht rechnen.
RING_UMFANG = 132

_FACHFARBEN = [
    ("#DBEAFE", "#1D4ED8"),
    ("#FCE7F3", "#9D174D"),
    ("#DCFCE7", "#166534"),
    ("#FEF3C7", "#92400E"),
    ("#EDE9FE", "#5B21B6"),
    ("#CFFAFE", "#155E75"),
]


def _schulfach_marke(lernblock):
    """Kuerzel und Farbe des Schulfachs — die Marke links an der Blockzeile."""
    fach = lernblock.display_schulfach
    if fach is None:
        return {
            "kuerzel": lernblock.name[:2].upper(),
            "farbe": "#E5E7EB",
            "schrift": "#374151",
        }
    hintergrund, schrift = _FACHFARBEN[sum(fach.name.encode()) % len(_FACHFARBEN)]
    return {"kuerzel": fach.name[:2].upper(), "farbe": hintergrund, "schrift": schrift}


def _blockzustand(faellig, anzahl, naechste_faelligkeit):
    """Was in der Blockzeile steht: was ansteht, und wann sonst.

    Drei Zustaende, weil sie sich fuer den Lernenden wirklich unterscheiden:
    heute dran, heute schon geschafft, und erst spaeter wieder faellig.
    """
    if faellig:
        prozent = round(faellig / anzahl * 100) if anzahl else 0
        return {
            "zustand": "faellig",
            "titel": "Heute üben",
            "ring_prozent": prozent,
            "ring_versatz": round(RING_UMFANG * (1 - prozent / 100)),
            "tage_bis_faellig": 0,
        }
    if naechste_faelligkeit is None:
        return {
            "zustand": "leer",
            "titel": "Noch keine Karten",
            "ring_prozent": 0,
            "ring_versatz": RING_UMFANG,
            "tage_bis_faellig": 0,
        }
    tage = (naechste_faelligkeit - date.today()).days
    if tage <= 0:
        tage = 1
    return {
        "zustand": "wartet",
        "titel": "Heute geschafft" if tage == 1 else f"In {tage} Tagen fällig",
        "ring_prozent": 0,
        "ring_versatz": RING_UMFANG,
        "tage_bis_faellig": tage,
    }


@login_required
def dashboard(request):
    """Main dashboard with user's learning blocks."""
    user = request.user

    lernbloecke = _gewaehlte_bloecke(user)

    # Schulfach-Filter. Gemeint ist das Schulfach (Englisch, Franzoesisch), nicht das
    # Leitner-Fach 1-5 — im Code heisst beides "Fach". display_schulfach folgt der
    # Lehrwerk-Hierarchie und ist deshalb eine Python-Property, keine Spalte: die
    # Auswahlliste und der Filter laufen in Python, nicht im ORM.
    schulfaecher = sorted(
        {b.display_schulfach for b in lernbloecke if b.display_schulfach},
        key=lambda fach: fach.name,
    )
    filter_fach = request.GET.get("fach", "")
    if filter_fach.isdigit():
        gewaehltes_fach = int(filter_fach)
        lernbloecke = [
            b
            for b in lernbloecke
            if b.display_schulfach and b.display_schulfach.pk == gewaehltes_fach
        ]
    else:
        filter_fach = ""

    # Get user statistics
    stats = BenutzerStatistik.get_or_create_for_user(user)

    # Kennzahlen und Blockliste in einem Durchgang — der Kartenstatus wurde vorher
    # je Karte zweimal geholt, einmal fuer die Summen und einmal fuer die Liste.
    total_karten = 0
    total_faellig = 0
    bloecke_mit_status = []
    for lernblock in lernbloecke:
        karten = list(lernblock.karten.all())
        faellig = 0
        naechste = None
        for karte in karten:
            karten_status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if karten_status.ist_faellig:
                faellig += 1
            elif naechste is None or karten_status.naechste_wiederholung < naechste:
                naechste = karten_status.naechste_wiederholung
        total_karten += len(karten)
        total_faellig += faellig
        bloecke_mit_status.append(
            {
                "lernblock": lernblock,
                "faellig": faellig,
                "anzahl": len(karten),
                **_blockzustand(faellig, len(karten), naechste),
                **_schulfach_marke(lernblock),
            }
        )

    # Today's results for this user — bei aktivem Filter nur die sichtbaren Bloecke,
    # damit Kennzahlen und Liste dasselbe beschreiben. Der Streak bleibt global: er
    # gehoert zur Person, nicht zum Fach.
    ergebnisse = Lernergebnis.objects.filter(
        benutzer=user, zeitstempel__date=date.today()
    )
    if filter_fach:
        ergebnisse = ergebnisse.filter(karte__lernblock__in=lernbloecke)
    heute_richtig = ergebnisse.filter(richtig=True).count()
    heute_falsch = ergebnisse.filter(richtig=False).count()

    context = {
        "bloecke_mit_status": bloecke_mit_status,
        "streak": stats.streak,
        "total_karten": total_karten,
        "total_faellig": total_faellig,
        "heute_richtig": heute_richtig,
        "heute_falsch": heute_falsch,
        "schulfaecher": schulfaecher,
        "filter_fach": filter_fach,
        "modus": _bevorzugter_modus(user),
    }
    return render(request, "karteikarten/dashboard.html", context)


@login_required
def profil(request):
    """User profile settings."""
    from .models import Jahrgangsstufe

    user = request.user
    stats = BenutzerStatistik.get_or_create_for_user(user)

    if request.method == "POST":
        # Update user name
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.save()

        # Update preferred Jahrgangsstufe
        stufe_id = request.POST.get("jahrgangsstufe", "")
        if stufe_id:
            stats.bevorzugte_jahrgangsstufe_id = int(stufe_id)
        else:
            stats.bevorzugte_jahrgangsstufe = None
        stats.save()

        return redirect("profil")

    jahrgangsstufen = Jahrgangsstufe.objects.all()

    context = {
        "jahrgangsstufen": jahrgangsstufen,
        "stats": stats,
    }
    return render(request, "karteikarten/profil.html", context)


@login_required
def meine_lernbloecke(request):
    """Manage user's learning block selection."""
    from .models import Schulfach, Jahrgangsstufe

    user = request.user
    stats = BenutzerStatistik.get_or_create_for_user(user)

    # Get filter parameters - use preferred Jahrgangsstufe as default
    fach_id = request.GET.get("fach", "")
    stufe_id = request.GET.get("stufe", "")

    # If no filter set and user has preferred Jahrgangsstufe, use it
    if not stufe_id and not request.GET and stats.bevorzugte_jahrgangsstufe:
        stufe_id = str(stats.bevorzugte_jahrgangsstufe_id)

    nur_ausgewaehlt = request.GET.get("ausgewaehlt", "") == "1"

    # Get all available blocks
    alle_bloecke = Lernblock.objects.select_related(
        "schulfach", "jahrgangsstufe", "lehrwerk_unit__lehrwerk"
    )

    # Apply filters
    if fach_id:
        alle_bloecke = alle_bloecke.filter(schulfach_id=fach_id)
    if stufe_id:
        alle_bloecke = alle_bloecke.filter(jahrgangsstufe_id=stufe_id)

    # Get user's selected blocks
    benutzer_block_ids = set(
        BenutzerLernblock.objects.filter(benutzer=user).values_list(
            "lernblock_id", flat=True
        )
    )

    bloecke = []
    for block in alle_bloecke:
        ist_ausgewaehlt = block.id in benutzer_block_ids
        if nur_ausgewaehlt and not ist_ausgewaehlt:
            continue
        bloecke.append({"lernblock": block, "ausgewaehlt": ist_ausgewaehlt})

    context = {
        "baum": _blockbaum(bloecke),
        "schulfaecher": Schulfach.objects.all(),
        "jahrgangsstufen": Jahrgangsstufe.objects.all(),
        "filter_fach": fach_id,
        "filter_stufe": stufe_id,
        "filter_ausgewaehlt": nur_ausgewaehlt,
        "anzahl_ausgewaehlt": len(benutzer_block_ids),
        "anzahl_sichtbar": len(bloecke),
    }
    return render(request, "karteikarten/meine_lernbloecke.html", context)


def _blockbaum(eintraege):
    """Buch -> Kapitel -> Lernblock, in genau dieser Reihenfolge.

    Eine flache Liste aus achtzig Bloecken ist keine Auswahl, sondern eine Suche.
    Der Baum bildet ab, wie ein Schuljahr tatsaechlich aussieht: ein Buch, darin
    Kapitel, darin die Vokabellisten. Bloecke ohne Einordnung fallen nicht unter
    den Tisch — sie landen sichtbar unter "Ohne Buch", ganz am Ende.
    """
    buecher = {}
    for eintrag in eintraege:
        unit = eintrag["lernblock"].lehrwerk_unit
        buch = unit.lehrwerk if unit else None
        kapitel = buecher.setdefault(buch, {})
        kapitel.setdefault(unit, []).append(eintrag)

    baum = []
    for buch in sorted(buecher, key=lambda b: (b is None, str(b) if b else "")):
        kapitel_liste = []
        for unit in sorted(
            buecher[buch],
            key=lambda u: (u is None, u.reihenfolge if u else 0, u.name if u else ""),
        ):
            gruppe = buecher[buch][unit]
            kapitel_liste.append(
                {
                    "unit": unit,
                    "name": unit.name if unit else "Ohne Kapitel",
                    "bloecke": gruppe,
                    "anzahl": len(gruppe),
                    "gewaehlt": sum(1 for e in gruppe if e["ausgewaehlt"]),
                }
            )
        baum.append(
            {
                "lehrwerk": buch,
                "name": str(buch) if buch else "Ohne Buch",
                "kapitel": kapitel_liste,
                "anzahl": sum(k["anzahl"] for k in kapitel_liste),
                "gewaehlt": sum(k["gewaehlt"] for k in kapitel_liste),
            }
        )
    return baum


@login_required
@require_POST
def lernbloecke_speichern(request):
    """Die Auswahl in einem Zug setzen statt Block fuer Block.

    Abwaehlen loescht nur die Zuordnung, nicht den Lernstand: `BenutzerKarteStatus`
    haengt an der Karte, nicht am Block. Wer einen Block spaeter wieder dazunimmt,
    findet seine Stufen vor.
    """
    gewaehlt = {int(pk) for pk in request.POST.getlist("bloecke") if pk.isdigit()}
    sichtbar = {int(pk) for pk in request.POST.getlist("sichtbar") if pk.isdigit()}

    # Nur ueber das entscheiden, was auf der Seite stand — ein aktiver Filter darf
    # nicht die Bloecke abwaehlen, die er gerade ausblendet.
    gewaehlt &= sichtbar
    vorhanden = set(
        BenutzerLernblock.objects.filter(
            benutzer=request.user, lernblock_id__in=sichtbar
        ).values_list("lernblock_id", flat=True)
    )

    BenutzerLernblock.objects.filter(
        benutzer=request.user, lernblock_id__in=vorhanden - gewaehlt
    ).delete()
    BenutzerLernblock.objects.bulk_create(
        [
            BenutzerLernblock(benutzer=request.user, lernblock_id=pk)
            for pk in gewaehlt - vorhanden
        ]
    )

    anzahl = BenutzerLernblock.objects.filter(benutzer=request.user).count()
    messages.success(request, f"Gespeichert — du lernst jetzt {anzahl} Blöcke.")
    return redirect("meine_lernbloecke")


@login_required
def lernblock_detail(request, pk):
    """Detail view for a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Check if user has this block
    hat_block = BenutzerLernblock.objects.filter(
        benutzer=user, lernblock=lernblock
    ).exists()

    auswahl = _kartenauswahl(request, lernblock)
    anzahl_karten = 0
    faellig_gesamt = 0
    faellig_auswahl = 0
    for karte in lernblock.karten.all():
        anzahl_karten += 1
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        if status.ist_faellig:
            faellig_gesamt += 1
            if auswahl is None or karte.pk in auswahl:
                faellig_auswahl += 1

    zuletzt_gelernt = Lernergebnis.objects.filter(
        benutzer=user, karte__lernblock=lernblock
    ).aggregate(zeitpunkt=Max("zeitstempel"))["zeitpunkt"]

    anteil = round(faellig_auswahl / anzahl_karten * 100) if anzahl_karten else 0

    context = {
        "lernblock": lernblock,
        "faellig_gesamt": faellig_gesamt,
        "faellig_auswahl": faellig_auswahl,
        "ring_versatz": round(RING_UMFANG * (1 - anteil / 100)),
        "zuletzt_gelernt": zuletzt_gelernt,
        "modus": _bevorzugter_modus(user, lernblock),
        "marke": _schulfach_marke(lernblock),
        "hat_block": hat_block,
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/lernblock_detail.html", context)


def _buecher_mit_kapiteln():
    """Buecher mit ihren Kapiteln — Vorlage fuer die Auswahl im Blockformular."""
    return Lehrwerk.objects.prefetch_related("units").all()


@login_required
def lernblock_create(request):
    """Create a new learning block."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        beschreibung = request.POST.get("beschreibung", "").strip()
        lehrbuch = request.POST.get("lehrbuch", "").strip()
        bidirektional = request.POST.get("bidirektional") == "on"

        if name:
            lernblock = Lernblock.objects.create(
                name=name,
                beschreibung=beschreibung,
                lehrbuch=lehrbuch,
                bidirektional=bidirektional,
                lehrwerk_unit=_wahl(LehrwerkUnit, request.POST.get("lehrwerk_unit")),
            )
            # Automatically add to user's blocks
            BenutzerLernblock.objects.create(benutzer=request.user, lernblock=lernblock)
            return redirect("lernblock_detail", pk=lernblock.pk)

    return render(
        request,
        "karteikarten/lernblock_form.html",
        {"action": "Erstellen", "buecher": _buecher_mit_kapiteln()},
    )


@login_required
def lernblock_edit(request, pk):
    """Edit a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)

    if request.method == "POST":
        lernblock.name = request.POST.get("name", "").strip() or lernblock.name
        lernblock.beschreibung = request.POST.get("beschreibung", "").strip()
        lernblock.lehrbuch = request.POST.get("lehrbuch", "").strip()
        lernblock.bidirektional = request.POST.get("bidirektional") == "on"
        lernblock.lehrwerk_unit = _wahl(LehrwerkUnit, request.POST.get("lehrwerk_unit"))
        lernblock.save()
        return redirect("lernblock_detail", pk=lernblock.pk)

    return render(
        request,
        "karteikarten/lernblock_form.html",
        {
            "lernblock": lernblock,
            "action": "Bearbeiten",
            "buecher": _buecher_mit_kapiteln(),
        },
    )


@login_required
@require_POST
def lernblock_delete(request, pk):
    """Delete a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    lernblock.delete()
    return redirect("dashboard")


@login_required
def karten_liste(request, pk):
    """List all cards in a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    karten = lernblock.karten.all()

    # Search filter
    suche = request.GET.get("suche", "").strip()
    if suche:
        karten = karten.filter(begriff__icontains=suche) | karten.filter(
            definition__icontains=suche
        )

    context = {
        "lernblock": lernblock,
        "karten": karten,
        "suche": suche,
    }
    return render(request, "karteikarten/karten_liste.html", context)


@login_required
def karte_create(request, pk):
    """Create a new flashcard."""
    lernblock = get_object_or_404(Lernblock, pk=pk)

    if request.method == "POST":
        begriff = request.POST.get("begriff", "").strip()
        definition = request.POST.get("definition", "").strip()
        beispiele = request.POST.get("beispiele", "").strip()
        zusatz_label = request.POST.get("zusatz_label", "").strip()
        zusatz_wert = request.POST.get("zusatz_wert", "").strip()

        if begriff and definition:
            Karteikarte.objects.create(
                lernblock=lernblock,
                begriff=begriff,
                definition=definition,
                beispiele=beispiele,
                zusatz_label=zusatz_label,
                zusatz_wert=zusatz_wert,
            )
            # Check if user wants to add more
            if request.POST.get("weitere"):
                return redirect("karte_create", pk=lernblock.pk)
            return redirect("karten_liste", pk=lernblock.pk)

    return render(
        request,
        "karteikarten/karte_form.html",
        {"lernblock": lernblock, "action": "Erstellen"},
    )


@login_required
def karte_edit(request, pk):
    """Edit a flashcard."""
    karte = get_object_or_404(Karteikarte, pk=pk)

    if request.method == "POST":
        karte.begriff = request.POST.get("begriff", "").strip() or karte.begriff
        karte.definition = (
            request.POST.get("definition", "").strip() or karte.definition
        )
        karte.beispiele = request.POST.get("beispiele", "").strip()
        karte.zusatz_label = request.POST.get("zusatz_label", "").strip()
        karte.zusatz_wert = request.POST.get("zusatz_wert", "").strip()
        karte.save()
        return redirect("karten_liste", pk=karte.lernblock.pk)

    return render(
        request,
        "karteikarten/karte_form.html",
        {"karte": karte, "lernblock": karte.lernblock, "action": "Bearbeiten"},
    )


@login_required
@require_POST
def karte_delete(request, pk):
    """Delete a flashcard."""
    karte = get_object_or_404(Karteikarte, pk=pk)
    lernblock_pk = karte.lernblock.pk
    karte.delete()
    return redirect("karten_liste", pk=lernblock_pk)


@login_required
def csv_import(request, pk):
    """Import cards from CSV file."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    errors = []
    imported = 0

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        has_header = request.POST.get("has_header") == "on"

        if csv_file:
            try:
                decoded = csv_file.read().decode("utf-8")
                reader = csv.reader(io.StringIO(decoded), delimiter=";")

                for i, row in enumerate(reader):
                    if i == 0 and has_header:
                        continue

                    if len(row) < 2:
                        errors.append(
                            f"Zeile {i + 1}: Mindestens Begriff und Definition erforderlich"
                        )
                        continue

                    begriff = row[0].strip()
                    definition = row[1].strip()
                    beispiele = row[2].strip() if len(row) > 2 else ""
                    zusatz_label = row[3].strip() if len(row) > 3 else ""
                    zusatz_wert = row[4].strip() if len(row) > 4 else ""

                    if not begriff or not definition:
                        errors.append(f"Zeile {i + 1}: Begriff oder Definition leer")
                        continue

                    _, created = Karteikarte.objects.get_or_create(
                        lernblock=lernblock,
                        begriff=begriff,
                        defaults={
                            "definition": definition,
                            "beispiele": beispiele,
                            "zusatz_label": zusatz_label,
                            "zusatz_wert": zusatz_wert,
                        },
                    )
                    if created:
                        imported += 1

            except Exception as e:
                errors.append(f"Fehler beim Lesen der Datei: {str(e)}")

        if imported > 0 and not errors:
            return redirect("karten_liste", pk=lernblock.pk)

    return render(
        request,
        "karteikarten/csv_import.html",
        {
            "lernblock": lernblock,
            "errors": errors,
            "imported": imported,
        },
    )


# Learning modes


# --- Temporaere Kartenauswahl ("Subblock") -----------------------------------
#
# Die Auswahl lebt in der Session, je Lernblock: {"<block_pk>": [karte_pk, ...]}.
# Damit ueberlebt sie das window.location.reload() nach jeder Antwort, ohne den
# Lernblock in der Datenbank anzufassen und ohne die URL zu sprengen (ein Block
# kann mehrere hundert Karten haben).

# Die Lernmodi mit dem Satz, der sie unterscheidet. Eine Liste statt vier
# Template-Bloecke: die Erklaerung soll ueberall dieselbe sein, wo ein Modus
# angeboten wird — auf der Blockseite wie in der Modusauswahl.
LERNMODI = [
    {
        "schluessel": "klassisch",
        "name": "Klassisch",
        "erklaerung": "Umdrehen und selbst einschaetzen",
        "symbol": "bi-book",
        "url": "lernen_klassisch",
        "kombiniert_url": "lernen_kombiniert",
    },
    {
        "schluessel": "tippen",
        "name": "Eintippen",
        "erklaerung": "Antwort schreiben, die App prueft",
        "symbol": "bi-keyboard",
        "url": "lernen_tippen",
        "kombiniert_url": "lernen_kombiniert_tippen",
    },
    {
        "schluessel": "rueckwaerts",
        "name": "Rueckwaerts",
        "erklaerung": "Von der Bedeutung zum Wort",
        "symbol": "bi-arrow-left-right",
        "url": "lernen_rueckwaerts",
        "kombiniert_url": None,
        "braucht_beide_richtungen": True,
    },
    {
        "schluessel": "multiple_choice",
        "name": "Multiple Choice",
        "erklaerung": "Aus vier Antworten waehlen",
        "symbol": "bi-ui-radios",
        "url": "lernen_multiple_choice",
        "kombiniert_url": "lernen_kombiniert_mc",
        "mindestkarten": 4,
    },
]

MODI_NACH_SCHLUESSEL = {modus["schluessel"]: modus for modus in LERNMODI}


def _bevorzugter_modus(user, lernblock=None):
    """Der zuletzt gewaehlte Modus — oder der naechstbeste, der hier passt.

    Ein Block ohne Rueckseite kennt keinen Rueckwaerts-Modus, einer mit drei
    Karten kein Multiple Choice. Statt einer Fehlermeldung faellt die Auswahl
    dann auf "klassisch" zurueck.
    """
    stats = BenutzerStatistik.get_or_create_for_user(user)
    modus = MODI_NACH_SCHLUESSEL.get(stats.bevorzugter_modus, LERNMODI[0])
    if lernblock is not None and not _modus_moeglich(modus, lernblock):
        return LERNMODI[0]
    return modus


def _modus_moeglich(modus, lernblock):
    if modus.get("braucht_beide_richtungen") and not lernblock.bidirektional:
        return False
    return lernblock.anzahl_karten >= modus.get("mindestkarten", 0)


def _modi_fuer_block(lernblock, gewaehlt):
    """Alle Modi mit dem, was das Template zum Anzeigen braucht."""
    return [
        {
            **modus,
            "moeglich": _modus_moeglich(modus, lernblock),
            "gewaehlt": modus["schluessel"] == gewaehlt,
        }
        for modus in LERNMODI
    ]


SESSION_KARTENAUSWAHL = "kartenauswahl"


def _kartenauswahl(request, lernblock):
    """IDs der ausgewaehlten Karten — None, wenn der ganze Block gelernt wird."""
    ids = request.session.get(SESSION_KARTENAUSWAHL, {}).get(str(lernblock.pk))
    return set(ids) if ids is not None else None


def _auswahl_context(request, lernblock):
    """Kontext fuer das Auswahl-Abzeichen in Lern- und Detailansichten."""
    auswahl = _kartenauswahl(request, lernblock)
    return {
        "auswahl_aktiv": auswahl is not None,
        "auswahl_anzahl": len(auswahl) if auswahl is not None else 0,
    }


SESSION_LETZTE_KARTE = "letzte_karte"
SESSION_SITZUNG = "lernsitzung"


def _sitzungsfortschritt(request, schluessel, verbleibend):
    """Wie weit die laufende Abfrage ist — fuer die Leiste in der Kopfzeile.

    Die Gesamtzahl wird beim ersten Aufruf einer Sitzung festgehalten. Sie steigt
    nur, wenn nachtraeglich mehr Karten faellig werden (etwa nach "Noch mal von
    vorn") — sonst bliebe die Leiste stehen oder liefe rueckwaerts. Falsch
    beantwortete Karten bringen die Leiste bewusst nicht voran: sie sind nicht
    erledigt.
    """
    sitzung = request.session.get(SESSION_SITZUNG) or {}
    if sitzung.get("schluessel") != schluessel:
        sitzung = {"schluessel": schluessel, "gesamt": verbleibend}
    elif verbleibend > sitzung.get("gesamt", 0):
        sitzung["gesamt"] = verbleibend
    request.session[SESSION_SITZUNG] = sitzung

    gesamt = sitzung["gesamt"] or 1
    erledigt = max(gesamt - verbleibend, 0)
    return {
        "gesamt": sitzung["gesamt"],
        "erledigt": erledigt,
        "prozent": round(erledigt / gesamt * 100),
    }


def _mischen_nach_fach(faellige, limit):
    """Niedriges Fach zuerst, innerhalb eines Fachs zufaellig.

    Der Shuffle laeuft bei *jedem* Aufruf neu; die Reihenfolge wird bewusst nicht
    einmalig zu Sitzungsbeginn festgelegt. Die Lernansichten laden sich nach jeder
    Antwort komplett neu — eine feste Reihenfolge spuelte deshalb immer wieder
    dieselbe Karte nach oben, allen voran die gerade falsch beantwortete, die
    zurueck in Fach 1 faellt und damit sofort wieder faellig ist.
    """
    random.shuffle(faellige)
    faellige.sort(key=lambda eintrag: eintrag[1].fach)
    return faellige[:limit]


def _naechste_karte(request, faellige):
    """Naechste abzufragende Karte, mit Sperre gegen sofortige Wiederholung.

    `faellige` ist bereits gemischt, hier faellt nur noch die Sperre an: die zuletzt
    gezeigte Karte kommt nicht direkt noch einmal dran, solange es eine Alternative
    gibt. Ohne sie waere gegen Ende einer Sitzung — wenn nur noch wenige Karten
    faellig sind — jede zweite Frage eine Wiederholung der vorigen.
    """
    letzte = request.session.get(SESSION_LETZTE_KARTE)
    kandidaten = [e for e in faellige if e[0].pk != letzte] or faellige
    karte, status = kandidaten[0]
    request.session[SESSION_LETZTE_KARTE] = karte.pk
    return karte, status


def _get_faellige_karten(user, lernblock, limit=20, nur_karten=None):
    """Faellige Karten eines Blocks — niedriges Fach zuerst, sonst zufaellig.

    nur_karten: Menge von Karten-IDs (temporaere Auswahl) oder None fuer den
    ganzen Block. Der Filter greift vor get_or_create_for_user — fuer abgewaehlte
    Karten entsteht also kein Status-Datensatz.
    """
    faellige = []
    for karte in lernblock.karten.all():
        if nur_karten is not None and karte.pk not in nur_karten:
            continue
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        if status.ist_faellig:
            faellige.append((karte, status))

    return _mischen_nach_fach(faellige, limit)


def _get_faellige_karten_multi(user, lernbloecke, limit=50):
    """Faellige Karten mehrerer Bloecke — niedriges Fach zuerst, sonst zufaellig."""
    faellige = []
    for lernblock in lernbloecke:
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if status.ist_faellig:
                faellige.append((karte, status))

    return _mischen_nach_fach(faellige, limit)


def _tipp_loesung(karte, richtung):
    """Die Seite, die eingetippt werden muss."""
    return karte.begriff if richtung == "rueckwaerts" else karte.definition


def _tipp_kontext(karte, status, lernblock, richtung, verbleibend, abbrechen_url):
    """Kontext der Tippansicht — fuer einen Block wie fuer mehrere gleich."""
    rueckwaerts = richtung == "rueckwaerts"
    return {
        "karte": karte,
        "status": status,
        "modus": "tippen",
        "richtung": richtung,
        "frage": karte.definition if rueckwaerts else karte.begriff,
        "gefragt_label": (
            lernblock.vorderseite_label if rueckwaerts else lernblock.rueckseite_label
        ),
        "verbleibend": verbleibend,
        "abbrechen_url": abbrechen_url,
    }


@login_required
def lernen_tippen(request, pk):
    """Tippmodus: die Antwort wird eingetippt statt nur aufgedeckt."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    richtung = request.GET.get("richtung", "")
    if richtung == "rueckwaerts" and not lernblock.bidirektional:
        richtung = ""

    faellige = _get_faellige_karten(
        request.user, lernblock, nur_karten=_kartenauswahl(request, lernblock)
    )

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_fertig.html",
            {
                "lernblock": lernblock,
                "modus": "tippen",
                **_auswahl_context(request, lernblock),
            },
        )

    karte, status = _naechste_karte(request, faellige)

    context = {
        "lernblock": lernblock,
        "fortschritt": _sitzungsfortschritt(
            request, f"block-{lernblock.pk}-tippen", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(request.user, lernblock),
        **_tipp_kontext(
            karte,
            status,
            lernblock,
            richtung,
            len(faellige),
            reverse("lernblock_detail", args=[lernblock.pk]),
        ),
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/lernen_tippen.html", context)


@login_required
def modus_waehlen(request, pk):
    """Den Lernmodus einmal waehlen statt bei jedem Start.

    Die Wahl gilt fuer alle Bloecke und haelt ueber die Sitzung hinaus — sie
    gehoert zur Person, nicht zum Block.
    """
    lernblock = get_object_or_404(Lernblock, pk=pk)
    stats = BenutzerStatistik.get_or_create_for_user(request.user)

    if request.method == "POST":
        gewaehlt = request.POST.get("modus", "")
        if gewaehlt in MODI_NACH_SCHLUESSEL:
            stats.bevorzugter_modus = gewaehlt
            stats.save(update_fields=["bevorzugter_modus"])
        return redirect("lernblock_detail", pk=pk)

    context = {
        "lernblock": lernblock,
        "modi": _modi_fuer_block(lernblock, stats.bevorzugter_modus),
    }
    return render(request, "karteikarten/modus_waehlen.html", context)


@login_required
def lernen_starten(request, pk):
    """Startet die Abfrage im gewaehlten Modus — ein Weg statt vier Kacheln."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    modus = _bevorzugter_modus(request.user, lernblock)
    return redirect(modus["url"], pk=lernblock.pk)


@login_required
def lernen_alles(request):
    """Alle Bloecke des Benutzers zusammen, im gewaehlten Modus.

    Der Weg von der Startseite ins Lernen ohne Zwischenfrage: welche Bloecke und
    welcher Modus stehen bereits fest — Bloecke sind die eigenen, der Modus ist
    die Einstellung.
    """
    block_ids = ",".join(
        str(lernblock.pk) for lernblock in _gewaehlte_bloecke(request.user)
    )
    if not block_ids:
        return redirect("meine_lernbloecke")

    modus = _bevorzugter_modus(request.user)
    ziel = modus["kombiniert_url"] or LERNMODI[0]["kombiniert_url"]
    return redirect(f"{reverse(ziel)}?bloecke={block_ids}")


@login_required
def fortschritt(request):
    """Fortschritt ueber die *ausgewaehlten* Bloecke, nach Schulfach und Lehrwerk.

    Wer im Februar Unit 1 waehlt und im April Unit 2 dazunimmt, soll im Februar
    keine Zahlen zu Unit 2 sehen: gezaehlt wird nur, was in `BenutzerLernblock`
    steht, nicht was es in der Datenbank gibt.
    """
    lernbloecke = _gewaehlte_bloecke(request.user)
    context = {
        "auswertung": gegliederter_fortschritt(request.user, lernbloecke),
        "stats": BenutzerStatistik.get_or_create_for_user(request.user),
    }
    return render(request, "karteikarten/fortschritt.html", context)


@login_required
def lernblock_fortschritt(request, pk):
    """Fortschritt eines einzelnen Blocks."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    context = {
        "lernblock": lernblock,
        "auswertung": block_fortschritt(request.user, lernblock),
    }
    return render(request, "karteikarten/lernblock_fortschritt.html", context)


# --- Buecher und Kapitel -----------------------------------------------------------
# Die Hierarchie Buch -> Kapitel -> Lernblock gab es im Datenmodell laengst, aber
# nur der JSON-Import konnte sie fuellen. Damit blieb sie fuer alle unsichtbar,
# die ihre Vokabeln von Hand pflegen.


@staff_required
def buecher(request):
    """Alle Buecher mit ihren Kapiteln."""
    gebunden = (
        Lehrwerk.objects.select_related("schulfach", "jahrgangsstufe")
        .prefetch_related("units__lernbloecke")
        .all()
    )
    buchliste = [
        {
            "lehrwerk": lehrwerk,
            "kapitel": [
                {"unit": unit, "anzahl_bloecke": unit.lernbloecke.count()}
                for unit in lehrwerk.units.all()
            ],
        }
        for lehrwerk in gebunden
    ]

    context = {
        "buecher": buchliste,
        "ohne_buch": Lernblock.objects.filter(lehrwerk_unit__isnull=True).count(),
    }
    return render(request, "karteikarten/buecher.html", context)


def _buch_speichern(request, lehrwerk):
    """Felder aus dem Formular uebernehmen. Gibt einen Fehlertext zurueck oder None."""
    name = request.POST.get("name", "").strip()
    if not name:
        return "Das Buch braucht einen Namen."

    band = request.POST.get("band", "").strip()
    doppelt = Lehrwerk.objects.filter(name=name, band=band).exclude(pk=lehrwerk.pk)
    if doppelt.exists():
        return f"„{name}“ mit diesem Band gibt es schon."

    lehrwerk.name = name
    lehrwerk.band = band
    lehrwerk.verlag = request.POST.get("verlag", "").strip()
    lehrwerk.schulfach = _wahl(Schulfach, request.POST.get("schulfach"))
    lehrwerk.jahrgangsstufe = _wahl(Jahrgangsstufe, request.POST.get("jahrgangsstufe"))
    lehrwerk.save()
    return None


def _wahl(modell, roh):
    """Ein optionales Auswahlfeld in ein Objekt uebersetzen — leer heisst None."""
    if not roh or not str(roh).isdigit():
        return None
    return modell.objects.filter(pk=int(roh)).first()


def _buch_kontext(lehrwerk=None):
    return {
        "lehrwerk": lehrwerk,
        "schulfaecher": Schulfach.objects.all(),
        "jahrgangsstufen": Jahrgangsstufe.objects.all(),
    }


@staff_required
def buch_create(request):
    """Neues Buch anlegen."""
    if request.method == "POST":
        lehrwerk = Lehrwerk()
        fehler = _buch_speichern(request, lehrwerk)
        if fehler is None:
            messages.success(request, f"Buch „{lehrwerk}“ angelegt.")
            return redirect("buch_detail", pk=lehrwerk.pk)
        messages.error(request, fehler)

    return render(
        request,
        "karteikarten/buch_form.html",
        {"aktion": "Anlegen", **_buch_kontext()},
    )


@staff_required
def buch_edit(request, pk):
    """Buch bearbeiten."""
    lehrwerk = get_object_or_404(Lehrwerk, pk=pk)

    if request.method == "POST":
        fehler = _buch_speichern(request, lehrwerk)
        if fehler is None:
            messages.success(request, "Buch gespeichert.")
            return redirect("buch_detail", pk=lehrwerk.pk)
        messages.error(request, fehler)

    return render(
        request,
        "karteikarten/buch_form.html",
        {"aktion": "Speichern", **_buch_kontext(lehrwerk)},
    )


@staff_required
def buch_detail(request, pk):
    """Ein Buch mit seinen Kapiteln und deren Bloecken."""
    lehrwerk = get_object_or_404(Lehrwerk, pk=pk)
    kapitel = [
        {"unit": unit, "bloecke": list(unit.lernbloecke.all())}
        for unit in lehrwerk.units.all()
    ]
    return render(
        request,
        "karteikarten/buch_detail.html",
        {"lehrwerk": lehrwerk, "kapitel": kapitel},
    )


@staff_required
@require_POST
def buch_loeschen(request, pk):
    """Buch loeschen — nur, solange kein Kapitel Bloecke traegt.

    Ein Buch zu loeschen wuerde ueber die Kaskade alle Kapitel mitnehmen; die
    Lernbloecke blieben zwar erhalten (ihr Verweis wird auf NULL gesetzt), aber
    ihre Einordnung waere weg. Das passiert nicht aus Versehen.
    """
    lehrwerk = get_object_or_404(Lehrwerk, pk=pk)
    belegte = [unit for unit in lehrwerk.units.all() if unit.lernbloecke.exists()]
    if belegte:
        messages.error(
            request,
            f"„{lehrwerk}“ hat noch Kapitel mit Lernblöcken "
            f"({', '.join(unit.name for unit in belegte)}). Erst die Blöcke umhängen.",
        )
        return redirect("buch_detail", pk=pk)

    name = str(lehrwerk)
    lehrwerk.delete()
    messages.success(request, f"Buch „{name}“ gelöscht.")
    return redirect("buecher")


@staff_required
def kapitel_create(request, pk):
    """Kapitel in einem Buch anlegen."""
    lehrwerk = get_object_or_404(Lehrwerk, pk=pk)

    if request.method == "POST":
        fehler = _kapitel_speichern(request, LehrwerkUnit(lehrwerk=lehrwerk))
        if fehler is None:
            return redirect("buch_detail", pk=lehrwerk.pk)
        messages.error(request, fehler)

    return render(
        request,
        "karteikarten/kapitel_form.html",
        {
            "lehrwerk": lehrwerk,
            "aktion": "Anlegen",
            # Neue Kapitel hinten anstellen, statt bei 0 zu beginnen
            "reihenfolge": lehrwerk.units.count() + 1,
        },
    )


@staff_required
def kapitel_edit(request, pk):
    """Kapitel bearbeiten."""
    unit = get_object_or_404(LehrwerkUnit, pk=pk)

    if request.method == "POST":
        fehler = _kapitel_speichern(request, unit)
        if fehler is None:
            return redirect("buch_detail", pk=unit.lehrwerk_id)
        messages.error(request, fehler)

    return render(
        request,
        "karteikarten/kapitel_form.html",
        {
            "lehrwerk": unit.lehrwerk,
            "unit": unit,
            "aktion": "Speichern",
            "reihenfolge": unit.reihenfolge,
        },
    )


def _kapitel_speichern(request, unit):
    name = request.POST.get("name", "").strip()
    if not name:
        return "Das Kapitel braucht einen Namen."

    doppelt = LehrwerkUnit.objects.filter(lehrwerk=unit.lehrwerk, name=name).exclude(
        pk=unit.pk
    )
    if doppelt.exists():
        return f"„{name}“ gibt es in diesem Buch schon."

    reihenfolge = request.POST.get("reihenfolge", "").strip()
    unit.name = name
    unit.beschreibung = request.POST.get("beschreibung", "").strip()
    unit.reihenfolge = int(reihenfolge) if reihenfolge.isdigit() else 0
    unit.save()
    messages.success(request, f"Kapitel „{name}“ gespeichert.")
    return None


@staff_required
@require_POST
def kapitel_loeschen(request, pk):
    """Kapitel loeschen — nur, solange keine Bloecke daran haengen."""
    unit = get_object_or_404(LehrwerkUnit, pk=pk)
    anzahl = unit.lernbloecke.count()
    if anzahl:
        messages.error(
            request,
            f"„{unit.name}“ trägt noch {anzahl} Lernblöcke. Erst die Blöcke umhängen.",
        )
        return redirect("buch_detail", pk=unit.lehrwerk_id)

    lehrwerk_id = unit.lehrwerk_id
    name = unit.name
    unit.delete()
    messages.success(request, f"Kapitel „{name}“ gelöscht.")
    return redirect("buch_detail", pk=lehrwerk_id)


@login_required
def mehr(request):
    """Alles, was nicht zum Lernen gehoert — inklusive der Verwaltung."""
    return render(request, "karteikarten/mehr.html")


@login_required
@require_POST
def karten_zuruecksetzen(request, pk):
    """Reset all cards in a block to be available for learning today."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Reset card statuses to today — bei aktiver Auswahl nur die ausgewaehlten
    auswahl = _kartenauswahl(request, lernblock)
    for karte in lernblock.karten.all():
        if auswahl is not None and karte.pk not in auswahl:
            continue
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        status.naechste_wiederholung = date.today()
        status.save()

    # Redirect back to the learning mode they came from
    modus = request.POST.get("modus", "klassisch")
    if modus == "rueckwaerts":
        return redirect("lernen_rueckwaerts", pk=pk)
    elif modus == "multiple_choice":
        return redirect("lernen_multiple_choice", pk=pk)
    elif modus == "tippen":
        return redirect("lernen_tippen", pk=pk)
    return redirect("lernen_klassisch", pk=pk)


@login_required
def kartenauswahl(request, pk):
    """Temporaere Kartenauswahl fuer einen Lernblock ("Subblock").

    Aendert den Lernblock nicht — die Auswahl liegt in der Session und gilt bis
    sie aufgehoben wird oder die Session endet.
    """
    lernblock = get_object_or_404(Lernblock, pk=pk)
    karten = list(lernblock.karten.all())

    if request.method == "POST":
        gewaehlt = {int(k) for k in request.POST.getlist("karten") if k.isdigit()}
        gewaehlt &= {karte.pk for karte in karten}
        if not gewaehlt:
            messages.error(request, "Mindestens eine Karte auswaehlen.")
        else:
            auswahl = request.session.get(SESSION_KARTENAUSWAHL, {})
            if len(gewaehlt) == len(karten):
                # Vollstaendige Auswahl ist keine Auswahl — sonst zeigte das
                # Abzeichen dauerhaft "40 von 40".
                auswahl.pop(str(lernblock.pk), None)
                messages.success(
                    request,
                    "Auswahl aufgehoben — es wird wieder der ganze Block gelernt.",
                )
            else:
                auswahl[str(lernblock.pk)] = sorted(gewaehlt)
                messages.success(
                    request,
                    f"Auswahl gespeichert: {len(gewaehlt)} von {len(karten)} Karten.",
                )
            request.session[SESSION_KARTENAUSWAHL] = auswahl
            return redirect("lernblock_detail", pk=lernblock.pk)

    auswahl = _kartenauswahl(request, lernblock)
    falsch_je_karte = dict(
        Lernergebnis.objects.filter(
            benutzer=request.user, karte__in=karten, richtig=False
        )
        .values_list("karte_id")
        .annotate(anzahl=Count("pk"))
    )

    # Vorauswahl per Link, etwa aus der Fortschrittsansicht ("Gezielt ueben").
    vorauswahl = request.GET.get("nur", "")
    if vorauswahl == "problem":
        gewuenscht = {pk for pk, anzahl in falsch_je_karte.items() if anzahl}
    else:
        gewuenscht = None

    # Gruppiert nach Leitner-Stufe: das ist die Ordnung, die der Lernende ohnehin
    # ueberall sieht — und sie sagt, wo Arbeit liegt.
    gruppen = {stufe: {"stufe": stufe, "karten": []} for stufe in range(1, 6)}
    for karte in karten:
        status = BenutzerKarteStatus.get_or_create_for_user(request.user, karte)
        if gewuenscht is not None:
            gewaehlt = karte.pk in gewuenscht
        else:
            gewaehlt = auswahl is None or karte.pk in auswahl
        gruppen[status.fach]["karten"].append(
            {
                "karte": karte,
                "status": status,
                "gewaehlt": gewaehlt,
                "falsch": falsch_je_karte.get(karte.pk, 0),
            }
        )

    for gruppe in gruppen.values():
        gruppe["karten"].sort(key=lambda eintrag: -eintrag["falsch"])
        gruppe["anzahl"] = len(gruppe["karten"])
        gruppe["gewaehlt"] = sum(1 for e in gruppe["karten"] if e["gewaehlt"])

    karten_mit_status = [
        eintrag for gruppe in gruppen.values() for eintrag in gruppe["karten"]
    ]

    context = {
        "lernblock": lernblock,
        "karten_mit_status": karten_mit_status,
        "gruppen": [gruppe for gruppe in gruppen.values() if gruppe["anzahl"]],
        "anzahl_problemkarten": sum(1 for wert in falsch_je_karte.values() if wert),
        "vorauswahl": vorauswahl,
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/kartenauswahl.html", context)


@login_required
@require_POST
def kartenauswahl_aufheben(request, pk):
    """Temporaere Auswahl verwerfen — es wird wieder der ganze Block gelernt."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    auswahl = request.session.get(SESSION_KARTENAUSWAHL, {})
    if auswahl.pop(str(lernblock.pk), None) is not None:
        request.session[SESSION_KARTENAUSWAHL] = auswahl
        messages.success(request, "Auswahl aufgehoben.")
    return redirect("lernblock_detail", pk=lernblock.pk)


@login_required
def lernen_klassisch(request, pk):
    """Classic learning mode: show term, reveal definition."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    faellige = _get_faellige_karten(
        user, lernblock, nur_karten=_kartenauswahl(request, lernblock)
    )

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_fertig.html",
            {
                "lernblock": lernblock,
                "modus": "klassisch",
                **_auswahl_context(request, lernblock),
            },
        )

    karte, status = _naechste_karte(request, faellige)

    context = {
        "lernblock": lernblock,
        "karte": karte,
        "status": status,
        "modus": "klassisch",
        "verbleibend": len(faellige),
        "fortschritt": _sitzungsfortschritt(
            request, f"block-{lernblock.pk}-klassisch", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(user, lernblock),
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/lernen_karte.html", context)


@login_required
def lernen_rueckwaerts(request, pk):
    """Reverse learning mode: show definition, reveal term."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    if not lernblock.bidirektional:
        return redirect("lernblock_detail", pk=pk)

    faellige = _get_faellige_karten(
        user, lernblock, nur_karten=_kartenauswahl(request, lernblock)
    )

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_fertig.html",
            {
                "lernblock": lernblock,
                "modus": "rueckwaerts",
                **_auswahl_context(request, lernblock),
            },
        )

    karte, status = _naechste_karte(request, faellige)

    context = {
        "lernblock": lernblock,
        "karte": karte,
        "status": status,
        "modus": "rueckwaerts",
        "verbleibend": len(faellige),
        "fortschritt": _sitzungsfortschritt(
            request, f"block-{lernblock.pk}-rueckwaerts", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(user, lernblock),
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/lernen_karte.html", context)


@login_required
def lernen_multiple_choice(request, pk):
    """Multiple choice learning mode."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Need at least 4 cards for multiple choice
    alle_karten = list(lernblock.karten.all())
    if len(alle_karten) < 4:
        return render(
            request,
            "karteikarten/lernen_fertig.html",
            {
                "lernblock": lernblock,
                "modus": "multiple_choice",
                "error": "Mindestens 4 Karten für Multiple Choice benötigt.",
            },
        )

    faellige = _get_faellige_karten(
        user, lernblock, nur_karten=_kartenauswahl(request, lernblock)
    )

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_fertig.html",
            {
                "lernblock": lernblock,
                "modus": "multiple_choice",
                **_auswahl_context(request, lernblock),
            },
        )

    karte, status = _naechste_karte(request, faellige)

    # Get 3 distractors
    andere_karten = [k for k in alle_karten if k.pk != karte.pk]
    distraktoren = random.sample(andere_karten, min(3, len(andere_karten)))

    # Build answer options
    optionen = [{"text": karte.definition, "korrekt": True, "karte_id": karte.pk}]
    for d in distraktoren:
        optionen.append({"text": d.definition, "korrekt": False, "karte_id": d.pk})

    random.shuffle(optionen)

    context = {
        "lernblock": lernblock,
        "karte": karte,
        "status": status,
        "optionen": optionen,
        "modus": "multiple_choice",
        "verbleibend": len(faellige),
        "fortschritt": _sitzungsfortschritt(
            request, f"block-{lernblock.pk}-mc", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(user, lernblock),
        **_auswahl_context(request, lernblock),
    }
    return render(request, "karteikarten/lernen_multiple_choice.html", context)


def _antwort_verbuchen(user, karte, richtig, modus):
    """Leitner-Fach weiterstellen und die Statistiken fortschreiben.

    Gemeinsamer Weg fuer alle Lernmodi: wer die Antwort selbst bewertet
    (klassisch, rueckwaerts, Multiple Choice) und wer sie eintippt, landet hier.
    """
    status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
    if richtig:
        status.richtig_beantwortet()
    else:
        status.falsch_beantwortet()

    Lernergebnis.objects.create(
        benutzer=user, karte=karte, modus=modus, richtig=richtig
    )

    stats, _ = TagesStatistik.objects.get_or_create(
        benutzer=user,
        lernblock=karte.lernblock,
        datum=date.today(),
    )
    stats.gelernt += 1
    if richtig:
        stats.richtig += 1
    else:
        stats.falsch += 1
    stats.save()

    benutzer_stats = BenutzerStatistik.get_or_create_for_user(user)
    benutzer_stats.gesamt_gelernt += 1
    if richtig:
        benutzer_stats.gesamt_richtig += 1
        benutzer_stats.update_streak()
    benutzer_stats.save()

    return status


@login_required
@require_POST
def karte_antwort(request, pk):
    """Process answer for a card (AJAX endpoint)."""
    karte = get_object_or_404(Karteikarte, pk=pk)
    richtig = request.POST.get("richtig") == "true"
    modus = request.POST.get("modus", "klassisch")

    status = _antwort_verbuchen(request.user, karte, richtig, modus)

    return JsonResponse(
        {
            "success": True,
            "neues_fach": status.fach,
            "naechste_wiederholung": str(status.naechste_wiederholung),
        }
    )


@login_required
@require_POST
def karte_tippen_antwort(request, pk):
    """Eingetippte Antwort pruefen, verbuchen und die Loesung zurueckmelden.

    Die Pruefung laeuft bewusst serverseitig: so steht die Loesung erst nach der
    Antwort im Browser, und die Nachsicht bei Akzenten und Artikeln liegt an einer
    Stelle statt in JavaScript.
    """
    karte = get_object_or_404(Karteikarte, pk=pk)
    loesung = _tipp_loesung(karte, request.POST.get("richtung", ""))
    ergebnis = pruefe_antwort(request.POST.get("eingabe", ""), loesung)
    richtig = ergebnis in (RICHTIG, FAST)

    status = _antwort_verbuchen(request.user, karte, richtig, "tippen")

    return JsonResponse(
        {
            "success": True,
            "ergebnis": ergebnis,
            "richtig": richtig,
            "loesung": loesung,
            "neues_fach": status.fach,
            "naechste_wiederholung": str(status.naechste_wiederholung),
        }
    )


# Combined learning (multiple blocks)


@login_required
def lernen_kombiniert_auswahl(request):
    """Select multiple blocks for combined learning."""
    user = request.user

    # Get user's selected blocks
    benutzer_bloecke = BenutzerLernblock.objects.filter(benutzer=user).select_related(
        "lernblock"
    )

    # Prepare blocks with due count
    bloecke = []
    total_faellig = 0
    for bl in benutzer_bloecke:
        lernblock = bl.lernblock
        faellig = 0
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if status.ist_faellig:
                faellig += 1
        total_faellig += faellig
        bloecke.append(
            {
                "lernblock": lernblock,
                "faellig": faellig,
                "anzahl": lernblock.anzahl_karten,
            }
        )

    modus = _bevorzugter_modus(user)
    context = {
        "modus": modus,
        "modus_url": reverse(modus["kombiniert_url"] or LERNMODI[0]["kombiniert_url"]),
        "bloecke": bloecke,
        "total_faellig": total_faellig,
    }
    return render(request, "karteikarten/lernen_kombiniert_auswahl.html", context)


def _kombinierte_bloecke(request):
    """Die per `?bloecke=` gewaehlten Bloecke — nur die, die dem Benutzer gehoeren.

    Leere Liste heisst: zurueck zur Blockauswahl.
    """
    block_ids = [
        int(bid) for bid in request.GET.get("bloecke", "").split(",") if bid.isdigit()
    ]
    if not block_ids:
        return []
    return list(
        Lernblock.objects.filter(
            pk__in=block_ids, benutzer_zuordnungen__benutzer=request.user
        )
    )


@login_required
def lernen_kombiniert(request):
    """Combined learning mode for multiple blocks (classic mode)."""
    lernbloecke = _kombinierte_bloecke(request)
    if not lernbloecke:
        return redirect("lernen_kombiniert_auswahl")

    block_ids = ",".join(str(b.pk) for b in lernbloecke)
    faellige = _get_faellige_karten_multi(request.user, lernbloecke)

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_kombiniert_fertig.html",
            {
                "lernbloecke": lernbloecke,
                "block_ids": block_ids,
                "modus": "klassisch",
            },
        )

    karte, status = _naechste_karte(request, faellige)

    context = {
        "lernbloecke": lernbloecke,
        "block_ids": block_ids,
        "karte": karte,
        "status": status,
        "modus": "klassisch",
        "verbleibend": len(faellige),
        "fortschritt": _sitzungsfortschritt(
            request, f"kombiniert-{block_ids}-klassisch", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(request.user, karte.lernblock),
    }
    return render(request, "karteikarten/lernen_kombiniert_karte.html", context)


@login_required
def lernen_kombiniert_mc(request):
    """Combined learning mode for multiple blocks (multiple choice)."""
    lernbloecke = _kombinierte_bloecke(request)
    if not lernbloecke:
        return redirect("lernen_kombiniert_auswahl")

    block_ids = ",".join(str(b.pk) for b in lernbloecke)

    # Get all cards from all blocks for distractors
    alle_karten = []
    for lb in lernbloecke:
        alle_karten.extend(list(lb.karten.all()))

    if len(alle_karten) < 4:
        return render(
            request,
            "karteikarten/lernen_kombiniert_fertig.html",
            {
                "lernbloecke": lernbloecke,
                "block_ids": ",".join(str(b.pk) for b in lernbloecke),
                "modus": "multiple_choice",
                "error": "Mindestens 4 Karten insgesamt fuer Multiple Choice benoetigt.",
            },
        )

    faellige = _get_faellige_karten_multi(request.user, lernbloecke)

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_kombiniert_fertig.html",
            {
                "lernbloecke": lernbloecke,
                "block_ids": block_ids,
                "modus": "multiple_choice",
            },
        )

    karte, status = _naechste_karte(request, faellige)

    # Get 3 distractors from all blocks
    andere_karten = [k for k in alle_karten if k.pk != karte.pk]
    distraktoren = random.sample(andere_karten, min(3, len(andere_karten)))

    # Build answer options
    optionen = [{"text": karte.definition, "korrekt": True, "karte_id": karte.pk}]
    for d in distraktoren:
        optionen.append({"text": d.definition, "korrekt": False, "karte_id": d.pk})

    random.shuffle(optionen)

    context = {
        "lernbloecke": lernbloecke,
        "block_ids": block_ids,
        "karte": karte,
        "status": status,
        "optionen": optionen,
        "modus": "multiple_choice",
        "verbleibend": len(faellige),
        "fortschritt": _sitzungsfortschritt(
            request, f"kombiniert-{block_ids}-mc", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(request.user, karte.lernblock),
    }
    return render(request, "karteikarten/lernen_kombiniert_mc.html", context)


@login_required
def lernen_kombiniert_tippen(request):
    """Tippmodus ueber mehrere Lernbloecke hinweg."""
    lernbloecke = _kombinierte_bloecke(request)
    if not lernbloecke:
        return redirect("lernen_kombiniert_auswahl")

    block_ids = ",".join(str(b.pk) for b in lernbloecke)
    faellige = _get_faellige_karten_multi(request.user, lernbloecke)

    if not faellige:
        return render(
            request,
            "karteikarten/lernen_kombiniert_fertig.html",
            {
                "lernbloecke": lernbloecke,
                "block_ids": block_ids,
                "modus": "tippen",
            },
        )

    karte, status = _naechste_karte(request, faellige)

    context = {
        "lernbloecke": lernbloecke,
        "block_ids": block_ids,
        "fortschritt": _sitzungsfortschritt(
            request, f"kombiniert-{block_ids}-tippen", len(faellige)
        ),
        "blockfortschritt": kurzfortschritt(request.user, karte.lernblock),
        **_tipp_kontext(
            karte,
            status,
            karte.lernblock,
            "",
            len(faellige),
            reverse("lernen_kombiniert_auswahl"),
        ),
    }
    return render(request, "karteikarten/lernen_tippen.html", context)


@login_required
@require_POST
def karten_zuruecksetzen_kombiniert(request):
    """Reset all cards in selected blocks to be available for learning today."""
    user = request.user
    block_ids = request.POST.get("bloecke", "").split(",")
    block_ids = [int(bid) for bid in block_ids if bid.isdigit()]

    lernbloecke = Lernblock.objects.filter(
        pk__in=block_ids, benutzer_zuordnungen__benutzer=user
    )

    for lernblock in lernbloecke:
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            status.naechste_wiederholung = date.today()
            status.save()

    modus = request.POST.get("modus", "klassisch")
    block_param = ",".join(str(bid) for bid in block_ids)

    if modus == "multiple_choice":
        ziel = reverse("lernen_kombiniert_mc")
    elif modus == "tippen":
        ziel = reverse("lernen_kombiniert_tippen")
    else:
        ziel = reverse("lernen_kombiniert")
    return redirect(f"{ziel}?bloecke={block_param}")


# PWA


def manifest(request):
    """PWA manifest."""
    return render(
        request, "karteikarten/manifest.json", content_type="application/manifest+json"
    )


def service_worker(request):
    """Service worker for PWA."""
    return render(request, "karteikarten/sw.js", content_type="application/javascript")


def js_db(request):
    """IndexedDB wrapper JavaScript."""
    return render(
        request, "karteikarten/js/db.js", content_type="application/javascript"
    )


def js_sync(request):
    """Sync JavaScript."""
    return render(
        request, "karteikarten/js/sync.js", content_type="application/javascript"
    )


def js_offline_learning(request):
    """Offline learning JavaScript."""
    return render(
        request,
        "karteikarten/js/offline-learning.js",
        content_type="application/javascript",
    )


@login_required
def lernen_offline(request):
    """Offline learning page."""
    return render(request, "karteikarten/lernen_offline.html")


# =============================================================================
# Offline Sync API
# =============================================================================


@login_required
def sync_pull(request):
    """Pull all data for offline use."""
    user = request.user

    # Alle Lernblöcke des Benutzers
    lernbloecke = Lernblock.objects.filter(benutzer_zuordnungen__benutzer=user).values(
        "id", "name", "beschreibung", "thema", "bidirektional"
    )

    # Alle Karten aus diesen Blöcken
    lernblock_ids = [b["id"] for b in lernbloecke]
    karten = Karteikarte.objects.filter(lernblock_id__in=lernblock_ids).values(
        "id",
        "lernblock_id",
        "begriff",
        "definition",
        "beispiele",
        "zusatz_label",
        "zusatz_wert",
    )

    # Benutzer-Status für alle Karten
    karten_ids = [k["id"] for k in karten]
    status_list = BenutzerKarteStatus.objects.filter(
        benutzer=user, karte_id__in=karten_ids
    ).values("karte_id", "fach", "naechste_wiederholung")

    # Status als Dict mit karte_id als Key formatieren
    status_data = []
    for s in status_list:
        status_data.append(
            {
                "karte_id": s["karte_id"],
                "fach": s["fach"],
                "naechste_wiederholung": s["naechste_wiederholung"].isoformat()
                if s["naechste_wiederholung"]
                else None,
            }
        )

    return JsonResponse(
        {
            "lernbloecke": list(lernbloecke),
            "karten": list(karten),
            "status": status_data,
            "timestamp": date.today().isoformat(),
        }
    )


@login_required
@require_POST
def sync_push(request):
    """Push offline changes to server."""
    import json

    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if data.get("type") == "antwort":
        karte_id = data.get("karte_id")
        richtig = data.get("richtig", False)
        modus = data.get("modus", "klassisch")

        try:
            karte = Karteikarte.objects.get(pk=karte_id)
        except Karteikarte.DoesNotExist:
            return JsonResponse({"error": "Karte not found"}, status=404)

        # Status aktualisieren
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        if richtig:
            status.richtig_beantwortet()
        else:
            status.falsch_beantwortet()

        # Lernergebnis speichern
        Lernergebnis.objects.create(
            benutzer=user, karte=karte, modus=modus, richtig=richtig
        )

        # Tagesstatistik aktualisieren
        stats, _ = TagesStatistik.objects.get_or_create(
            benutzer=user,
            lernblock=karte.lernblock,
            datum=date.today(),
        )
        stats.gelernt += 1
        if richtig:
            stats.richtig += 1
        else:
            stats.falsch += 1
        stats.save()

        # Benutzerstatistik aktualisieren
        benutzer_stats = BenutzerStatistik.get_or_create_for_user(user)
        benutzer_stats.gesamt_gelernt += 1
        if richtig:
            benutzer_stats.gesamt_richtig += 1
        benutzer_stats.update_streak()
        benutzer_stats.save()

        return JsonResponse(
            {
                "success": True,
                "karte_id": karte_id,
                "neuer_status": {
                    "fach": status.fach,
                    "naechste_wiederholung": status.naechste_wiederholung.isoformat(),
                },
            }
        )

    return JsonResponse({"error": "Unknown action type"}, status=400)


# =============================================================================
# Admin: User Management
# =============================================================================


@staff_required
def benutzer_liste(request):
    """List all users (admin only)."""
    benutzer = User.objects.all().order_by("username")

    # Add stats to each user
    benutzer_mit_stats = []
    for user in benutzer:
        stats = BenutzerStatistik.get_or_create_for_user(user)
        benutzer_mit_stats.append(
            {
                "user": user,
                "stats": stats,
                "bloecke": user.lernbloecke.count(),
            }
        )

    context = {
        "benutzer_liste": benutzer_mit_stats,
    }
    return render(request, "karteikarten/admin/benutzer_liste.html", context)


@staff_required
def benutzer_erstellen(request):
    """Create a new user (admin only)."""
    errors = []

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        is_staff = request.POST.get("is_staff") == "on"

        # Validation
        if not username:
            errors.append("Benutzername ist erforderlich.")
        elif User.objects.filter(username=username).exists():
            errors.append("Benutzername existiert bereits.")

        if not password:
            errors.append("Passwort ist erforderlich.")
        elif len(password) < 6:
            errors.append("Passwort muss mindestens 6 Zeichen haben.")

        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            user.is_staff = is_staff
            user.save()

            # Create stats and mark password change required
            stats = BenutzerStatistik.get_or_create_for_user(user)
            stats.muss_passwort_aendern = True
            stats.save()

            messages.success(request, f'Benutzer "{username}" wurde erstellt.')
            return redirect("benutzer_liste")

    return render(
        request,
        "karteikarten/admin/benutzer_form.html",
        {
            "errors": errors,
            "action": "erstellen",
        },
    )


@staff_required
def benutzer_bearbeiten(request, pk):
    """Edit an existing user (admin only)."""
    user = get_object_or_404(User, pk=pk)
    stats = BenutzerStatistik.get_or_create_for_user(user)
    errors = []

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        is_staff = request.POST.get("is_staff") == "on"
        is_active = request.POST.get("is_active") == "on"
        reset_password = request.POST.get("reset_password", "").strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_staff = is_staff
        user.is_active = is_active

        if reset_password:
            if len(reset_password) < 6:
                errors.append("Passwort muss mindestens 6 Zeichen haben.")
            else:
                user.set_password(reset_password)
                stats.muss_passwort_aendern = True
                stats.save()

        if not errors:
            user.save()
            messages.success(request, f'Benutzer "{user.username}" wurde aktualisiert.')
            return redirect("benutzer_liste")

    return render(
        request,
        "karteikarten/admin/benutzer_form.html",
        {
            "benutzer": user,
            "benutzer_stats": stats,
            "errors": errors,
            "action": "bearbeiten",
        },
    )


@staff_required
@require_POST
def benutzer_loeschen(request, pk):
    """Delete a user (admin only)."""
    user = get_object_or_404(User, pk=pk)

    # Don't allow deleting yourself
    if user == request.user:
        messages.error(request, "Du kannst dich nicht selbst loeschen.")
        return redirect("benutzer_liste")

    username = user.username
    user.delete()
    messages.success(request, f'Benutzer "{username}" wurde geloescht.')
    return redirect("benutzer_liste")


# =============================================================================
# Password Change
# =============================================================================


@login_required
def passwort_aendern(request):
    """Change password view."""
    user = request.user
    stats = BenutzerStatistik.get_or_create_for_user(user)
    errors = []
    force_change = stats.muss_passwort_aendern

    if request.method == "POST":
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Validation
        if not user.check_password(current_password):
            errors.append("Aktuelles Passwort ist falsch.")

        if not new_password:
            errors.append("Neues Passwort ist erforderlich.")
        elif len(new_password) < 6:
            errors.append("Neues Passwort muss mindestens 6 Zeichen haben.")

        if new_password != confirm_password:
            errors.append("Passwoerter stimmen nicht ueberein.")

        if current_password == new_password:
            errors.append("Neues Passwort muss sich vom aktuellen unterscheiden.")

        if not errors:
            user.set_password(new_password)
            user.save()

            # Clear the force change flag
            stats.muss_passwort_aendern = False
            stats.save()

            # Keep user logged in
            update_session_auth_hash(request, user)

            messages.success(request, "Passwort wurde erfolgreich geaendert.")
            return redirect("dashboard")

    return render(
        request,
        "karteikarten/passwort_aendern.html",
        {
            "errors": errors,
            "force_change": force_change,
        },
    )


# =============================================================================
# Backup
# =============================================================================


@staff_required
def backup_liste(request):
    """List existing backups and create new ones."""
    from .services.json_exporter import JSONExporter

    exporter = JSONExporter()
    backups = exporter.list_backups()

    # Get stats about current data
    from .models import Lehrwerk

    lehrwerke = Lehrwerk.objects.all()
    lehrwerk_stats = []
    total_karten = 0
    for lw in lehrwerke:
        anzahl = lw.anzahl_karten
        total_karten += anzahl
        if anzahl > 0:
            lehrwerk_stats.append(
                {
                    "name": str(lw),
                    "anzahl_karten": anzahl,
                    "anzahl_units": lw.anzahl_units,
                }
            )

    context = {
        "backups": backups,
        "lehrwerk_stats": lehrwerk_stats,
        "total_karten": total_karten,
    }
    return render(request, "karteikarten/admin/backup_liste.html", context)


@staff_required
@require_POST
def backup_erstellen(request):
    """Create a new backup."""
    from .services.json_exporter import JSONExporter

    exporter = JSONExporter()
    modus = request.POST.get("modus", "einzeln")

    if modus == "single":
        filepath = exporter.backup_all_to_single_file()
        messages.success(request, f"Backup erstellt: {filepath.name}")
    else:
        files = exporter.backup_all(include_timestamp=True)
        messages.success(request, f"{len(files)} Backup-Dateien erstellt.")

    return redirect("backup_liste")


@staff_required
def backup_download(request, filename):
    """Download a backup file."""
    from django.http import FileResponse
    from .services.json_exporter import JSONExporter

    exporter = JSONExporter()
    filepath = exporter.backup_dir / filename

    if not filepath.exists() or not filepath.is_file():
        messages.error(request, "Backup-Datei nicht gefunden.")
        return redirect("backup_liste")

    # Security: ensure the file is in the backup directory
    try:
        filepath.resolve().relative_to(exporter.backup_dir.resolve())
    except ValueError:
        messages.error(request, "Ungueltiger Dateipfad.")
        return redirect("backup_liste")

    return FileResponse(open(filepath, "rb"), as_attachment=True, filename=filename)
