import os
import subprocess
import re
from datetime import datetime
from core.framework import run_pipeline, step, exists

# ///// Zone file paths /////
ZONE_DIR = "/var/named"
NAMED_CONF = "/etc/named.conf"

# ///// Helpers /////
def _generate_serial(zone_path):
    today = datetime.now().strftime("%Y%m%d")
    highest_nn = 0

    if exists(zone_path):
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

    if exists(zone_path):
        subprocess.run(["cp", zone_path, backup_path], check=True)

    with open(zone_path, "w") as f:
        f.write(content)

    print(f"[+] Zona master criada em {zone_path} (serial {serial})")
    return True

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

    if exists(zone_path):
        backup = f"{zone_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subprocess.run(["cp", zone_path, backup], check=True)

    with open(zone_path, "w") as f:
        f.write(content)

    print(f"[+] Zona reverse criada a {reverse_zone}")
    return reverse_zone

def _remove_zone_file(domain):
    zone_path = f"/var/named/{domain}.hosts"

    if exists(zone_path):
        os.remove(zone_path)
        print(f"[+] Zona em {zone_path} apagada")
    else:
        print("Ficheiro de zona não encontrado")

    return True

def _update_named_conf(domain):
    with open(NAMED_CONF, "r") as f:
        content = f.read()
        if f'zone "{domain}"' in content:
            print("Zona master já existe em named.conf")
            return True

    config_block = f"""
zone "{domain}" IN {{
    type master;
    file "{ZONE_DIR}/{domain}.hosts";
}};
"""

    with open(NAMED_CONF, "a") as f:
        f.write(config_block)

    print("[+] named.conf atualizado com zona master")
    return True

def _update_reverse_named_conf(reverse_zone):
    with open(NAMED_CONF, "r") as f:
        if reverse_zone in f.read():
            print("Zona reverse já existe em named.conf")
            return True

    config_block = f"""
zone "{reverse_zone}" IN {{
    type master;
    file "{ZONE_DIR}/{reverse_zone}.hosts";
}};
"""

    with open(NAMED_CONF, "a") as f:
        f.write(config_block)

    print("[+] named.conf atualizado com zona reverse")
    return True

def _remove_named_conf_zone(domain):
    path = "/etc/named.conf"

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    inside_block = False

    for line in lines:
        if f'zone "{domain}"' in line:
            inside_block = True
            continue

        if inside_block and "};" in line:
            inside_block = False
            continue

        if not inside_block:
            new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    print("[+] Zona apagada de named.conf")
    return True

def _validate_zone(domain):
    result = subprocess.run(
        ["named-checkzone", domain, f"{ZONE_DIR}/{domain}.hosts"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print("[ERROR] Validação de zona falhou:")
        print(result.stderr)
        return False

    print("[+] Zona validada com sucesso")
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
        print("[ERROR] named.conf inválido:")
        print(result.stderr)
        return False

    return True

def _set_permissions(domain):
    try:
        subprocess.run(["chown", "named:named", f"{ZONE_DIR}/{domain}.hosts"], check=True)
        subprocess.run(["chmod", "640", f"{ZONE_DIR}/{domain}.hosts"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("[ERROR] Setup de permissões falhou:", e)
        return False

def _restart_named():
    try:
        subprocess.run(["systemctl", "restart", "named"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("[ERROR] named falhou a reiniciar:", e)
        return False

# ///// Pipeline wrappers /////
def run_dns_setup(domain, ip, records):
    return run_pipeline("DNS", [
        step("Criar zona master ", lambda: _create_zone_file(domain, ip, records)),
        step("Atualizar named.conf", lambda: _update_named_conf(domain)),
        step("Validar zona master", lambda: _validate_zone(domain)),
        step("Validar named.conf", _validate_named_conf),
        step("Definir permissões", lambda: _set_permissions(domain)),
        step("Reiniciar named", _restart_named),
    ])

def run_reverse_dns_setup(forward_domain, ip, fqdn):
    reverse_zone = _ip_to_reverse_zone(ip)

    return run_pipeline("REVERSE DNS", [
        step("Criar zona reverse", lambda: _create_reverse_zone(ip, fqdn, forward_domain)),
        step("Atualizar named.conf", lambda: _update_reverse_named_conf(reverse_zone)),
        step("Validar zona reverse", lambda: _validate_reverse_zone(reverse_zone)),
        step("Reiniciar named", _restart_named),
    ])

def run_dns_teardown(domain):
    return run_pipeline("DNS REMOVE", [
        step("Apagar zona master", lambda: _remove_zone_file(domain)),
        step("Apagar registo em named.conf", lambda: _remove_named_conf_zone(domain)),
        step("Reiniciar named", _restart_named),
    ])

def run_reverse_dns_teardown(ip):
    reverse_zone = _ip_to_reverse_zone(ip)
    
    return run_pipeline("REVERSE DNS REMOVE", [
        step("Apagar zona reverse", lambda: _remove_zone_file(reverse_zone)),
        step("Apagar registo em named.conf", lambda: _remove_named_conf_zone(reverse_zone)),
        step("Reiniciar named", _restart_named),
    ])