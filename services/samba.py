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
        print("[*] Share already exists (skipping)")
        return True

    blocks[name] = [
        f"[{name}]\n",
        f"    path = {path}\n",
        "    browseable = yes\n",
        f"    read only = {read_only}\n",
        f"    valid users = {user}\n"
    ]

    _write_smb_conf(blocks)

    print("[+] Samba share added")
    return True


def _remove_share(name):
    blocks = _parse_smb_conf()

    if name in blocks:
        del blocks[name]
        _write_smb_conf(blocks)
        print("[+] Samba share removed")
    else:
        print("[*] Share not found (skipping)")

    return True


def _disable_share(name):
    blocks = _parse_smb_conf()

    if name not in blocks:
        print("[*] Share not found")
        return True

    commented = []
    for line in blocks[name]:
        if not line.startswith("#"):
            commented.append("#" + line.rstrip("\n"))
        else:
            commented.append(line)

    blocks[name] = ["# DISABLED\n"] + commented
    _write_smb_conf(blocks)

    print("[+] Samba share disabled")
    return True


def _edit_share(name, path, user, read_only):
    blocks = _parse_smb_conf()

    if name not in blocks:
        print("[!] Share not found")
        return False

    new_block = [
        f"[{name}]\n",
        f"    path = {path}\n",
        "    browseable = yes\n",
        f"    read only = {read_only}\n",
        f"    valid users = {user}\n"
    ]

    blocks[name] = new_block
    _write_smb_conf(blocks)

    print("[+] Samba share updated")
    return True


def _apply_samba():
    subprocess.run(["testparm"], check=False)
    subprocess.run(["systemctl", "restart", "smb"], check=True)
    subprocess.run(["systemctl", "restart", "nmb"], check=True)
    return True


def _ensure_samba_user(username, password):
    # 1. Ensure Linux user exists
    if not _linux_user_exists(username):
        print(f"[*] Creating system user: {username}")
        subprocess.run(["useradd", "-m", username], check=True)
        subprocess.run(["bash", "-c", f"echo '{username}:{password}' | chpasswd"], check=True)
    else:
        print(f"[*] User {username} already exists (skipping system creation)")

    # 2. Ensure Samba user exists / password set
    print(f"[*] Ensuring Samba user: {username}")
    proc = subprocess.run(
        ["smbpasswd", "-a", username],
        input=f"{password}\n{password}\n",
        text=True,
        capture_output=True
    )

    subprocess.run(["smbpasswd", "-e", username], check=True)

    return True

# ///// Main Pipelines /////

def run_samba_add_share(name, path, user, password, read_only="no"):
    return run_pipeline("SAMBA ADD SHARE", [
        step("Ensure Samba user", lambda: _ensure_samba_user(user, password)),
        step("Add share", lambda: _add_share(name, path, read_only)),
        step("Apply config", _apply_samba),
    ])


def run_samba_remove_share(name):
    return run_pipeline("SAMBA REMOVE SHARE", [
        step("Remove share", lambda: _remove_share(name)),
        step("Apply config", _apply_samba),
    ])


def run_samba_disable_share(name):
    return run_pipeline("SAMBA DISABLE SHARE", [
        step("Disable share", lambda: _disable_share(name)),
        step("Apply config", _apply_samba),
    ])


def run_samba_edit_share(name, path, user, read_only):
    return run_pipeline("SAMBA EDIT SHARE", [
        step("Edit share", lambda: _edit_share(name, path, user, read_only)),
        step("Apply config", _apply_samba),
    ])


def run_samba_inspect():
    blocks = _parse_smb_conf()

    print("\nSAMBA SHARES:\n")

    for name, block in blocks.items():
        if name in ["global", "homes", "printers"]:
            continue

        print(f"[{name}]")
        for line in block[1:]:
            print(line.strip())
        print()

    return True