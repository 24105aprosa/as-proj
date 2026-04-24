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

from core.setup import (
    setup_dns_service,
    setup_apache_service,
    setup_full_web_service,
    setup_nfs_service
)

# ///// Input collectors /////

def collect_dns_inputs():
    domain = input("Enter domain name: ").strip()
    ip = input("Enter primary server IP: ").strip()

    records = []

    while True:
        add = input("Add additional DNS record? (y/n): ").strip().lower()

        if add != "y":
            break

        rtype = input("Type (A/MX): ").strip().upper()
        name = input("Name (e.g. www, mail, @): ").strip()

        if rtype == "A":
            value = input("IP address: ").strip()
            records.append({
                "type": "A",
                "name": name,
                "value": value
            })

        elif rtype == "MX":
            priority = input("Priority (e.g. 10): ").strip()
            value = input("Mail server (FQDN): ").strip()
            records.append({
                "type": "MX",
                "priority": int(priority),
                "value": value
            })

        else:
            print("[!] Unsupported record type")

    return domain, ip, records

def collect_reverse_dns_inputs():
    forward_domain = input("Enter domain name (e.g. example.com): ").strip()
    ip = input("Enter IP address: ").strip()
    fqdn = input("Enter FQDN (e.g. server.example.com): ").strip()

    return forward_domain,ip, fqdn

def collect_domain_only():
    return (input("Enter domain name: ").strip(),)

def collect_reverse_remove_inputs():
    ip = input("Enter IP address: ").strip()
    return (None, ip)

def collect_nfs_add():
    path = input("Directory to share: ").strip()
    client = input("Client IP/subnet (e.g. 192.168.1.0/24): ").strip()
    options = input("Options (e.g. rw,sync,no_root_squash): ").strip()
    return (path, client, options)

def collect_nfs_remove():
    path = input("Directory to remove: ").strip()
    return (path,)

def collect_nfs_disable():
    path = input("Directory to disable: ").strip()
    return (path,)

def collect_nfs_edit():
    index = int(input("Share number to edit: ")) - 1
    path = input("New path: ").strip()
    client = input("New client: ").strip()
    options = input("New options: ").strip()

    return (index, path, client, options)

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
            "label": "DNS + Apache (Full Website)",
            "aliases": {
                "short": ["full"],
                "numeric": ["4"]
            },
            "runner": run_full_web_setup,
            "setup": setup_full_web_service,
            "inputs": collect_dns_inputs
        },
        "nfs_add": {
            "label": "NFS (Add Share)",
            "aliases": {
                "short": ["nfs", "nfs-a"],
                "numeric": ["5"]
            },
            "runner": run_nfs_add_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_add
        }
    },
    "configure": {
        "nfs_inspect": {
            "label": "NFS (Inspect Shares)",
            "aliases": {
                "short": ["nfs-list", "nfs-i"],
                "numeric": ["6"]
            },
            "runner": run_nfs_inspect,
            "setup": None,
            "inputs": lambda: ()
        },
        "nfs_edit": {
            "label": "NFS (Edit Share)",
            "aliases": {
                "short": ["nfs-e"],
                "numeric": ["7"]
            },
            "runner": run_nfs_edit_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_edit
        },
        "nfs_disable": {
            "label": "NFS (Disable Share)",
            "aliases": {
                "short": ["nfs-off", "nfs-d"],
                "numeric": ["8"]
            },
            "runner": run_nfs_disable_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_disable
        }
    },
    "teardown": {
        "dns_remove": {
            "label": "DNS (Remove Forward Zone)",
            "aliases": {
                "short": ["dns-r", "forward-r"],
                "numeric": ["9"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_dns_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "reverse_dns_remove": {
            "label": "DNS (Remove Reverse Zone)",
            "aliases": {
                "short": ["reverse-r"],
                "numeric": ["10"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_reverse_dns_teardown,
            "setup": None,
            "inputs": collect_reverse_remove_inputs
        },
        "apache_remove": {
            "label": "Apache (Remove VirtualHost)",
            "aliases": {
                "short": ["apache-r"],
                "numeric": ["11"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_apache_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "web_remove": {
            "label": "DNS + Apache (Full Website Removal)",
            "aliases": {
                "short": ["web-r", "full-r"],
                "numeric": ["12"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_full_web_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "nfs_remove": {
            "label": "NFS (Remove Share)",
            "aliases": {
                "short": ["nfs-r"],
                "numeric": ["13"]
            },
            "meta": {
                "destructive": True
            },
            "runner": run_nfs_remove_share,
            "setup": setup_nfs_service,
            "inputs": collect_nfs_remove
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

def render_menu(services):
    print("\nAvailable services:\n")

    for group_name, group in services.items():
        print(f"[{group_name.upper()}]")

        for key, svc in group.items():
            aliases = []

            for a in svc.get("aliases", {}).values():
                aliases.extend(a)

            alias_str = ", ".join(aliases)

            print(f"  - {key} ({alias_str}): {svc['label']}")

        print()
