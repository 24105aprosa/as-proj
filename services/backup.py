import subprocess
import os
import tarfile
import shutil
from datetime import datetime
from core.framework import run_pipeline, step, exists

# ///// Backup paths /////
BACKUP_ROOT = "/var/backups"
TAR_DIR = "/var/backups/snapshots"
RSYNC_DIR = "/var/backups/rsync"

# ///// Backup targets /////
DEFAULT_TARGETS = [
    "/home",
    "/etc",
    "/var/www",
    "/etc/samba",
    "/etc/exports",
    "/var/named"
]

# ///// Helpers /////
def _ensure_dirs():
    for path in [BACKUP_ROOT, TAR_DIR, RSYNC_DIR]:
        if not os.path.exists(path):
            os.makedirs(path)


def _latest_rsync_backup():
    if not os.path.exists(RSYNC_DIR):
        return None

    entries = sorted(os.listdir(RSYNC_DIR))
    if not entries:
        return None

    return os.path.join(RSYNC_DIR, entries[-1])

# ///// TAR snapshot backup /////
def _tar_backup(paths):
    _ensure_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = os.path.join(TAR_DIR, "snapshot_{}.tar.gz".format(timestamp))

    cmd = ["tar", "-czf", archive] + paths

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("[!] TAR backup failed")
        return False

    print("[+] Snapshot created:", archive)
    return True

# ///// RSYNC incremental backup /////
def _rsync_backup(source="/home"):
    _ensure_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(RSYNC_DIR, timestamp)

    os.makedirs(target)

    last = _latest_rsync_backup()

    cmd = ["rsync", "-a", "--delete"]

    if last:
        cmd.append("--link-dest={}".format(last))

    cmd += [source + "/", target]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("[!] RSYNC backup failed")
        return False

    print("[+] Incremental backup created:", target)
    return True

# ///// TAR snapshot restore /////
def _tar_restore(archive_path, target="/"):
    if not os.path.exists(archive_path):
        print("[!] Snapshot not found")
        return False

    print("[*] Restoring TAR snapshot:", archive_path)

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=target)
    except Exception as e:
        print("[!] Restore failed:", e)
        return False

    print("[+] TAR restore complete")
    return True

# ///// RSYNC incremental restore /////
def _rsync_restore(snapshot_path, target="/"):
    if not os.path.exists(snapshot_path):
        print("[!] Snapshot not found")
        return False

    print("[*] Restoring RSYNC snapshot:", snapshot_path)

    cmd = [
        "rsync",
        "-a",
        "--delete",
        snapshot_path + "/",
        target
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("[!] RSYNC restore failed")
        return False

    print("[+] RSYNC restore complete")
    return True

# ///// Pipeline wrappers /////
def run_full_snapshot_backup(paths=DEFAULT_TARGETS):
    return run_pipeline("TAR SNAPSHOT BACKUP", [
        step("Create snapshot archive", lambda: _tar_backup(paths))
    ])


def run_home_incremental_backup():
    return run_pipeline("RSYNC INCREMENTAL BACKUP", [
        step("Create incremental backup", lambda: _rsync_backup("/home"))
    ])


def run_full_incremental_backup():
    return run_pipeline("RSYNC FULL SYSTEM BACKUP", [
        step("Backup system state", lambda: _rsync_backup("/"))
    ])

def run_tar_restore(archive_path):
    return run_pipeline("TAR RESTORE", [
        step("Restore snapshot", lambda: _tar_restore(archive_path))
    ])

def run_rsync_restore(snapshot_path):
    return run_pipeline("RSYNC RESTORE", [
        step("Restore incremental backup", lambda: _rsync_restore(snapshot_path))
    ])

def run_backups_inspect():
    print("\n[TAR SNAPSHOTS]")
    for f in sorted(os.listdir(TAR_DIR)):
        print(" -", f)

    print("\n[RSYNC SNAPSHOTS]")
    for f in sorted(os.listdir(RSYNC_DIR)):
        print(" -", f)

    return True