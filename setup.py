import subprocess

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

    print("DNS service ready")