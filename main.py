from dns import run_dns_setup, run_reverse_dns_setup
from apache import run_apache_setup
from full_web import run_full_web_setup
from setup import setup_dns_service, setup_apache_service, setup_full_web_service

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

SERVICES = {
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
        "inputs": lambda: (input("Enter domain name: ").strip(),)
    },
    "web": {
        "label": "DNS + Apache (Full Website)",
        "runner": run_full_web_setup,
        "setup": setup_full_web_service,
        "inputs": collect_dns_inputs
    }
}

# /////

def main():
    print("Available services:")
    for service in SERVICES:
        print(f" - {service}: {SERVICES[service]['label']}")

    service_name = input("\nChoose service: ").strip().lower()

    if service_name not in SERVICES:
        print("[!] Unknown service")
        return

    service = SERVICES[service_name]

    # Optional service-specific setup (e.g., install packages)
    if service["setup"]:
        service["setup"]()

    # Collect only the inputs required for that service
    inputs = service["inputs"]()

    # Call the service runner with unpacked arguments
    success = service["runner"](*inputs)

    if success:
        print(f"[✔] {service_name.upper()} setup completed successfully!")
    else:
        print(f"[!] {service_name.upper()} setup failed.")


if __name__ == "__main__":
    main()