#!/bin/env python3
import configparser
import subprocess
import getpass
import sys
import os

SETTINGS = {}

# TODO check if gpg command succeeded before removing the file... 
def encrypt_file(keys, file: str) -> None:
    r = subprocess.run(["gpg", "--output", file+".enc", "--encrypt", "--recipient", keys, file])
    if r.returncode == 0:
        subprocess.run(["shred", "-uzn", "10", file])
    else:
        print("Failed to encrypt file %s, not removing" % file, file=sys.stderr)

def decrypt_file(file: str, password):
    r = subprocess.run(["gpg", "--output", file[:-4], "--batch", "--passphrase", password, "--decrypt", file], capture_output=True)
    if r.returncode == 0:
        os.remove(file)
    else:
        print("Failed to decrypt file %s, not removing" % file, file=sys.stderr)

def init(dir: str, symmetric=False, key=None):
    pass

def find_dir():
    odir = os.getcwd()
    while odir != "/":
        if os.path.isfile(os.path.join(odir, ".crypter")):
            return odir
        
        odir = os.path.abspath(os.path.join(odir, "../"))
    
    return None

def lock_dir(key, path):
    for path, _, files in os.walk(path):
        for file in files:
            if not file.endswith(".enc") and file != ".crypter":
                encrypt_file(key, os.path.join(path, file))

def unlock_dir(path, passphrase):
    for path, _, files in os.walk(path):
        for file in files:
            if file.endswith(".enc"):
                decrypt_file(os.path.join(path, file), passphrase)

def main():
    config = configparser.ConfigParser()
    dir = find_dir()
    if dir == None:
        print("Crypter config file not found.", file=sys.stderr)
        sys.exit(1)
    
    config.read(os.path.join(dir, ".crypter"))

    SETTINGS['key'] = config.get('config', 'key', fallback=None)
    if SETTINGS['key'] == None:
        print("Key not specified in config.", file=sys.stderr)
    
    if sys.argv[1] == "lock":
        print("Locking " + dir)
        lock_dir(SETTINGS['key'], dir)
    elif sys.argv[1] == "unlock":
        print("Unlocking " + dir)
        password = getpass.getpass("GPG password: ")
        unlock_dir(dir, password)
    

if __name__ == "__main__":
    main()