"""
Background scheduler for automatic JSON import.

Scans the import directory periodically and imports new files automatically.
Uses a file lock to prevent multiple workers from importing simultaneously.
"""
import fcntl
import logging
import os
import threading
from pathlib import Path

from django.conf import settings

logger = logging.getLogger('karteikarten')

# Global state
_scheduler_thread = None
_stop_event = threading.Event()
_lock_file = None


def _acquire_lock() -> bool:
    """Try to acquire the import lock. Returns True if acquired."""
    global _lock_file

    lock_path = Path(settings.KARTEIKARTEN_IMPORT_DIR) / '.import.lock'
    try:
        _lock_file = open(lock_path, 'w')
        fcntl.flock(_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True
    except (IOError, OSError):
        # Another process has the lock
        if _lock_file:
            _lock_file.close()
            _lock_file = None
        return False


def _release_lock():
    """Release the import lock."""
    global _lock_file

    if _lock_file:
        try:
            fcntl.flock(_lock_file.fileno(), fcntl.LOCK_UN)
            _lock_file.close()
        except (IOError, OSError):
            pass
        _lock_file = None


def scan_and_import():
    """Scan import directory and import new files."""
    # Import here to avoid circular imports
    from karteikarten.services.json_importer import JSONImporter

    import_dir = Path(settings.KARTEIKARTEN_IMPORT_DIR)

    if not import_dir.exists():
        logger.warning(f"[ImportScheduler] Import directory does not exist: {import_dir}")
        return

    json_files = list(import_dir.glob('*.json'))
    if not json_files:
        return

    # Try to acquire lock - if another worker has it, skip this scan
    if not _acquire_lock():
        logger.debug("[ImportScheduler] Another worker is importing, skipping this scan")
        return

    try:
        importer = JSONImporter()
        for json_file in json_files:
            # Re-check if file still exists (another worker might have processed it)
            if not json_file.exists():
                continue

            logger.info(f"[ImportScheduler] Processing: {json_file.name}")
            try:
                log = importer.import_file(json_file)

                if log.status == 'success':
                    logger.info(
                        f"[ImportScheduler] Imported {json_file.name}: "
                        f"{log.anzahl_bloecke} blocks, {log.anzahl_karten} cards - "
                        f"archived to {log.archiv_pfad}"
                    )
                elif log.status == 'skipped':
                    logger.info(
                        f"[ImportScheduler] Skipped {json_file.name}: "
                        f"Already imported (hash match) - archived to {log.archiv_pfad}"
                    )
                else:
                    logger.warning(
                        f"[ImportScheduler] Failed {json_file.name}: {log.nachricht}"
                    )
            except Exception as e:
                logger.error(f"[ImportScheduler] Error {json_file.name}: {e}")
    finally:
        _release_lock()


def _scheduler_loop(interval_seconds: int):
    """Main scheduler loop running in background thread."""
    import_dir = Path(settings.KARTEIKARTEN_IMPORT_DIR)
    archive_dir = Path(settings.KARTEIKARTEN_ARCHIVE_DIR)

    logger.info(
        f"[ImportScheduler] Started - scanning every {interval_seconds}s\n"
        f"  Import directory:  {import_dir}\n"
        f"  Archive directory: {archive_dir}"
    )

    scan_count = 0
    while not _stop_event.is_set():
        scan_count += 1
        try:
            json_files = list(import_dir.glob('*.json')) if import_dir.exists() else []
            if json_files:
                logger.info(
                    f"[ImportScheduler] Scan #{scan_count}: Found {len(json_files)} file(s) - "
                    f"{', '.join(f.name for f in json_files)}"
                )
                scan_and_import()
            else:
                # Log every 10th scan to show scheduler is alive
                if scan_count % 10 == 0:
                    logger.info(
                        f"[ImportScheduler] Scan #{scan_count}: No files - "
                        f"watching {import_dir}"
                    )
        except Exception as e:
            logger.error(f"[ImportScheduler] Scan #{scan_count}: Error - {e}")

        # Wait for interval or stop event
        _stop_event.wait(timeout=interval_seconds)

    logger.info("[ImportScheduler] Stopped")


def start_scheduler(interval_seconds: int = 60):
    """
    Start the background import scheduler.

    Args:
        interval_seconds: How often to scan for new files (default: 60s)
    """
    global _scheduler_thread, _stop_event

    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logger.warning("Import scheduler already running")
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        args=(interval_seconds,),
        daemon=True,
        name="ImportScheduler"
    )
    _scheduler_thread.start()


def stop_scheduler():
    """Stop the background import scheduler."""
    global _scheduler_thread, _stop_event

    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        return

    _stop_event.set()
    _scheduler_thread.join(timeout=5)
    _scheduler_thread = None


def is_running() -> bool:
    """Check if the scheduler is running."""
    return _scheduler_thread is not None and _scheduler_thread.is_alive()
