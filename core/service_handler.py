from services.dns import (
    run_dns_setup,
    run_reverse_dns_setup,
    run_dns_teardown,
    run_reverse_dns_teardown
)

from services.apache import (
    run_apache_setup,
    run_apache_teardown
)

from services.full_web import (
    run_full_web_setup,
    run_full_web_teardown
)

from services.nfs import (
    run_nfs_add_share,
    run_nfs_remove_share,
    run_nfs_edit_share,
    run_nfs_disable_share,
    run_nfs_inspect
)

from services.samba import (
    run_samba_add_share,
    run_samba_remove_share,
    run_samba_edit_share,
    run_samba_disable_share,
    run_samba_inspect
)

from services.backup import (
    run_full_snapshot_backup,
    run_home_incremental_backup,
    run_tar_restore,
    run_rsync_restore,
    run_backups_inspect
)

from core.setup import (
    setup_dns_service,
    setup_apache_service,
    setup_full_web_service,
    setup_nfs_service,
    setup_samba_service,
    setup_backup_service
)

# ///// Read-only helper /////
def _normalize_ro(value):
    return "yes" if value.strip().lower() in ["yes", "y", "true", "1"] else "no"

# ///// DNS/Apache input collectors /////
def collect_dns_inputs():
    domain = input("Domínio primário: ").strip()
    ip = input("IP do servidor primário: ").strip()

    records = []

    while True:
        add = input("Adicionar um registo DNS? (y/n): ").strip().lower()

        if add != "y":
            break

        rtype = input("Tipo (A/MX): ").strip().upper()
        name = input("Nome (ex.: www, mail, @): ").strip()

        if rtype == "A":
            value = input("Endereço IP: ").strip()
            records.append({
                "type": "A",
                "name": name,
                "value": value
            })

        elif rtype == "MX":
            priority = input("Prioridade (ex.: 10): ").strip()
            value = input("Servidor de mail (FQDN): ").strip()
            records.append({
                "type": "MX",
                "priority": int(priority),
                "value": value
            })

        else:
            print("[!] Registo desconhecido")

    return domain, ip, records

def collect_reverse_dns_inputs():
    forward_domain = input("Domínio (ex.: teste.com): ").strip()
    ip = input("Endereço IP: ").strip()
    fqdn = input("FQDN (ex.: webmail.teste.com): ").strip()

    return forward_domain,ip, fqdn

def collect_domain_only():
    return (input("Domínio: ").strip(),)

def collect_reverse_remove_inputs():
    ip = input("Endereço IP: ").strip()
    return (ip)

# ///// NFS input collectors /////
def collect_nfs_add():
    path = input("Diretoria a partilhar: ").strip()
    client = input("IP/máscara(ex.: 192.168.1.0/24): ").strip()
    options = input("Opções (ex.: rw,sync,no_root_squash): ").strip()
    return (path, client, options)

def collect_nfs_remove():
    path = input("Diretoria a remover: ").strip()
    return (path,)

def collect_nfs_disable():
    path = input("Diretoria a desativar: ").strip()
    return (path,)

def collect_nfs_edit():
    index = int(input("Partilha a editar: ")) - 1
    path = input("Nova diretoria: ").strip()
    client = input("Novo IP: ").strip()
    options = input("Opções: ").strip()

    return (index, path, client, options)

# ///// Samba input collectors /////
def collect_samba_add():
    name = input("Nome da partilha: ").strip()
    path = input("Diretoria a partilhar: ").strip()

    ro = _normalize_ro(input("Read-only? (y/n): "))

    user = input("Utilizador: ").strip()
    password = input("Password: ").strip()

    return (name, path, user, password, ro)

def collect_samba_remove():
    name = input("Partilha a remover: ").strip()
    return (name,)

def collect_samba_edit():
    name = input("Partilha a editar: ").strip()
    path = input("Nova diretoria: ").strip()

    ro = _normalize_ro(input("Read-only? (y/n): "))

    user = input("Utilizador: ").strip()

    return (name, path, user, ro)

def collect_samba_disable():
    name = input("Partilha a desativar: ").strip()
    return (name,)

# ///// Backup input collectors /////
def collect_backup_snapshot():
    return ()

def collect_backup_home():
    return ()

def collect_tar_restore():
    path = input("Ficheiro do snapshot TAR: ").strip()
    return (f"/var/backups/snapshots/{path}",)

def collect_rsync_restore():
    path = input("Ficheiro do backup RSYNC: ").strip()
    return (f"/var/backups/rsync/{path}",)

def collect_backup_list():
    return ()

# ///// Services /////
SERVICE_GROUPS = {
    "provision": {
        "dns": {
            "label": "DNS (Forward)",
            "aliases": {
                "short": ["forward"],
                "numeric": ["1"]
            },
            "runner": run_dns_setup,
            "setup": setup_dns_service,
            "inputs": collect_dns_inputs
        },
        "reverse_dns": {
            "label": "DNS (Reverse)",
            "aliases": {
                "short": ["reverse"],
                "numeric": ["2"]
            },
            "runner": run_reverse_dns_setup,
            "setup": setup_dns_service,
            "inputs": collect_reverse_dns_inputs
        },
        "apache": {
            "label": "Apache (VirtualHost)",
            "aliases": {
                "short": ["apache"],
                "numeric": ["3"]
            },
            "runner": run_apache_setup,
            "setup": setup_apache_service,
            "inputs": collect_domain_only
        },
        "web": {
            "label": "DNS + Apache (Website Completo)",
            "aliases": {
                "short": ["full"],
                "numeric": ["4"]
            },
            "runner": run_full_web_setup,
            "setup": setup_full_web_service,
            "inputs": collect_dns_inputs
        },
        "nfs_add": {
            "label": "NFS (Nova Partilha)",
            "aliases": {
                "short": ["nfs", "nfs-a"],
                "numeric": ["5"]
            },
            "runner": run_nfs_add_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_add
        },
            "samba_add": {
                "label": "Samba (Nova Partilha)",
                "aliases": {
                    "short": ["smb", "smb-a"],
                    "numeric": ["6"]
                },
                "runner": run_samba_add_share,
                "setup": setup_samba_service,
                "inputs": collect_samba_add
            }
    },
    "configure": {
        "nfs_inspect": {
            "label": "NFS (Lista)",
            "aliases": {
                "short": ["nfs-list", "nfs-i"],
                "numeric": ["7"]
            },
            "runner": run_nfs_inspect,
            "setup": None,
            "inputs": lambda: ()
        },
        "nfs_edit": {
            "label": "NFS (Editar Partilha)",
            "aliases": {
                "short": ["nfs-e"],
                "numeric": ["8"]
            },
            "runner": run_nfs_edit_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_edit
        },
        "nfs_disable": {
            "label": "NFS (Desativar Partilha)",
            "aliases": {
                "short": ["nfs-off", "nfs-d"],
                "numeric": ["9"]
            },
            "runner": run_nfs_disable_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_disable
        },
        "samba_inspect": {
            "label": "Samba (Lista)",
            "aliases": {
                "short": ["smb-list", "smb-i"],
                "numeric": ["10"]
            },
            "runner": run_samba_inspect,
            "setup": setup_samba_service,
            "inputs": lambda: ()
        },
        "samba_edit": {
            "label": "Samba (Editar Partilha)",
            "aliases": {
                "short": ["smb-e"],
                "numeric": ["11"]
            },
            "runner": run_samba_edit_share,
            "setup": setup_samba_service,
            "inputs": collect_samba_edit
        },
        "samba_disable": {
            "label": "Samba (Desativar Partilha)",
            "aliases": {
                "short": ["smb-off", "smb-d"],
                "numeric": ["12"]
            },
            "runner": run_samba_disable_share,
            "setup": setup_samba_service,
            "inputs": collect_samba_disable
        }
    },
    "teardown": {
        "dns_remove": {
            "label": "DNS (Apagar Zona Forward)",
            "aliases": {
                "short": ["dns-r", "forward-r"],
                "numeric": ["13"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_dns_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "reverse_dns_remove": {
            "label": "DNS (Apagar Zona Reverse)",
            "aliases": {
                "short": ["reverse-r"],
                "numeric": ["14"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_reverse_dns_teardown,
            "setup": None,
            "inputs": collect_reverse_remove_inputs
        },
        "apache_remove": {
            "label": "Apache (Apagar VirtualHost)",
            "aliases": {
                "short": ["apache-r"],
                "numeric": ["15"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_apache_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "web_remove": {
            "label": "DNS + Apache (Apagar Website Completo)",
            "aliases": {
                "short": ["web-r", "full-r"],
                "numeric": ["16"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_full_web_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "nfs_remove": {
            "label": "NFS (Apagar Partilha)",
            "aliases": {
                "short": ["nfs-r"],
                "numeric": ["17"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_nfs_remove_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_remove
        },
        "samba_remove": {
            "label": "Samba (Apagar Partilha)",
            "aliases": {
                "short": ["smb-r"],
                "numeric": ["18"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_samba_remove_share,
            "setup": setup_samba_service,
            "inputs": collect_samba_remove
        }
    },
    "backup": {
        "snapshot": {
            "label": "Backup (Snapshot - TAR)",
            "aliases": {
                "short": ["bak-snap", "tar", "t"],
                "numeric": ["19"]
            },
            "runner": run_full_snapshot_backup,
            "setup": setup_backup_service,
            "inputs": collect_backup_snapshot
        },
        "home": {
            "label": "Backup (Incremental - RSYNC)",
            "aliases": {
                "short": ["bak-home", "rsync", "r"],
                "numeric": ["20"]
            },
            "runner": run_home_incremental_backup,
            "setup": setup_backup_service,
            "inputs": collect_backup_home
        },
        "list": {
            "label": "Backup (Lista)",
            "aliases": {
                "short": ["bak-list", "bak-l"],
                "numeric": ["21"]
            },
            "runner": run_backups_inspect,
            "setup": setup_backup_service,
            "inputs": collect_backup_list
        },
        "tar_restore": {
            "label": "Backup (Recuperar snapshot TAR)",
            "aliases": {
                "short": ["bak-rt", "rt"],
                "numeric": ["22"]
            },
            "runner": run_tar_restore,
            "setup": setup_backup_service,
            "inputs": collect_tar_restore
        },
        "rsync_restore": {
            "label": "Backup (Recuperar backup RSYNC)",
            "aliases": {
                "short": ["bak-rr", "rr"],
                "numeric": ["23"]
            },
            "runner": run_rsync_restore,
            "setup": setup_backup_service,
            "inputs": collect_rsync_restore
        }
    }
}

def build_service_maps():
    services = {}
    alias_map = {}

    for group in SERVICE_GROUPS.values():
        for key, svc in group.items():
            services[key] = svc
            alias_map[key] = key

            for alias_group in svc.get("aliases", {}).values():
                for alias in alias_group:
                    alias_map[alias] = key

    return services, alias_map

def render_menu(service_groups):
    print("\nServiços disponíveis:\n")

    for group_name, group in service_groups.items():
        print(f"[{group_name.upper()}]")

        for key, svc in group.items():
            alias_list = []

            for alias_group in svc.get("aliases", {}).values():
                alias_list.extend(alias_group)

            alias_str = ", ".join(alias_list) if alias_list else "-"

            print(f"  - {key} ({alias_str}): {svc['label']}")

        print()
