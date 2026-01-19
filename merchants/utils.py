import secrets
import hashlib

def generate_api_keys():
    public_key = f"pk_{secrets.token_hex(12)}"
    secret_key = f"sk_{secrets.token_hex(24)}"

    secret_hash = hashlib.sha256(secret_key.encode()).hexdigest()

    return public_key, secret_key, secret_hash
