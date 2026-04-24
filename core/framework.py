import os

def run_pipeline(name, steps, silent=False):
    if not silent:
        print(f"\n===== [{name}] START =====")

    for step in steps:
        try:
            result = step()

            if result is False or result is None:
                if not silent:
                    print(f"[!] {name} falhou")
                return False

        except Exception as e:
            if not silent:
                print(f"[ERROR] {name} falhou durante passo: {e}")
            return False

    if not silent:
        print(f"[+] {name} completo com sucesso")
    return True

def step(name, fn, silent=False):
    def wrapper():
        if not silent:
            print(f"{name}")
        return fn()
    return wrapper

def exists(path):
    return os.path.exists(path)