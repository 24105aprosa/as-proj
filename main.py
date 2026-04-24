from dns import (
    run_dns_setup,
    run_reverse_dns_setup,
    run_dns_teardown,
    run_reverse_dns_teardown
)

from apache import (
    run_apache_setup,
    run_apache_teardown
)

from full_web import (
    run_full_web_setup,
    run_full_web_teardown
)

from setup import (
    setup_dns_service,
    setup_apache_service,
    setup_full_web_service
)

# /////

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

# ///// Services /////

SERVICE_GROUPS = {
    "create": {
        "dns": {
            "label": "DNS (Forward)",
            "runner": run_dns_setup,
            "setup": setup_dns_service,
            "inputs": collect_dns_inputs
        },
        "reverse_dns": {
            "label": "DNS (Reverse)",
            "runner": run_reverse_dns_setup,
            "setup": setup_dns_service,
            "inputs": collect_reverse_dns_inputs
        },
        "apache": {
            "label": "Apache (VirtualHost)",
            "runner": run_apache_setup,
            "setup": setup_apache_service,
            "inputs": collect_domain_only
        },
        "web": {
            "label": "DNS + Apache (Full Website)",
            "runner": run_full_web_setup,
            "setup": setup_full_web_service,
            "inputs": collect_dns_inputs
        }
    },
    "remove": {
        "dns_remove": {
            "label": "DNS (Remove Forward Zone)",
            "runner": run_dns_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "reverse_dns_remove": {
            "label": "DNS (Remove Reverse Zone)",
            "runner": run_reverse_dns_teardown,
            "setup": None,
            "inputs": collect_reverse_remove_inputs
        },
        "apache_remove": {
            "label": "Apache (Remove VirtualHost)",
            "runner": run_apache_teardown,
            "setup": None,
            "inputs": collect_domain_only
        },
        "web_remove": {
            "label": "DNS + Apache (Full Website Removal)",
            "runner": run_full_web_teardown,
            "setup": None,
            "inputs": collect_domain_only
        }
    }
}

def get_all_services():
    services = {}
    for group in SERVICE_GROUPS.values():
        services.update(group)
    return services

def display_services():
    print("Available services:\n")

    for group_name, group in SERVICE_GROUPS.items():
        print(f"[{group_name.upper()}]")
        for key, svc in group.items():
            print(f"  - {key}: {svc['label']}")
        print()

# /////

def main():
    services = get_all_services()

    while True:
        display_services()

        service_name = input("Choose service (or 'exit'): ").strip().lower()

        # Exit program
        if service_name in ["exit", "quit", "q"]:
            print("Exiting...")
            break

        # Back / refresh menu
        if service_name == "back":
            continue

        if service_name not in services:
            print("[!] Unknown service\n")
            continue

        service = services[service_name]

        # Setup
        if service["setup"]:
            service["setup"]()

        # Inputs
        inputs = service["inputs"]()

        # Allow user to cancel after input
        confirm_run = input("Proceed? (yes/back): ").strip().lower()
        if confirm_run == "back":
            print("[*] Returning to menu...\n")
            continue

        # Confirm destructive actions
        if service_name in SERVICE_GROUPS["remove"]:
            confirm = input("⚠️ Confirm deletion? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("[!] Operation cancelled\n")
                continue

        # Run
        success = service["runner"](*inputs)

        if success:
            print(f"[✔] {service_name.upper()} completed successfully!\n")
        else:
            print(f"[!] {service_name.upper()} failed.\n")


if __name__ == "__main__":
    main()