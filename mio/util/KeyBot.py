# -*- coding: utf-8 -*-
import os
import rsa
import base64
from typing import Optional, List


class KeyBot(object):
    __key_path__: str
    __pubkey__: Optional[rsa.PublicKey] = None
    __privkey__: Optional[rsa.PrivateKey] = None

    def __init__(self, key_path: Optional[str] = None):
        # 如果只想做一次性加密，就不需要设置文件路径
        self.__key_path = key_path
        if key_path:
            if not os.path.isdir(key_path):
                os.makedirs(key_path)

    def gen_new_key(self, is_save: bool = True, nbits: int = 2048, accurate: bool = True, poolsize: int = 1,
                    exponent: int = 65537):
        pubkey, privkey = rsa.newkeys(nbits, accurate, poolsize, exponent)
        self.__pubkey__ = pubkey
        self.__privkey__ = privkey
        if is_save and self.__key_path:
            privkey_file: str = '{}/privkey.pem'.format(self.__key_path)
            pubkey_file: str = '{}/cacert.pem'.format(self.__key_path)
            priv = self.__privkey__.save_pkcs1()
            with open(privkey_file, 'wb+') as f:
                f.write(priv)
            pub = self.__pubkey__.save_pkcs1()
            with open(pubkey_file, 'wb+') as f:
                f.write(pub)

    def __load_key__(self, key_type: int):
        key_file: str = 'privkey.pem' if key_type == 1 else 'cacert.pem'
        paths: List[str] = [self.__key_path, key_file]
        key_file = os.path.sep.join(paths)
        if not os.path.isfile(key_file):
            return
        with open(key_file, 'rb') as kf:
            p = kf.read()
        if key_type == 1:
            self.__privkey__ = rsa.PrivateKey.load_pkcs1(p)
        else:
            self.__pubkey__ = rsa.PublicKey.load_pkcs1(p)

    def encrypt(self, msg: str) -> Optional[bytes]:
        if self.__pubkey__ is None:
            self.__load_key__(0)
            if self.__pubkey__ is None:
                return None
        message: bytes = msg.encode('utf-8')
        crypto: bytes = rsa.encrypt(message, self.__pubkey__)
        return crypto

    def base64_encrypt(self, msg: str) -> Optional[str]:
        crypto = self.encrypt(msg)
        if crypto is None:
            return None
        ec: bytes = base64.b64encode(crypto)
        return str(ec, encoding="utf-8")

    def decrypt(self, crypto: bytes) -> Optional[str]:
        if self.__privkey__ is None:
            self.__load_key__(1)
            if self.__privkey__ is None:
                return None
        message: bytes = rsa.decrypt(crypto, self.__privkey__)
        msg: str = str(message, encoding="utf-8")
        return msg

    def base64_decrypt(self, crypto: str) -> Optional[str]:
        crypto_message: bytes = base64.b64decode(crypto)
        message: Optional[str] = self.decrypt(crypto_message)
        return message

    def get_base64_pubkey(self) -> Optional[str]:
        if self.__pubkey__ is None:
            self.__load_key__(0)
            if self.__pubkey__ is None:
                return None
        kfc: bytes = base64.b64encode(self.__pubkey__.save_pkcs1())
        return str(kfc, encoding="utf-8")

    def get_base64_privkey(self) -> Optional[str]:
        if self.__privkey__ is None:
            self.__load_key__(1)
            if self.__privkey__ is None:
                return None
        kfc: bytes = base64.b64encode(self.__privkey__.save_pkcs1())
        return str(kfc, encoding="utf-8")

    def set_base64_pubkey(self, crypto: str):
        crypto_message: bytes = base64.b64decode(crypto)
        self.__pubkey__ = rsa.PublicKey.load_pkcs1(crypto_message)

    def set_base64_privkey(self, crypto: str):
        crypto_message: bytes = base64.b64decode(crypto)
        self.__privkey__ = rsa.PrivateKey.load_pkcs1(crypto_message)

    def get_pubkey(self) -> Optional[bytes]:
        if self.__pubkey__ is None:
            self.__load_key__(0)
            if self.__pubkey__ is None:
                return None
        return self.__pubkey__.save_pkcs1()

    def get_privkey(self) -> Optional[bytes]:
        if self.__privkey__ is None:
            self.__load_key__(1)
            if self.__privkey__ is None:
                return None
        return self.__privkey__.save_pkcs1()

    def set_pubkey(self, crypto_message: bytes):
        self.__pubkey__ = rsa.PublicKey.load_pkcs1(crypto_message)

    def set_privkey(self, crypto_message: bytes):
        self.__privkey__ = rsa.PrivateKey.load_pkcs1(crypto_message)
