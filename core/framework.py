import os

# ///// Pipeline /////

def run_pipeline(name, steps, silent=False):
    if not silent:
        print(f"\n===== [{name}] START =====")

    for step in steps:
        try:
            result = step()

            if result is False or result is None:
                if not silent:
                    print(f"[✖] {name} failed")
                return False

        except Exception as e:
            if not silent:
                print(f"[ERROR] {name} failed during step: {e}")
            return False

    if not silent:
        print(f"[✔] {name} completed successfully")
    return True

# ///// Step wrapper /////

def step(name, fn, silent=False):
    """
    Optional helper to label steps nicely.
    """
    def wrapper():
        if not silent:
            print(f"[*] {name}")
        return fn()
    return wrapper

# ///// Helpers /////

def exists(path):
    return os.path.exists(path)