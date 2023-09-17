import os


def get_shared_secret():
    return os.getenv("SHARED_SECRET", "seccon-ctf-2023-tokyo-payload")
