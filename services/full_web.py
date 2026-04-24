from services.dns import run_dns_setup, run_dns_teardown
from services.apache import run_apache_setup, run_apache_teardown
from core.framework import run_pipeline, step

# ///// Setup pipeline /////
def run_full_web_setup(domain, ip, records):
    return run_pipeline("FULL WEB STACK", [
        step("Setup DNS", lambda: run_dns_setup(domain, ip, records)),
        step("Setup Apache", lambda: run_apache_setup(domain)),
    ])

# ///// Teardown pipeline /////
def run_full_web_teardown(domain):
    return run_pipeline("FULL WEB STACK REMOVE", [
        step("Apagar Apache", lambda: run_apache_teardown(domain)),
        step("Apagar DNS", lambda: run_dns_teardown(domain)),
    ])