import base64
import json
import os
from pathlib import Path
from typing import Dict

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_ecies_keypair(private_key_path: Path, public_key_path: Path):
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)

    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    public_key_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def load_public_key(public_key_path: Path):
    return serialization.load_pem_public_key(public_key_path.read_bytes())


def load_private_key(private_key_path: Path):
    return serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=None,
    )


def derive_key(shared_secret: bytes, salt: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"integrated-poc-ecies-usk-protection",
    ).derive(shared_secret)


def ecies_encrypt(plaintext: str, recipient_public_key_path: Path) -> str:
    recipient_public_key = load_public_key(recipient_public_key_path)

    ephemeral_private_key = ec.generate_private_key(ec.SECP256K1())
    ephemeral_public_key = ephemeral_private_key.public_key()

    shared_secret = ephemeral_private_key.exchange(
        ec.ECDH(),
        recipient_public_key,
    )

    salt = os.urandom(16)
    nonce = os.urandom(12)
    aes_key = derive_key(shared_secret, salt)

    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    ephemeral_public_pem = ephemeral_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    envelope = {
        "scheme": "ECIES-SECP256K1-AESGCM-HKDFSHA256",
        "ephemeral_public_key_pem_b64": base64.b64encode(ephemeral_public_pem).decode("utf-8"),
        "salt_b64": base64.b64encode(salt).decode("utf-8"),
        "nonce_b64": base64.b64encode(nonce).decode("utf-8"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("utf-8"),
    }

    envelope_json = json.dumps(envelope, separators=(",", ":"), sort_keys=True)

    return base64.b64encode(envelope_json.encode("utf-8")).decode("utf-8")


def ecies_decrypt(encrypted_envelope_b64: str, recipient_private_key_path: Path) -> str:
    recipient_private_key = load_private_key(recipient_private_key_path)

    envelope_json = base64.b64decode(encrypted_envelope_b64.encode("utf-8")).decode("utf-8")
    envelope: Dict = json.loads(envelope_json)

    ephemeral_public_pem = base64.b64decode(envelope["ephemeral_public_key_pem_b64"])
    ephemeral_public_key = serialization.load_pem_public_key(ephemeral_public_pem)

    shared_secret = recipient_private_key.exchange(
        ec.ECDH(),
        ephemeral_public_key,
    )

    salt = base64.b64decode(envelope["salt_b64"])
    nonce = base64.b64decode(envelope["nonce_b64"])
    ciphertext = base64.b64decode(envelope["ciphertext_b64"])

    aes_key = derive_key(shared_secret, salt)
    aesgcm = AESGCM(aes_key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise RuntimeError("ECIES decryption failed: invalid key or corrupted ciphertext") from exc

    return plaintext.decode("utf-8")
