from ceased_cli import CLI
import os


if __name__ == "__main__":
    os.makedirs("keys", exist_ok=True)
    os.makedirs("auth", exist_ok=True)
    with open("auth/PLACE CREDENTIALS HERE", "wb") as f:
        f.write(b"")
    CLI().run()