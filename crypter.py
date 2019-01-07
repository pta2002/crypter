#!/bin/env python3
import configparser
import subprocess
import getpass
import sys
import os

SETTINGS = {}

# TODO check if gpg command succeeded before removing the file... 
def encrypt_file(keys, file) -> None:
    r = subprocess.run(["gpg", "--output", file+".enc", "--encrypt", "--recipient", keys, file])
    if r.returncode == 0:
        subprocess.run(["shred", "-uzn", "10", file])
    else:
        print(f"Failed to encrypt file {file!r}, not removing", file=sys.stderr)

def decrypt_file(file, password):
    r = subprocess.run(["gpg", "--output", file[:-4], "--batch", "--passphrase", password, "--decrypt", file], capture_output=True)
    if r.returncode == 0:
        os.remove(file)
    else:
        print(f"Failed to decrypt file {file!r}, not removing", file=sys.stderr)

def init(dir, symmetric=False, key=None):
    pass

def find_dir():
    odir = os.getcwd()
    while odir != "/":
        if os.path.isfile(os.path.join(odir, ".crypter")):
            return odir
        
        odir = os.path.abspath(os.path.join(odir, "../"))
    
    return None

def lock_dir(key, _path):
    for path, _, files in os.walk(_path):
        for file in files:
            if not file.endswith(".enc") and file != ".crypter" and file != ".filenames":
                encrypt_file(key, os.path.join(path, file))
    if SETTINGS['jumble'] and not os.path.isfile(os.path.join(find_dir(), ".filenames.enc")):
        basedir = find_dir()
        jumble(_path)
        encrypt_file(key, os.path.join(basedir, ".filenames"))

def unlock_dir(_path, passphrase):
    if SETTINGS['jumble'] and os.path.isfile(os.path.join(find_dir(), ".filenames.enc")):
        decrypt_file(os.path.join(find_dir(), ".filenames.enc"), passphrase)
        unjumble(_path)
        os.remove(os.path.join(find_dir(), ".filenames"))

    for path, _, files in os.walk(_path):
        for file in files:
            if file.endswith(".enc"):
                decrypt_file(os.path.join(path, file), passphrase)
    
def unjumble(path):
    names = []
    basepath = find_dir()
    with open(os.path.join(basepath, ".filenames"), 'r') as f:
        for line in f:
            l = line.strip()
            if l != "":
                names.append(l.split(":"))
    
    for name in names:
        dir = os.path.join(basepath, os.path.dirname(name[1]))
        finalpath = os.path.join(basepath, name[1])
        curpath = os.path.join(basepath, name[0])
        if not os.path.isdir(dir):
            os.makedirs(dir)
        os.rename(curpath, finalpath)

def jumble(_path):
    counter = 0
    names = []
    basepath = find_dir()
    for path, _, files in os.walk(_path):
        for file in files:
            if file.endswith(".enc") and file != ".filenames.enc":
                curpath = os.path.join(path, file)
                newpath = str(counter) + ".enc"
                names.append((newpath, os.path.relpath(curpath, basepath)))

                os.rename(curpath, os.path.join(basepath, newpath))

                counter += 1

    delete_subdirs(basepath)

    with open(os.path.join(basepath, '.filenames'), 'w') as f:
        text = ""
        for name in names:
            text += f'{name[0]}:{name[1]}\n'
        f.write(text)

def delete_subdirs(path):
    subdirs = next(os.walk(path))[1]
    for dir in subdirs:
        delete_subdirs(os.path.join(path, dir))
        if os.listdir(os.path.join(path, dir)) == []:
            os.rmdir(os.path.join(path, dir))

def main():
    config = configparser.ConfigParser()
    dir = find_dir()
    if dir == None:
        print("Crypter config file not found.", file=sys.stderr)
        sys.exit(1)
    
    config.read(os.path.join(dir, ".crypter"))

    SETTINGS['key'] = config.get('config', 'key', fallback=None)
    SETTINGS['jumble'] = config.get('config', 'jumble', fallback=True)
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
