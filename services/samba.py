import subprocess
import pwd
import re
from core.framework import run_pipeline, step, exists

SMB_CONF = "/etc/samba/smb.conf"

# ///// Helpers /////

def _linux_user_exists(username):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def _read_conf():
    if not exists(SMB_CONF):
        return ""
    with open(SMB_CONF, "r") as f:
        return f.read()


def _parse_smb_conf():
    if not exists(SMB_CONF):
        return {}

    with open(SMB_CONF, "r") as f:
        lines = f.readlines()

    blocks = {}
    current = None
    buffer = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("[") and stripped.endswith("]"):
            if current:
                blocks[current] = buffer

            current = stripped[1:-1]
            buffer = [line]
        else:
            if current:
                buffer.append(line)

    if current:
        blocks[current] = buffer

    return blocks


def _write_smb_conf(blocks):
    with open(SMB_CONF, "w") as f:
        for name, lines in blocks.items():
            f.writelines(lines)
            if not lines[-1].endswith("\n"):
                f.write("\n")


def _add_share(name, path, user, read_only="no"):
    blocks = _parse_smb_conf()

    if name in blocks:
        print("Partilha já existe")
        return True

    blocks[name] = [
        f"[{name}]\n",
        f"    path = {path}\n",
        "    browseable = yes\n",
        f"    read only = {read_only}\n",
        f"    valid users = {user}\n"
    ]

    _write_smb_conf(blocks)

    print("[+] Partilha Samba adicionada")
    return True


def _remove_share(name):
    blocks = _parse_smb_conf()

    if name in blocks:
        del blocks[name]
        _write_smb_conf(blocks)
        print("[+] Partilha Samba removida")
    else:
        print("Partilha não encontrada")

    return True


def _disable_share(name):
    blocks = _parse_smb_conf()

    if name not in blocks:
        print("Partilha não encontrada")
        return True

    commented = []
    for line in blocks[name]:
        if not line.startswith("#"):
            commented.append("#" + line.rstrip("\n"))
        else:
            commented.append(line)

    blocks[name] = ["# DISABLED\n"] + commented
    _write_smb_conf(blocks)

    print("[+] Partilha Samba desativada")
    return True


def _edit_share(name, path, user, read_only):
    blocks = _parse_smb_conf()

    if name not in blocks:
        print("[!] Partilha não encontrada")
        return False

    created = _ensure_samba_user(user)

    if created is False:
        print("[!] Sem utilizador válido, cancelando")
        return False

    blocks[name] = [
        f"[{name}]\n",
        f"    path = {path}\n",
        "    browseable = yes\n",
        f"    read only = {read_only}\n",
        f"    valid users = {user}\n"
    ]

    _write_smb_conf(blocks)

    print("[+] Partilha Samba atualizada")
    return True


def _apply_samba(debug=False):
    if debug:
        subprocess.run(["testparm", "-s"])
    else:
        subprocess.run(
            ["testparm", "-s"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

    subprocess.run(["systemctl", "restart", "smb"], check=True)
    subprocess.run(["systemctl", "restart", "nmb"], check=True)

    return True


def _ensure_samba_user(username, password=None):
    if not _linux_user_exists(username):
        print(f"Utilizador {username} não existe.")

        choice = input("Criar utilizador? (y/n): ").strip().lower()
        if choice != "y":
            print("[!] Utilizador não criado")
            return False

        if not password:
            password = input("Password do novo utilizador: ").strip()

        print(f"Novo utilizador do sistema: {username}")
        subprocess.run(["useradd", "-m", username], check=True)

        subprocess.run(
            ["bash", "-c", "echo '{}:{}' | chpasswd".format(username, password)],
            check=True
        )
    else:
        print(f"Utilizador {username} já existe")

    print(f"Verificando utilizador: {username}")

    subprocess.run(
        ["smbpasswd", "-a", username],
        input=(password + "\n" + password + "\n").encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    subprocess.run(["smbpasswd", "-e", username], check=True)

    return True

# ///// Pipeline wrappers /////
def run_samba_add_share(name, path, user, password, read_only="no"):
    return run_pipeline("SAMBA ADD SHARE", [
        step("Verificar utilizador Samba", lambda: _ensure_samba_user(user, password)),
        step("Adicionar partilha", lambda: _add_share(name, path, user, read_only)),
        step("Aplicar config", _apply_samba),
    ])

def run_samba_remove_share(name):
    return run_pipeline("SAMBA REMOVE SHARE", [
        step("Apagar partilha", lambda: _remove_share(name)),
        step("Aplicar config", _apply_samba),
    ])

def run_samba_disable_share(name):
    return run_pipeline("SAMBA DISABLE SHARE", [
        step("Desativar partilha", lambda: _disable_share(name)),
        step("Aplicar config", _apply_samba),
    ])

def run_samba_edit_share(name, path, user, read_only):
    return run_pipeline("SAMBA EDIT SHARE", [
        step("Editar partilha", lambda: _edit_share(name, path, user, read_only)),
        step("Aplicar config", _apply_samba),
    ])

def run_samba_inspect():
    blocks = _parse_smb_conf()

    print("\nPARTILHAS SAMBA:\n")

    for name, block in blocks.items():
        if name in ["global", "homes", "printers"]:
            continue

        print(f"[{name}]")
        for line in block[1:]:
            print(line.strip())
        print()

    return True