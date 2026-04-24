import subprocess
import re

# ///// Helpers /////

def _is_package_installed(pkg):
    result = subprocess.run(
        ["rpm", "-q", pkg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def _install_packages(packages):
    to_install = [pkg for pkg in packages if not _is_package_installed(pkg)]

    if not to_install:
        print("[*] Packages already installed (skipping)")
        return True

    print(f"[+] Installing: {' '.join(to_install)}")

    subprocess.run(
        ["dnf", "install", "-y"] + to_install,
        check=True
    )

    return True


def _is_service_active(service):
    result = subprocess.run(
        ["systemctl", "is-active", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def _is_service_enabled(service):
    result = subprocess.run(
        ["systemctl", "is-enabled", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def _ensure_service(service):
    if not _is_service_enabled(service):
        print(f"[+] Enabling {service}")
        subprocess.run(["systemctl", "enable", service], check=True)
    else:
        print(f"[*] {service} already enabled")

    if not _is_service_active(service):
        print(f"[+] Starting {service}")
        subprocess.run(["systemctl", "start", service], check=True)
    else:
        print(f"[*] {service} already running")


def _configure_named_conf_access():
    path = "/etc/named.conf"

    with open(path, "r") as f:
        content = f.read()

    desired_listen = "listen-on port 53 { 127.0.0.1; any; };"
    desired_query = "allow-query { any; };"

    if desired_listen in content and desired_query in content:
        print("[*] named.conf already configured (skipping)")
        return True

    print("[+] Updating named.conf network access...")

    # Replace listen-on
    content = re.sub(
        r'listen-on port 53\s*\{[^}]*\};',
        desired_listen,
        content
    )

    # Replace allow-query
    content = re.sub(
        r'allow-query\s*\{[^}]*\};',
        desired_query,
        content
    )

    with open(path, "w") as f:
        f.write(content)

    print("[+] named.conf updated")

# ///// DNS /////
def setup_dns_service():
    print("Setting up DNS service...")

    _install_packages(["bind", "bind-utils"])

    _ensure_service("named")

    print("Configuring named.conf access rules...")
    _configure_named_conf_access()

    print("[✔] DNS service ready")

# ///// Apache /////
def setup_apache_service():
    print("Setting up Apache service...")

    _install_packages(["httpd"])

    _ensure_service("httpd")

    print("[✔] Apache service ready")

# ///// Apache + DNS /////
def setup_full_web_service():
    setup_dns_service()
    setup_apache_service()

# ///// NFS /////
def setup_nfs_service():
    print("Setting up NFS service...")

    _install_packages(["nfs-utils"])

    _ensure_service("nfs-server")

    print("[✔] NFS service ready")