import subprocess
import os
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
        if not exists(path):
            os.makedirs(path)

def _latest_rsync_backup():
    if not exists(RSYNC_DIR):
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

    valid_paths = []
    for p in paths:
        if exists(p):
            valid_paths.append(p.lstrip("/"))
        else:
            print(f"Diretoria não existe: {p}, ignorando")

    if not valid_paths:
        print("[!] Sem diretorias válidas para backup")
        return False

    cmd = [
        "tar",
        "-czf",
        archive,
        "-C", "/"
    ] + valid_paths

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("[!] Snapshot TAR falhou")
        return False

    print("[+] Snapshot criado:", archive)
    return True

# ///// RSYNC incremental backup /////
def _rsync_backup():
    _ensure_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(RSYNC_DIR, timestamp)

    os.makedirs(target)

    last = _latest_rsync_backup()

    # Get actual user directories
    users = [
        d for d in os.listdir("/home")
        if os.path.isdir(os.path.join("/home", d))
    ]

    success = True

    for user in users:
        src = f"/home/{user}/"
        dst = os.path.join(target, user)

        cmd = ["rsync", "-a", "--delete"]

        if last:
            cmd.append(f"--link-dest={os.path.join(last, user)}")

        cmd += [src, dst]

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"[!] Falhou backup do utilizador: {user}")
            success = False

    if success:
        print("[+] Backup de utilizador criado:", target)

    return success

# ///// TAR snapshot restore /////
def _tar_restore(archive_path, target="/"):
    if not exists(archive_path):
        print("[!] Snapshot não encontrado")
        return False

    print("Recuperando snapshot TAR:", archive_path)

    try:
        result = subprocess.run([
            "tar",
            "-xzf",
            archive_path,
            "-C",
            target
        ])

        if result.returncode != 0:
            print("[!] Recuperação falhou")
            return False

    except Exception as e:
        print("[!] Exceção:", e)
        return False

    print("[+] Recuperação TAR concluída")
    return True

# ///// RSYNC incremental restore /////
def _rsync_restore(snapshot_path):
    if not exists(snapshot_path):
        print("[!] Snapshot não encontrado")
        return False

    print("Recuperando diretorias /home/*utilizador* de:", snapshot_path)

    users = [
        d for d in os.listdir(snapshot_path)
        if os.path.isdir(os.path.join(snapshot_path, d))
    ]

    success = True

    for user in users:
        src = os.path.join(snapshot_path, user) + "/"
        dst = f"/home/{user}/"

        print(f"Recuperando {user}...")

        cmd = [
            "rsync",
            "-a",
            "--delete",
            src,
            dst
        ]

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"[!] Falhou a recuperação do utilizador: {user}")
            success = False

    if success:
        print("[+] RSYNC restore complete")

    return success

# ///// Pipeline wrappers /////
def run_full_snapshot_backup(paths=DEFAULT_TARGETS):
    return run_pipeline("TAR SNAPSHOT BACKUP", [
        step("Criar arquivo TAR", lambda: _tar_backup(paths))
    ])

def run_home_incremental_backup():
    return run_pipeline("RSYNC USER BACKUP", [
        step("Guardar diretorias de utilizadores", _rsync_backup)
    ])

def run_tar_restore(archive_path):
    return run_pipeline("TAR RESTORE", [
        step("Recuperar snapshot", lambda: _tar_restore(archive_path))
    ])

def run_rsync_restore(snapshot_path):
    return run_pipeline("RSYNC RESTORE", [
        step("Recuperar backup incremental", lambda: _rsync_restore(snapshot_path))
    ])

def run_backups_inspect():
    print("\n[TAR SNAPSHOTS]")
    for f in sorted(os.listdir(TAR_DIR)):
        print(" -", f)

    print("\n[RSYNC BACKUPS]")
    for f in sorted(os.listdir(RSYNC_DIR)):
        print(" -", f)

    return True