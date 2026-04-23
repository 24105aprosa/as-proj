from dns import run_dns_setup
from apache import run_apache_setup
from framework import run_pipeline, step

def run_full_web_setup(domain, ip, records):
    return run_pipeline("FULL WEB STACK", [
        step("Setup DNS", lambda: run_dns_setup(domain, ip, records)),
        step("Setup Apache", lambda: run_apache_setup(domain)),
    ])