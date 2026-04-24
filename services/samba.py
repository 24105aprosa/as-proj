import subprocess
import re
from core.framework import run_pipeline, step, exists

SMB_CONF = "/etc/samba/smb.conf"

# ///// Helpers /////

def _read_conf():
    if not exists(SMB_CONF):
        return ""
    with open(SMB_CONF, "r") as f:
        return f.read()


def _share_exists(name):
    content = _read_conf()
    return f"[{name}]" in content


def _add_share(name, path, read_only="no"):
    if _share_exists(name):
        print("[*] Share already exists (skipping)")
        return True

    block = f"""

[{name}]
    path = {path}
    browseable = yes
    read only = {read_only}
    guest ok = yes
"""

    with open(SMB_CONF, "a") as f:
        f.write(block)

    print("[+] Samba share added")
    return True


def _remove_share(name):
    if not exists(SMB_CONF):
        return True

    with open(SMB_CONF, "r") as f:
        lines = f.readlines()

    new_lines = []
    skip = False

    for line in lines:
        if line.strip().startswith(f"[{name}]"):
            skip = True
            continue

        if skip and line.strip().startswith("[") and not line.strip().startswith(f"[{name}]"):
            skip = False

        if not skip:
            new_lines.append(line)

    with open(SMB_CONF, "w") as f:
        f.writelines(new_lines)

    print("[+] Samba share removed")
    return True


def _disable_share(name):
    content = _read_conf()

    content = re.sub(
        rf"\[{name}\](.*?)((?=\n\[)|\Z)",
        lambda m: "# DISABLED\n" + m.group(0).replace("\n", "\n# "),
        content,
        flags=re.S
    )

    with open(SMB_CONF, "w") as f:
        f.write(content)

    print("[+] Samba share disabled")
    return True


def _edit_share(name, path, read_only):
    _remove_share(name)
    return _add_share(name, path, read_only)


def _apply_samba():
    subprocess.run(["testparm"], check=False)
    subprocess.run(["systemctl", "restart", "smb"], check=True)
    subprocess.run(["systemctl", "restart", "nmb"], check=True)
    return True

# ///// Main Pipelines /////

def run_samba_add_share(name, path, read_only="no"):
    return run_pipeline("SAMBA ADD SHARE", [
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


def run_samba_edit_share(name, path, read_only):
    return run_pipeline("SAMBA EDIT SHARE", [
        step("Edit share", lambda: _edit_share(name, path, read_only)),
        step("Apply config", _apply_samba),
    ])


def run_samba_inspect():
    content = _read_conf()
    print("\nSAMBA SHARES:\n")

    for line in content.splitlines():
        if line.strip().startswith("[") and "]" in line:
            print(line.strip())

    return True