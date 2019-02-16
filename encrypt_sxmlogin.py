#!/usr/bin/env python3

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_0AEP
import zlib
import base64

def generate_keypair(bits=4096):
    # Generate pub/priv keypair
    gen_key = RSA.generate(bits, e=65537)
    # Save private key PEM
    priv_key = gen_key.exportKey("PEM")
    # Save public key PEM
    pub_key = gen_key.publicKey().exportKey("PEM")

    print ('Saving private key...')
    save = open("priv_key.pem", "wb")
    save.write(priv_key)
    save.close()

    print('Saving public key...')
    save = open("pub_key.pem", "wb")
    save.write(pub_key)
    save.close()


def encrypt_file(file=None):
    # Check for available public key in $PWD
    try:
        rsa_key = RSA.importKey(pub_key)