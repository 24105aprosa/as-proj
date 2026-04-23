import subprocess
import re

def configure_named_conf_access():
    path = "/etc/named.conf"

    with open(path, "r") as f:
        content = f.read()

    # Update listen-on
    content = re.sub(
        r'listen-on port 53 \{[^}]*\};',
        'listen-on port 53 { 127.0.0.1; any; };',
        content
    )

    # Update allow-query
    content = re.sub(
        r'allow-query\s+\{[^}]*\};',
        'allow-query { any; };',
        content
    )

    with open(path, "w") as f:
        f.write(content)

    print("[+] named.conf network access updated")

def setup_dns_service():
    print("Installing BIND...")

    subprocess.run(
        ["dnf", "install", "-y", "bind", "bind-utils"],
        check=True
    )

    print("Enabling named service...")

    subprocess.run(
        ["systemctl", "enable", "--now", "named"],
        check=True
    )

    print("Configuring named.conf access rules...")

    configure_named_conf_access()

    print("DNS service ready")

# ///// Apache /////
def setup_apache_service():
    print("Installing Apache...")

    subprocess.run(
        ["dnf", "install", "-y", "httpd"],
        check=True
    )

    print("Enabling httpd service...")

    subprocess.run(
        ["systemctl", "enable", "--now", "httpd"],
        check=True
    )

    print("Apache service ready")

# ///// Apache + DNS /////
def setup_full_web_service():
    setup_dns_service()
    setup_apache_service()