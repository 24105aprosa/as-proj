import os


def run_pipeline(name, steps):
    print(f"\n===== [{name}] START =====")

    for step in steps:
        try:
            result = step()

            if result is False:
                print(f"[✖] {name} failed")
                return False

        except Exception as e:
            print(f"[ERROR] {name} failed during step: {e}")
            return False

    print(f"[✔] {name} completed successfully")
    return True


def step(name, fn):
    """
    Optional helper to label steps nicely.
    """
    def wrapper():
        print(f"[*] {name}")
        return fn()
    return wrapper

def exists(path):
    return os.path.exists(path)