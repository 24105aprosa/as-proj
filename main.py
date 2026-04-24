from core.service_handler import (
    SERVICE_GROUPS,
    build_service_maps,
    render_menu,
)

def main():
    services, alias_map = build_service_maps()

    while True:
        render_menu(SERVICE_GROUPS)

        choice = input("Selecione um serviço, ou 'exit' para sair: ").strip().lower()

        if choice in ["exit", "quit", "q"]:
            print("Terminando...")
            break

        if choice == "back":
            continue

        if choice not in alias_map:
            print("[!] Serviço desconhecido\n")
            continue

        service_key = alias_map[choice]
        service = services[service_key]

        if service.get("setup"):
            service["setup"]()

        inputs = service["inputs"]()
        if inputs is None:
            print("Operação cancelada\n")
            continue

        label = service.get("label", service_key)

        confirm_run = input(f"Quer prosseguir com {label}? (y/n): ").strip().lower()
        if confirm_run == "n":
            print("Voltando ao menu...\n")
            continue

        if service.get("meta", {}).get("destructive"):
            confirm = input("[!] Quer mesmo apagar? (y/n): ").strip().lower()
            if confirm != "y":
                print("Operação cancelada\n")
                continue

        success = service["runner"](*inputs)

        if success:
            print(f"[+] {service_key.upper()} completo com sucesso\n")
        else:
            print(f"[!] {service_key.upper()} falhou.\n")

        input("Enter para continuar...")

if __name__ == "__main__":
    main()