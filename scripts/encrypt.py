from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes, hmac

import os

from cryptography.fernet import Fernet
import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
import hashlib


class RSA:
    def __init__(self):
        pass

    @staticmethod
    def generate_key_pair():
        """
        Generate a key pair for encryption.

        Returns:
            tuple: A tuple containing the private key and public key in PEM format.
        """
        private_key = _rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    @staticmethod
    def encrypt(plain_text:bytes, public_key):
        public_key = serialization.load_pem_public_key(public_key)
        encrypted = public_key.encrypt(
            plain_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted

    @staticmethod
    def decrypt(cipher_text:bytes, private_key):
        private_key = serialization.load_pem_private_key(private_key, password=None)
        decrypted = private_key.decrypt(
            cipher_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted

class AES:
    def __init__(self):
        pass

    @staticmethod
    def generate_key() -> bytes:
        key = Fernet.generate_key()
        return key
    
    @staticmethod
    def load_key(pem:bytes) -> bytes:
        key = pem.split(b'\n')[1]
        key = key.decode()
        key = urlsafe_b64decode(key)
        while len(key) < 32:
            key += b'\x00'
        key = key[:32]
        return key

    def encrypt(self, plain_text:bytes, key:str):
        return Fernet(key).encrypt(plain_text)

    def decrypt(self, cipher_text:bytes, key:str):
        return Fernet(key).decrypt(cipher_text)
    


def hash_md5(data: bytes) -> bytes:
    md5_hash = hashlib.md5()
    md5_hash.update(data)
    return md5_hash.digest()


def hash_sha256(data: bytes) -> bytes:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.digest()

aes = AES()
rsa = RSA()