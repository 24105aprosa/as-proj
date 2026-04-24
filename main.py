from core.service_handler import (
    SERVICE_GROUPS,
    build_service_maps,
    render_menu,
)

def main():
    services, alias_map = build_service_maps()

    while True:
        render_menu(SERVICE_GROUPS)

        choice = input("Choose service (or 'exit'): ").strip().lower()

        # Exit program
        if choice in ["exit", "quit", "q"]:
            print("Exiting...")
            break

        # Back / refresh menu
        if choice == "back":
            continue

        # Resolve alias → real service key
        if choice not in alias_map:
            print("[!] Unknown service\n")
            continue

        service_key = alias_map[choice]
        service = services[service_key]

        # Setup
        if service.get("setup"):
            service["setup"]()

        # Inputs
        inputs = service["inputs"]()

        if inputs is None:
            print("[*] Operation cancelled\n")
            continue

        # Allow user to cancel after input
        confirm_run = input("Proceed? (y/n): ").strip().lower()
        if confirm_run == "n":
            print("[*] Returning to menu...\n")
            continue

        # Confirm destructive actions
        if service.get("meta", {}).get("destructive"):
            confirm = input("⚠️ Confirm deletion? (y/n): ").strip().lower()
            if confirm != "y":
                print("[!] Operation cancelled\n")
                continue

        # Run
        success = service["runner"](*inputs)

        if success:
            print(f"[✔] {service_key.upper()} completed successfully!\n")
        else:
            print(f"[!] {service_key.upper()} failed.\n")


if __name__ == "__main__":
    main()