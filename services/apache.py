import os
import subprocess
from core.framework import run_pipeline, step, exists

# ///// Helpers /////
def _create_vhost(domain):
    vhost_path = f"/etc/httpd/conf.d/{domain}.conf"
    web_root = f"/var/www/{domain}"

    if exists(vhost_path):
        print("VirtualHost já existe")
        return True

    os.makedirs(web_root, exist_ok=True)

    index_path = f"{web_root}/index.html"

    with open(index_path, "w") as f:
        f.write(f"""<html>
<head><title>{domain}</title></head>
<body>
<h1>{domain}</h1>
</body>
</html>
""")

    vhost_config = f"""
<VirtualHost *:80>
    ServerName {domain}
    ServerAlias www.{domain}
    DocumentRoot /var/www/{domain}

    <Directory /var/www/{domain}>
        Require all granted
    </Directory>
</VirtualHost>
"""

    with open(vhost_path, "w") as f:
        f.write(vhost_config)

    print(f"[+] VirtualHost criado para {domain}")
    return True

def _remove_vhost(domain):
    vhost_path = f"/etc/httpd/conf.d/{domain}.conf"

    if exists(vhost_path):
        os.remove(vhost_path)
        print(f"[+] VHost {vhost_path} apagado")
    else:
        print("VHost não encontrado")

    return True

def _remove_web_root(domain):
    web_root = f"/var/www/{domain}"

    if exists(web_root):
        subprocess.run(["rm", "-rf", web_root], check=True)
        print(f"[+] Web root {web_root} apagada")
    else:
        print("Web root não encontrada")

    return True

def _validate_apache_config():
    result = subprocess.run(
        ["httpd", "-t"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print("[ERROR] Configuração Apache inválida:")
        print(result.stderr)
        return False

    print("[+] Configuração Apache válida")
    return True

def _set_apache_permissions(domain):
    web_root = f"/var/www/{domain}"

    subprocess.run(["chown", "-R", "apache:apache", web_root], check=True)
    subprocess.run(["chmod", "-R", "755", web_root], check=True)

    return True

def _restart_apache():
    subprocess.run(["systemctl", "restart", "httpd"], check=True)
    return True

# ///// Pipeline wrappers /////
def run_apache_setup(domain):
    return run_pipeline("APACHE", [
        step("Criar VirtualHost", lambda: _create_vhost(domain)),
        step("Verificar configuração Apache", _validate_apache_config),
        step("Definir permissões", lambda: _set_apache_permissions(domain)),
        step("Reiniciar Apache", _restart_apache),
    ])

def run_apache_teardown(domain):
    return run_pipeline("APACHE REMOVE", [
        step("Apagar VirtualHost", lambda: _remove_vhost(domain)),
        step("Apagar web root", lambda: _remove_web_root(domain)),
        step("Reiniciar Apache", _restart_apache),
    ])