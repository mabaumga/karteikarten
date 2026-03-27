"""Views for Karteikarten application."""
import csv
import io
import random
from datetime import date
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from .models import (
    Lernblock, Karteikarte, TagesStatistik, Lernergebnis,
    BenutzerLernblock, BenutzerKarteStatus, BenutzerStatistik
)


def staff_required(view_func):
    """Decorator that requires user to be staff."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard(request):
    """Main dashboard with user's learning blocks."""
    user = request.user

    # Get user's selected blocks
    benutzer_bloecke = BenutzerLernblock.objects.filter(
        benutzer=user
    ).select_related('lernblock')

    lernbloecke = [bl.lernblock for bl in benutzer_bloecke]

    # Get user statistics
    stats = BenutzerStatistik.get_or_create_for_user(user)

    # Calculate user-specific stats
    total_karten = 0
    total_faellig = 0

    for lernblock in lernbloecke:
        karten = lernblock.karten.all()
        total_karten += karten.count()

        # Count due cards for this user
        for karte in karten:
            karten_status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if karten_status.ist_faellig:
                total_faellig += 1

    # Today's results for this user
    heute_richtig = Lernergebnis.objects.filter(
        benutzer=user,
        zeitstempel__date=date.today(),
        richtig=True
    ).count()
    heute_falsch = Lernergebnis.objects.filter(
        benutzer=user,
        zeitstempel__date=date.today(),
        richtig=False
    ).count()

    # Prepare blocks with user-specific due count
    bloecke_mit_status = []
    for lernblock in lernbloecke:
        faellig = 0
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if status.ist_faellig:
                faellig += 1
        bloecke_mit_status.append({
            'lernblock': lernblock,
            'faellig': faellig,
            'anzahl': lernblock.anzahl_karten,
        })

    context = {
        'bloecke_mit_status': bloecke_mit_status,
        'streak': stats.streak,
        'total_karten': total_karten,
        'total_faellig': total_faellig,
        'heute_richtig': heute_richtig,
        'heute_falsch': heute_falsch,
    }
    return render(request, 'karteikarten/dashboard.html', context)


@login_required
def profil(request):
    """User profile settings."""
    from .models import Jahrgangsstufe

    user = request.user
    stats = BenutzerStatistik.get_or_create_for_user(user)

    if request.method == 'POST':
        # Update user name
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.save()

        # Update preferred Jahrgangsstufe
        stufe_id = request.POST.get('jahrgangsstufe', '')
        if stufe_id:
            stats.bevorzugte_jahrgangsstufe_id = int(stufe_id)
        else:
            stats.bevorzugte_jahrgangsstufe = None
        stats.save()

        return redirect('profil')

    jahrgangsstufen = Jahrgangsstufe.objects.all()

    context = {
        'jahrgangsstufen': jahrgangsstufen,
        'stats': stats,
    }
    return render(request, 'karteikarten/profil.html', context)


@login_required
def meine_lernbloecke(request):
    """Manage user's learning block selection."""
    from .models import Schulfach, Jahrgangsstufe

    user = request.user
    stats = BenutzerStatistik.get_or_create_for_user(user)

    # Get filter parameters - use preferred Jahrgangsstufe as default
    fach_id = request.GET.get('fach', '')
    stufe_id = request.GET.get('stufe', '')

    # If no filter set and user has preferred Jahrgangsstufe, use it
    if not stufe_id and not request.GET and stats.bevorzugte_jahrgangsstufe:
        stufe_id = str(stats.bevorzugte_jahrgangsstufe_id)

    nur_ausgewaehlt = request.GET.get('ausgewaehlt', '') == '1'

    # Get all available blocks
    alle_bloecke = Lernblock.objects.select_related('schulfach', 'jahrgangsstufe')

    # Apply filters
    if fach_id:
        alle_bloecke = alle_bloecke.filter(schulfach_id=fach_id)
    if stufe_id:
        alle_bloecke = alle_bloecke.filter(jahrgangsstufe_id=stufe_id)

    # Get user's selected blocks
    benutzer_block_ids = set(BenutzerLernblock.objects.filter(
        benutzer=user
    ).values_list('lernblock_id', flat=True))

    # Mark blocks as selected or not
    bloecke = []
    for block in alle_bloecke:
        ist_ausgewaehlt = block.id in benutzer_block_ids
        if nur_ausgewaehlt and not ist_ausgewaehlt:
            continue
        bloecke.append({
            'lernblock': block,
            'ausgewaehlt': ist_ausgewaehlt,
        })

    # Get filter options
    schulfaecher = Schulfach.objects.all()
    jahrgangsstufen = Jahrgangsstufe.objects.all()

    context = {
        'bloecke': bloecke,
        'schulfaecher': schulfaecher,
        'jahrgangsstufen': jahrgangsstufen,
        'filter_fach': fach_id,
        'filter_stufe': stufe_id,
        'filter_ausgewaehlt': nur_ausgewaehlt,
        'anzahl_ausgewaehlt': len(benutzer_block_ids),
    }
    return render(request, 'karteikarten/meine_lernbloecke.html', context)


@login_required
@require_POST
def lernblock_hinzufuegen(request, pk):
    """Add a learning block to user's selection."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    BenutzerLernblock.objects.get_or_create(
        benutzer=request.user,
        lernblock=lernblock
    )
    # Preserve filter parameters
    query_string = request.GET.urlencode()
    url = 'meine_lernbloecke'
    if query_string:
        return redirect(f"{{% url '{url}' %}}?{query_string}".replace("{{% url '{url}' %}}", f"/meine-lernbloecke/"))
    return redirect(url)


@login_required
@require_POST
def lernblock_entfernen(request, pk):
    """Remove a learning block from user's selection."""
    BenutzerLernblock.objects.filter(
        benutzer=request.user,
        lernblock_id=pk
    ).delete()
    # Preserve filter parameters
    query_string = request.GET.urlencode()
    url = 'meine_lernbloecke'
    if query_string:
        return redirect(f"/meine-lernbloecke/?{query_string}")
    return redirect(url)


@login_required
def lernblock_detail(request, pk):
    """Detail view for a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Check if user has this block
    hat_block = BenutzerLernblock.objects.filter(
        benutzer=user,
        lernblock=lernblock
    ).exists()

    # Calculate user-specific card distribution
    karten_verteilung = {i: 0 for i in range(1, 6)}
    for karte in lernblock.karten.all():
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        karten_verteilung[status.fach] += 1

    # Today's stats for this block and user
    heute_stats, _ = TagesStatistik.objects.get_or_create(
        benutzer=user,
        lernblock=lernblock,
        datum=date.today(),
    )

    context = {
        'lernblock': lernblock,
        'karten_verteilung': karten_verteilung,
        'heute_stats': heute_stats,
        'hat_block': hat_block,
    }
    return render(request, 'karteikarten/lernblock_detail.html', context)


@login_required
def lernblock_create(request):
    """Create a new learning block."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        beschreibung = request.POST.get('beschreibung', '').strip()
        lehrbuch = request.POST.get('lehrbuch', '').strip()
        bidirektional = request.POST.get('bidirektional') == 'on'

        if name:
            lernblock = Lernblock.objects.create(
                name=name,
                beschreibung=beschreibung,
                lehrbuch=lehrbuch,
                bidirektional=bidirektional
            )
            # Automatically add to user's blocks
            BenutzerLernblock.objects.create(
                benutzer=request.user,
                lernblock=lernblock
            )
            return redirect('lernblock_detail', pk=lernblock.pk)

    return render(request, 'karteikarten/lernblock_form.html', {'action': 'Erstellen'})


@login_required
def lernblock_edit(request, pk):
    """Edit a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)

    if request.method == 'POST':
        lernblock.name = request.POST.get('name', '').strip() or lernblock.name
        lernblock.beschreibung = request.POST.get('beschreibung', '').strip()
        lernblock.lehrbuch = request.POST.get('lehrbuch', '').strip()
        lernblock.bidirektional = request.POST.get('bidirektional') == 'on'
        lernblock.save()
        return redirect('lernblock_detail', pk=lernblock.pk)

    return render(request, 'karteikarten/lernblock_form.html', {
        'lernblock': lernblock,
        'action': 'Bearbeiten'
    })


@login_required
@require_POST
def lernblock_delete(request, pk):
    """Delete a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    lernblock.delete()
    return redirect('dashboard')


@login_required
def karten_liste(request, pk):
    """List all cards in a learning block."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    karten = lernblock.karten.all()

    # Search filter
    suche = request.GET.get('suche', '').strip()
    if suche:
        karten = karten.filter(begriff__icontains=suche) | karten.filter(definition__icontains=suche)

    context = {
        'lernblock': lernblock,
        'karten': karten,
        'suche': suche,
    }
    return render(request, 'karteikarten/karten_liste.html', context)


@login_required
def karte_create(request, pk):
    """Create a new flashcard."""
    lernblock = get_object_or_404(Lernblock, pk=pk)

    if request.method == 'POST':
        begriff = request.POST.get('begriff', '').strip()
        definition = request.POST.get('definition', '').strip()
        beispiele = request.POST.get('beispiele', '').strip()
        zusatz_label = request.POST.get('zusatz_label', '').strip()
        zusatz_wert = request.POST.get('zusatz_wert', '').strip()

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
            if request.POST.get('weitere'):
                return redirect('karte_create', pk=lernblock.pk)
            return redirect('karten_liste', pk=lernblock.pk)

    return render(request, 'karteikarten/karte_form.html', {
        'lernblock': lernblock,
        'action': 'Erstellen'
    })


@login_required
def karte_edit(request, pk):
    """Edit a flashcard."""
    karte = get_object_or_404(Karteikarte, pk=pk)

    if request.method == 'POST':
        karte.begriff = request.POST.get('begriff', '').strip() or karte.begriff
        karte.definition = request.POST.get('definition', '').strip() or karte.definition
        karte.beispiele = request.POST.get('beispiele', '').strip()
        karte.zusatz_label = request.POST.get('zusatz_label', '').strip()
        karte.zusatz_wert = request.POST.get('zusatz_wert', '').strip()
        karte.save()
        return redirect('karten_liste', pk=karte.lernblock.pk)

    return render(request, 'karteikarten/karte_form.html', {
        'karte': karte,
        'lernblock': karte.lernblock,
        'action': 'Bearbeiten'
    })


@login_required
@require_POST
def karte_delete(request, pk):
    """Delete a flashcard."""
    karte = get_object_or_404(Karteikarte, pk=pk)
    lernblock_pk = karte.lernblock.pk
    karte.delete()
    return redirect('karten_liste', pk=lernblock_pk)


@login_required
def csv_import(request, pk):
    """Import cards from CSV file."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    errors = []
    imported = 0

    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        has_header = request.POST.get('has_header') == 'on'

        if csv_file:
            try:
                decoded = csv_file.read().decode('utf-8')
                reader = csv.reader(io.StringIO(decoded), delimiter=';')

                for i, row in enumerate(reader):
                    if i == 0 and has_header:
                        continue

                    if len(row) < 2:
                        errors.append(f"Zeile {i+1}: Mindestens Begriff und Definition erforderlich")
                        continue

                    begriff = row[0].strip()
                    definition = row[1].strip()
                    beispiele = row[2].strip() if len(row) > 2 else ''
                    zusatz_label = row[3].strip() if len(row) > 3 else ''
                    zusatz_wert = row[4].strip() if len(row) > 4 else ''

                    if not begriff or not definition:
                        errors.append(f"Zeile {i+1}: Begriff oder Definition leer")
                        continue

                    _, created = Karteikarte.objects.get_or_create(
                        lernblock=lernblock,
                        begriff=begriff,
                        defaults={
                            'definition': definition,
                            'beispiele': beispiele,
                            'zusatz_label': zusatz_label,
                            'zusatz_wert': zusatz_wert,
                        }
                    )
                    if created:
                        imported += 1

            except Exception as e:
                errors.append(f"Fehler beim Lesen der Datei: {str(e)}")

        if imported > 0 and not errors:
            return redirect('karten_liste', pk=lernblock.pk)

    return render(request, 'karteikarten/csv_import.html', {
        'lernblock': lernblock,
        'errors': errors,
        'imported': imported,
    })


# Learning modes

def _get_faellige_karten(user, lernblock, limit=20):
    """Get due cards for a user, sorted by box (lower first)."""
    faellige = []
    for karte in lernblock.karten.all():
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        if status.ist_faellig:
            faellige.append((karte, status))

    # Sort by box (lower first)
    faellige.sort(key=lambda x: x[1].fach)
    return faellige[:limit]


def _get_faellige_karten_multi(user, lernbloecke, limit=50):
    """Get due cards from multiple blocks for a user, sorted by box (lower first)."""
    faellige = []
    for lernblock in lernbloecke:
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            if status.ist_faellig:
                faellige.append((karte, status))

    # Sort by box (lower first), then shuffle within same box for variety
    faellige.sort(key=lambda x: (x[1].fach, random.random()))
    return faellige[:limit]


@login_required
@require_POST
def karten_zuruecksetzen(request, pk):
    """Reset all cards in a block to be available for learning today."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Reset all card statuses to today
    for karte in lernblock.karten.all():
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        status.naechste_wiederholung = date.today()
        status.save()

    # Redirect back to the learning mode they came from
    modus = request.POST.get('modus', 'klassisch')
    if modus == 'rueckwaerts':
        return redirect('lernen_rueckwaerts', pk=pk)
    elif modus == 'multiple_choice':
        return redirect('lernen_multiple_choice', pk=pk)
    return redirect('lernen_klassisch', pk=pk)


@login_required
def lernen_klassisch(request, pk):
    """Classic learning mode: show term, reveal definition."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    faellige = _get_faellige_karten(user, lernblock)

    if not faellige:
        return render(request, 'karteikarten/lernen_fertig.html', {
            'lernblock': lernblock,
            'modus': 'klassisch',
        })

    karte, status = faellige[0]

    context = {
        'lernblock': lernblock,
        'karte': karte,
        'status': status,
        'modus': 'klassisch',
        'verbleibend': len(faellige),
    }
    return render(request, 'karteikarten/lernen_karte.html', context)


@login_required
def lernen_rueckwaerts(request, pk):
    """Reverse learning mode: show definition, reveal term."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    if not lernblock.bidirektional:
        return redirect('lernblock_detail', pk=pk)

    faellige = _get_faellige_karten(user, lernblock)

    if not faellige:
        return render(request, 'karteikarten/lernen_fertig.html', {
            'lernblock': lernblock,
            'modus': 'rueckwaerts',
        })

    karte, status = faellige[0]

    context = {
        'lernblock': lernblock,
        'karte': karte,
        'status': status,
        'modus': 'rueckwaerts',
        'verbleibend': len(faellige),
    }
    return render(request, 'karteikarten/lernen_karte.html', context)


@login_required
def lernen_multiple_choice(request, pk):
    """Multiple choice learning mode."""
    lernblock = get_object_or_404(Lernblock, pk=pk)
    user = request.user

    # Need at least 4 cards for multiple choice
    alle_karten = list(lernblock.karten.all())
    if len(alle_karten) < 4:
        return render(request, 'karteikarten/lernen_fertig.html', {
            'lernblock': lernblock,
            'modus': 'multiple_choice',
            'error': 'Mindestens 4 Karten für Multiple Choice benötigt.',
        })

    faellige = _get_faellige_karten(user, lernblock)

    if not faellige:
        return render(request, 'karteikarten/lernen_fertig.html', {
            'lernblock': lernblock,
            'modus': 'multiple_choice',
        })

    karte, status = faellige[0]

    # Get 3 distractors
    andere_karten = [k for k in alle_karten if k.pk != karte.pk]
    distraktoren = random.sample(andere_karten, min(3, len(andere_karten)))

    # Build answer options
    optionen = [
        {'text': karte.definition, 'korrekt': True, 'karte_id': karte.pk}
    ]
    for d in distraktoren:
        optionen.append({'text': d.definition, 'korrekt': False, 'karte_id': d.pk})

    random.shuffle(optionen)

    context = {
        'lernblock': lernblock,
        'karte': karte,
        'status': status,
        'optionen': optionen,
        'modus': 'multiple_choice',
        'verbleibend': len(faellige),
    }
    return render(request, 'karteikarten/lernen_multiple_choice.html', context)


@login_required
@require_POST
def karte_antwort(request, pk):
    """Process answer for a card (AJAX endpoint)."""
    karte = get_object_or_404(Karteikarte, pk=pk)
    user = request.user
    richtig = request.POST.get('richtig') == 'true'
    modus = request.POST.get('modus', 'klassisch')

    # Get user's card status
    status = BenutzerKarteStatus.get_or_create_for_user(user, karte)

    # Update status based on answer
    if richtig:
        status.richtig_beantwortet()
    else:
        status.falsch_beantwortet()

    # Record result
    Lernergebnis.objects.create(
        benutzer=user,
        karte=karte,
        modus=modus,
        richtig=richtig
    )

    # Update daily stats
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

    # Update user statistics
    benutzer_stats = BenutzerStatistik.get_or_create_for_user(user)
    benutzer_stats.gesamt_gelernt += 1
    if richtig:
        benutzer_stats.gesamt_richtig += 1
        benutzer_stats.update_streak()
    benutzer_stats.save()

    return JsonResponse({
        'success': True,
        'neues_fach': status.fach,
        'naechste_wiederholung': str(status.naechste_wiederholung),
    })


# Combined learning (multiple blocks)

@login_required
def lernen_kombiniert_auswahl(request):
    """Select multiple blocks for combined learning."""
    user = request.user

    # Get user's selected blocks
    benutzer_bloecke = BenutzerLernblock.objects.filter(
        benutzer=user
    ).select_related('lernblock')

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
        bloecke.append({
            'lernblock': lernblock,
            'faellig': faellig,
            'anzahl': lernblock.anzahl_karten,
        })

    context = {
        'bloecke': bloecke,
        'total_faellig': total_faellig,
    }
    return render(request, 'karteikarten/lernen_kombiniert_auswahl.html', context)


@login_required
def lernen_kombiniert(request):
    """Combined learning mode for multiple blocks (classic mode)."""
    user = request.user

    # Get block IDs from query params
    block_ids = request.GET.get('bloecke', '').split(',')
    block_ids = [int(bid) for bid in block_ids if bid.isdigit()]

    if not block_ids:
        return redirect('lernen_kombiniert_auswahl')

    # Get blocks that user has access to
    lernbloecke = list(Lernblock.objects.filter(
        pk__in=block_ids,
        benutzer_zuordnungen__benutzer=user
    ))

    if not lernbloecke:
        return redirect('lernen_kombiniert_auswahl')

    faellige = _get_faellige_karten_multi(user, lernbloecke)

    if not faellige:
        return render(request, 'karteikarten/lernen_kombiniert_fertig.html', {
            'lernbloecke': lernbloecke,
            'block_ids': ','.join(str(b.pk) for b in lernbloecke),
            'modus': 'klassisch',
        })

    karte, status = faellige[0]

    context = {
        'lernbloecke': lernbloecke,
        'block_ids': ','.join(str(b.pk) for b in lernbloecke),
        'karte': karte,
        'status': status,
        'modus': 'klassisch',
        'verbleibend': len(faellige),
    }
    return render(request, 'karteikarten/lernen_kombiniert_karte.html', context)


@login_required
def lernen_kombiniert_mc(request):
    """Combined learning mode for multiple blocks (multiple choice)."""
    user = request.user

    # Get block IDs from query params
    block_ids = request.GET.get('bloecke', '').split(',')
    block_ids = [int(bid) for bid in block_ids if bid.isdigit()]

    if not block_ids:
        return redirect('lernen_kombiniert_auswahl')

    # Get blocks that user has access to
    lernbloecke = list(Lernblock.objects.filter(
        pk__in=block_ids,
        benutzer_zuordnungen__benutzer=user
    ))

    if not lernbloecke:
        return redirect('lernen_kombiniert_auswahl')

    # Get all cards from all blocks for distractors
    alle_karten = []
    for lb in lernbloecke:
        alle_karten.extend(list(lb.karten.all()))

    if len(alle_karten) < 4:
        return render(request, 'karteikarten/lernen_kombiniert_fertig.html', {
            'lernbloecke': lernbloecke,
            'block_ids': ','.join(str(b.pk) for b in lernbloecke),
            'modus': 'multiple_choice',
            'error': 'Mindestens 4 Karten insgesamt fuer Multiple Choice benoetigt.',
        })

    faellige = _get_faellige_karten_multi(user, lernbloecke)

    if not faellige:
        return render(request, 'karteikarten/lernen_kombiniert_fertig.html', {
            'lernbloecke': lernbloecke,
            'block_ids': ','.join(str(b.pk) for b in lernbloecke),
            'modus': 'multiple_choice',
        })

    karte, status = faellige[0]

    # Get 3 distractors from all blocks
    andere_karten = [k for k in alle_karten if k.pk != karte.pk]
    distraktoren = random.sample(andere_karten, min(3, len(andere_karten)))

    # Build answer options
    optionen = [
        {'text': karte.definition, 'korrekt': True, 'karte_id': karte.pk}
    ]
    for d in distraktoren:
        optionen.append({'text': d.definition, 'korrekt': False, 'karte_id': d.pk})

    random.shuffle(optionen)

    context = {
        'lernbloecke': lernbloecke,
        'block_ids': ','.join(str(b.pk) for b in lernbloecke),
        'karte': karte,
        'status': status,
        'optionen': optionen,
        'modus': 'multiple_choice',
        'verbleibend': len(faellige),
    }
    return render(request, 'karteikarten/lernen_kombiniert_mc.html', context)


@login_required
@require_POST
def karten_zuruecksetzen_kombiniert(request):
    """Reset all cards in selected blocks to be available for learning today."""
    user = request.user
    block_ids = request.POST.get('bloecke', '').split(',')
    block_ids = [int(bid) for bid in block_ids if bid.isdigit()]

    lernbloecke = Lernblock.objects.filter(
        pk__in=block_ids,
        benutzer_zuordnungen__benutzer=user
    )

    for lernblock in lernbloecke:
        for karte in lernblock.karten.all():
            status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
            status.naechste_wiederholung = date.today()
            status.save()

    modus = request.POST.get('modus', 'klassisch')
    block_param = ','.join(str(bid) for bid in block_ids)

    if modus == 'multiple_choice':
        return redirect(f'/lernen/kombiniert/multiple-choice/?bloecke={block_param}')
    return redirect(f'/lernen/kombiniert/?bloecke={block_param}')


# PWA

def manifest(request):
    """PWA manifest."""
    return render(request, 'karteikarten/manifest.json', content_type='application/manifest+json')


def service_worker(request):
    """Service worker for PWA."""
    return render(request, 'karteikarten/sw.js', content_type='application/javascript')


def js_db(request):
    """IndexedDB wrapper JavaScript."""
    return render(request, 'karteikarten/js/db.js', content_type='application/javascript')


def js_sync(request):
    """Sync JavaScript."""
    return render(request, 'karteikarten/js/sync.js', content_type='application/javascript')


def js_offline_learning(request):
    """Offline learning JavaScript."""
    return render(request, 'karteikarten/js/offline-learning.js', content_type='application/javascript')


@login_required
def lernen_offline(request):
    """Offline learning page."""
    return render(request, 'karteikarten/lernen_offline.html')


# =============================================================================
# Offline Sync API
# =============================================================================

@login_required
def sync_pull(request):
    """Pull all data for offline use."""
    user = request.user

    # Alle Lernblöcke des Benutzers
    lernbloecke = Lernblock.objects.filter(
        benutzer_zuordnungen__benutzer=user
    ).values('id', 'name', 'beschreibung', 'thema', 'bidirektional')

    # Alle Karten aus diesen Blöcken
    lernblock_ids = [b['id'] for b in lernbloecke]
    karten = Karteikarte.objects.filter(
        lernblock_id__in=lernblock_ids
    ).values('id', 'lernblock_id', 'begriff', 'definition', 'beispiele',
             'zusatz_label', 'zusatz_wert')

    # Benutzer-Status für alle Karten
    karten_ids = [k['id'] for k in karten]
    status_list = BenutzerKarteStatus.objects.filter(
        benutzer=user,
        karte_id__in=karten_ids
    ).values('karte_id', 'fach', 'naechste_wiederholung')

    # Status als Dict mit karte_id als Key formatieren
    status_data = []
    for s in status_list:
        status_data.append({
            'karte_id': s['karte_id'],
            'fach': s['fach'],
            'naechste_wiederholung': s['naechste_wiederholung'].isoformat() if s['naechste_wiederholung'] else None
        })

    return JsonResponse({
        'lernbloecke': list(lernbloecke),
        'karten': list(karten),
        'status': status_data,
        'timestamp': date.today().isoformat()
    })


@login_required
@require_POST
def sync_push(request):
    """Push offline changes to server."""
    import json
    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if data.get('type') == 'antwort':
        karte_id = data.get('karte_id')
        richtig = data.get('richtig', False)
        modus = data.get('modus', 'klassisch')

        try:
            karte = Karteikarte.objects.get(pk=karte_id)
        except Karteikarte.DoesNotExist:
            return JsonResponse({'error': 'Karte not found'}, status=404)

        # Status aktualisieren
        status = BenutzerKarteStatus.get_or_create_for_user(user, karte)
        if richtig:
            status.richtig_beantwortet()
        else:
            status.falsch_beantwortet()

        # Lernergebnis speichern
        Lernergebnis.objects.create(
            benutzer=user,
            karte=karte,
            modus=modus,
            richtig=richtig
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

        return JsonResponse({
            'success': True,
            'karte_id': karte_id,
            'neuer_status': {
                'fach': status.fach,
                'naechste_wiederholung': status.naechste_wiederholung.isoformat()
            }
        })

    return JsonResponse({'error': 'Unknown action type'}, status=400)


# =============================================================================
# Admin: User Management
# =============================================================================

@staff_required
def benutzer_liste(request):
    """List all users (admin only)."""
    benutzer = User.objects.all().order_by('username')

    # Add stats to each user
    benutzer_mit_stats = []
    for user in benutzer:
        stats = BenutzerStatistik.get_or_create_for_user(user)
        benutzer_mit_stats.append({
            'user': user,
            'stats': stats,
            'bloecke': user.lernbloecke.count(),
        })

    context = {
        'benutzer_liste': benutzer_mit_stats,
    }
    return render(request, 'karteikarten/admin/benutzer_liste.html', context)


@staff_required
def benutzer_erstellen(request):
    """Create a new user (admin only)."""
    errors = []

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'

        # Validation
        if not username:
            errors.append('Benutzername ist erforderlich.')
        elif User.objects.filter(username=username).exists():
            errors.append('Benutzername existiert bereits.')

        if not password:
            errors.append('Passwort ist erforderlich.')
        elif len(password) < 6:
            errors.append('Passwort muss mindestens 6 Zeichen haben.')

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
            return redirect('benutzer_liste')

    return render(request, 'karteikarten/admin/benutzer_form.html', {
        'errors': errors,
        'action': 'erstellen',
    })


@staff_required
def benutzer_bearbeiten(request, pk):
    """Edit an existing user (admin only)."""
    user = get_object_or_404(User, pk=pk)
    stats = BenutzerStatistik.get_or_create_for_user(user)
    errors = []

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        reset_password = request.POST.get('reset_password', '').strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_staff = is_staff
        user.is_active = is_active

        if reset_password:
            if len(reset_password) < 6:
                errors.append('Passwort muss mindestens 6 Zeichen haben.')
            else:
                user.set_password(reset_password)
                stats.muss_passwort_aendern = True
                stats.save()

        if not errors:
            user.save()
            messages.success(request, f'Benutzer "{user.username}" wurde aktualisiert.')
            return redirect('benutzer_liste')

    return render(request, 'karteikarten/admin/benutzer_form.html', {
        'benutzer': user,
        'benutzer_stats': stats,
        'errors': errors,
        'action': 'bearbeiten',
    })


@staff_required
@require_POST
def benutzer_loeschen(request, pk):
    """Delete a user (admin only)."""
    user = get_object_or_404(User, pk=pk)

    # Don't allow deleting yourself
    if user == request.user:
        messages.error(request, 'Du kannst dich nicht selbst loeschen.')
        return redirect('benutzer_liste')

    username = user.username
    user.delete()
    messages.success(request, f'Benutzer "{username}" wurde geloescht.')
    return redirect('benutzer_liste')


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

    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validation
        if not user.check_password(current_password):
            errors.append('Aktuelles Passwort ist falsch.')

        if not new_password:
            errors.append('Neues Passwort ist erforderlich.')
        elif len(new_password) < 6:
            errors.append('Neues Passwort muss mindestens 6 Zeichen haben.')

        if new_password != confirm_password:
            errors.append('Passwoerter stimmen nicht ueberein.')

        if current_password == new_password:
            errors.append('Neues Passwort muss sich vom aktuellen unterscheiden.')

        if not errors:
            user.set_password(new_password)
            user.save()

            # Clear the force change flag
            stats.muss_passwort_aendern = False
            stats.save()

            # Keep user logged in
            update_session_auth_hash(request, user)

            messages.success(request, 'Passwort wurde erfolgreich geaendert.')
            return redirect('dashboard')

    return render(request, 'karteikarten/passwort_aendern.html', {
        'errors': errors,
        'force_change': force_change,
    })


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
            lehrwerk_stats.append({
                'name': str(lw),
                'anzahl_karten': anzahl,
                'anzahl_units': lw.anzahl_units,
            })

    context = {
        'backups': backups,
        'lehrwerk_stats': lehrwerk_stats,
        'total_karten': total_karten,
    }
    return render(request, 'karteikarten/admin/backup_liste.html', context)


@staff_required
@require_POST
def backup_erstellen(request):
    """Create a new backup."""
    from .services.json_exporter import JSONExporter

    exporter = JSONExporter()
    modus = request.POST.get('modus', 'einzeln')

    if modus == 'single':
        filepath = exporter.backup_all_to_single_file()
        messages.success(request, f'Backup erstellt: {filepath.name}')
    else:
        files = exporter.backup_all(include_timestamp=True)
        messages.success(request, f'{len(files)} Backup-Dateien erstellt.')

    return redirect('backup_liste')


@staff_required
def backup_download(request, filename):
    """Download a backup file."""
    from django.http import FileResponse
    from .services.json_exporter import JSONExporter

    exporter = JSONExporter()
    filepath = exporter.backup_dir / filename

    if not filepath.exists() or not filepath.is_file():
        messages.error(request, 'Backup-Datei nicht gefunden.')
        return redirect('backup_liste')

    # Security: ensure the file is in the backup directory
    try:
        filepath.resolve().relative_to(exporter.backup_dir.resolve())
    except ValueError:
        messages.error(request, 'Ungueltiger Dateipfad.')
        return redirect('backup_liste')

    return FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename=filename
    )
