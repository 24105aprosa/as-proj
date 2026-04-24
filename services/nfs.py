import subprocess
import re
from core.framework import run_pipeline, step, exists

EXPORTS_FILE = "/etc/exports"

# ///// Helpers /////
def _parse_exports():
    shares = []

    if not exists(EXPORTS_FILE):
        return shares

    with open(EXPORTS_FILE, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        match = re.match(r"(\S+)\s+(\S+)\((.+)\)", line)
        if match:
            path, client, options = match.groups()
            shares.append({
                "path": path,
                "client": client,
                "options": options
            })

    return shares
    
def _add_share(path, client, options):
    shares = _parse_exports()

    for s in shares:
        if s["path"] == path and s["client"] == client:
            print("Partilha já existe")
            return True

    with open(EXPORTS_FILE, "a") as f:
        f.write(f"{path} {client}({options})\n")

    print("[+] Partilha adicionada")
    return True

def _remove_share(path, client=None):
    if not exists(EXPORTS_FILE):
        return True

    shares = _parse_exports()

    with open(EXPORTS_FILE, "w") as f:
        for s in shares:
            if s["path"] == path and (client is None or s["client"] == client):
                continue

            f.write(f"{s['path']} {s['client']}({s['options']})\n")

    print("[+] Partilha apagada")
    return True

def _disable_share(path):
    if not exists(EXPORTS_FILE):
        return True

    shares = _parse_exports()

    with open(EXPORTS_FILE, "w") as f:
        for s in shares:
            line = f"{s['path']} {s['client']}({s['options']})\n"

            if s["path"] == path:
                f.write("# " + line)
            else:
                f.write(line)

    print("[+] Partilha desativada")
    return True

def _edit_share(path, new_path, new_client, new_options):
    shares = _parse_exports()

    updated = False

    with open(EXPORTS_FILE, "w") as f:
        for s in shares:
            if s["path"] == path:
                s = {
                    "path": new_path,
                    "client": new_client,
                    "options": new_options
                }
                updated = True

            f.write(f"{s['path']} {s['client']}({s['options']})\n")

    if not updated:
        print("[!] Partilha não encontrada")
        return False

    print("[+] Partilha atualizada")
    return True

def _apply_nfs():
    subprocess.run(["exportfs", "-rav"], check=True)
    subprocess.run(["systemctl", "restart", "nfs-server"], check=True)
    return True

# ///// Pipeline wrappers /////
def run_nfs_add_share(path, client, options):
    return run_pipeline("NFS ADD SHARE", [
        step("Adicionar partilha", lambda: _add_share(path, client, options)),
        step("Reiniciar nfs-server", _apply_nfs),
    ])

def run_nfs_remove_share(path):
    return run_pipeline("NFS REMOVE SHARE", [
        step("Apagar partilha", lambda: _remove_share(path)),
        step("Reiniciar nfs-server", _apply_nfs),
    ])

def run_nfs_disable_share(path):
    return run_pipeline("NFS DISABLE SHARE", [
        step("Desativar partilha", lambda: _disable_share(path)),
        step("Reiniciar nfs-server", _apply_nfs),
    ])

def run_nfs_edit_share(index, path, client, options):
    return run_pipeline("NFS EDIT SHARE", [
        step("Editar partilha", lambda: _edit_share(index, path, client, options)),
        step("Reiniciar nfs-server", _apply_nfs),
    ])

def run_nfs_inspect():
    shares = _parse_exports()

    if not shares:
        print("Sem partilhas NFS configuradas")
        return True

    print("\nPARTILHAS NFS:")
    print("-" * 40)

    for i, s in enumerate(shares, 1):
        print(f"[{i}] Path: {s['path']}")
        print(f"    Cliente: {s['client']}")
        print(f"    Opções: {s['options']}\n")

    return True