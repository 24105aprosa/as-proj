from dns import run_dns_setup, run_dns_teardown
from apache import run_apache_setup, run_apache_teardown
from framework import run_pipeline, step

# ///// Setup /////

def run_full_web_setup(domain, ip, records):
    return run_pipeline("FULL WEB STACK", [
        step("Setup DNS", lambda: run_dns_setup(domain, ip, records)),
        step("Setup Apache", lambda: run_apache_setup(domain)),
    ])

# ///// Teardown /////

def run_full_web_teardown(domain):
    return run_pipeline("FULL WEB STACK REMOVE", [
        step("Remove Apache", lambda: run_apache_teardown(domain)),
        step("Remove DNS", lambda: run_dns_teardown(domain)),
    ])