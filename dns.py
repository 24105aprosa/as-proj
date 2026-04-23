import os
import subprocess
import re
from datetime import datetime

from framework import run_pipeline, step

ZONE_DIR = "/var/named"
NAMED_CONF = "/etc/named.conf"

# ///// Internal helpers /////

def _generate_serial(zone_path):
    today = datetime.now().strftime("%Y%m%d")
    highest_nn = 0

    if os.path.exists(zone_path):
        with open(zone_path, "r") as f:
            content = f.read()

        matches = re.findall(r'(\d{10})\s*;\s*serial', content)

        for m in matches:
            if m.startswith(today):
                highest_nn = max(highest_nn, int(m[8:]))

    return f"{today}{highest_nn + 1:02d}"


def _build_records(records):
    lines = []

    for r in records:
        if r["type"] == "A":
            lines.append(f'{r["name"]} IN A {r["value"]}')

        elif r["type"] == "MX":
            lines.append(f'@ IN MX {r["priority"]} {r["value"]}')

    return "\n".join(lines)


def _create_zone_file(domain, ip, records):
    template_path = "templates/zone_master.txt"
    zone_path = f"{ZONE_DIR}/{domain}.hosts"
    backup_path = f"{zone_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"

    serial = _generate_serial(zone_path)

    with open(template_path, "r") as f:
        content = f.read()

    content = content.replace("{domain}", domain)
    content = content.replace("{ip}", ip)
    content = content.replace("{serial}", serial)

    record_block = _build_records(records)
    content = content.replace("{records}", record_block)

    if os.path.exists(zone_path):
        subprocess.run(["cp", zone_path, backup_path], check=True)

    with open(zone_path, "w") as f:
        f.write(content)

    print(f"[+] Zone file created at {zone_path} (serial {serial})")


def _ip_to_reverse_zone(ip):
    parts = ip.split(".")
    return f"{parts[2]}.{parts[1]}.{parts[0]}.in-addr.arpa"


def _build_ptr_record(ip, fqdn):
    last_octet = ip.split(".")[-1]
    return f"{last_octet} IN PTR {fqdn}."


def _create_reverse_zone(ip, fqdn, forward_domain):
    template_path = "templates/zone_reverse.txt"

    reverse_zone = _ip_to_reverse_zone(ip)
    zone_path = f"{ZONE_DIR}/{reverse_zone}.hosts"

    serial = _generate_serial(zone_path)

    with open(template_path, "r") as f:
        content = f.read()

    ptr_record = _build_ptr_record(ip, fqdn)

    content = content.replace("{reverse}", reverse_zone)
    content = content.replace("{domain}", forward_domain)
    content = content.replace("{ptr}", ptr_record)
    content = content.replace("{serial}", serial)

    if os.path.exists(zone_path):
        backup = f"{zone_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subprocess.run(["cp", zone_path, backup], check=True)

    with open(zone_path, "w") as f:
        f.write(content)

    print(f"[+] Reverse zone created: {reverse_zone}")
    return reverse_zone


def _update_named_conf(domain):
    with open(NAMED_CONF, "r") as f:
        content = f.read()
        if f'zone "{domain}"' in content:
            print("[*] Zone already exists in named.conf (skipping)")
            return True

    config_block = f"""
zone "{domain}" IN {{
    type master;
    file "{ZONE_DIR}/{domain}.hosts";
}};
"""

    with open(NAMED_CONF, "a") as f:
        f.write(config_block)

    print("[+] named.conf updated")
    return True


def _update_reverse_named_conf(reverse_zone):
    with open(NAMED_CONF, "r") as f:
        if reverse_zone in f.read():
            print("[*] Reverse zone already exists")
            return True

    config_block = f"""
zone "{reverse_zone}" IN {{
    type master;
    file "{ZONE_DIR}/{reverse_zone}.hosts";
}};
"""

    with open(NAMED_CONF, "a") as f:
        f.write(config_block)

    print("[+] Reverse named.conf updated")
    return True


def _validate_zone(domain):
    result = subprocess.run(
        ["named-checkzone", domain, f"{ZONE_DIR}/{domain}.hosts"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print("[ERROR] Zone validation failed:")
        print(result.stderr)
        return False

    print("[+] Zone file is valid")
    return True


def _validate_reverse_zone(reverse_zone):
    result = subprocess.run(
        ["named-checkzone", reverse_zone, f"/var/named/{reverse_zone}.hosts"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print(result.stderr)
        return False

    return True


def _validate_named_conf():
    result = subprocess.run(
        ["named-checkconf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print("[ERROR] named.conf invalid:")
        print(result.stderr)
        return False

    return True


def _set_permissions(domain):
    try:
        subprocess.run(["chown", "named:named", f"{ZONE_DIR}/{domain}.hosts"], check=True)
        subprocess.run(["chmod", "640", f"{ZONE_DIR}/{domain}.hosts"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("[ERROR] Permission setup failed:", e)
        return False


def _restart_named():
    try:
        subprocess.run(["systemctl", "restart", "named"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to restart named:", e)
        return False

# ///// Main setup /////

def run_dns_setup(domain, ip, records):
    return run_pipeline("DNS", [
        step("Create zone file", lambda: _create_zone_file(domain, ip, records)),
        step("Update named.conf", lambda: _update_named_conf(domain)),
        step("Validate zone file", lambda: _validate_zone(domain)),
        step("Validate named.conf", _validate_named_conf),
        step("Set permissions", lambda: _set_permissions(domain)),
        step("Restart named", _restart_named),
    ])

def run_reverse_dns_setup(ip, fqdn):
    reverse_zone = _ip_to_reverse_zone(ip)

    return run_pipeline("REVERSE DNS", [
        step("Create reverse zone", lambda: _create_reverse_zone(ip, fqdn)),
        step("Update named.conf", lambda: _update_reverse_named_conf(reverse_zone)),
        step("Validate reverse zone", lambda: _validate_reverse_zone(reverse_zone)),
        step("Restart named", _restart_named),
    ])