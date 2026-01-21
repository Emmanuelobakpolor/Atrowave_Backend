import secrets
import hashlib

def generate_api_keys(environment='test'):
    env_prefix = environment.lower()
    public_key = f"pk_{env_prefix}_{secrets.token_hex(12)}"
    secret_key = f"sk_{env_prefix}_{secrets.token_hex(24)}"

    secret_hash = hashlib.sha256(secret_key.encode()).hexdigest()

    return public_key, secret_key, secret_hash
