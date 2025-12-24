#!/usr/bin/env python3
"""
Universal Brute Force Tool - DUAL MODE
Supports both single-threaded and multi-threaded operation
Usage: 
  Single-thread: python bruteforce.py file.kdbx wordlist.txt
  Multi-thread:  python bruteforce.py file.kdbx wordlist.txt -t 8
  No threads:    python bruteforce.py file.kdbx wordlist.txt -t 1
"""

import sys
import os
import argparse
import threading
import time
import queue
import subprocess
import tempfile
from pathlib import Path

# Import optional dependencies
try:
    from pykeepass import PyKeePass
    from pykeepass.exceptions import CredentialsError
    KDBX_SUPPORT = True
except ImportError:
    KDBX_SUPPORT = False

try:
    import zipfile
    ZIP_SUPPORT = True
except ImportError:
    ZIP_SUPPORT = False

try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP, AES
    SSH_SUPPORT = True
except ImportError:
    SSH_SUPPORT = False

class UniversalBruteForcer:
    def __init__(self, target_file):
        self.target_file = target_file
        self.file_type = self.detect_file_type()
        self.found = False
        self.password = None
        self.attempts = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def detect_file_type(self):
        """Detect the type of file based on extension"""
        path = Path(self.target_file)
        ext = path.suffix.lower()
        
        if ext == '.kdbx':
            return 'kdbx'
        elif ext in ['.zip', '.jar', '.war']:
            return 'zip'
        elif ext == '.rar':
            return 'rar'
        elif ext == '.7z':
            return '7z'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt']:
            return 'office'
        elif ext in ['.id_rsa', '.ssh', '.pem', '.key']:
            return 'ssh'
        return 'unknown'
    
    def try_password_7z(self, password):
        """Try password for 7z archives using 7z command line tool"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
               
                cmd = [
                    '7z', 'x', f'-p{password}', 
                    '-y',  
                    '-o' + tmpdir, y
                    self.target_file
                ]
                
               
                result = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    timeout=5  
                )
                
                
                if result.returncode == 0:
                    return True
                
                
                error_output = result.stderr.decode('utf-8', errors='ignore')
                if "Wrong password" in error_output or "CRC Failed" in error_output:
                    return False
                    
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
            pass
            
        return False
    
    def try_password_rar(self, password):
        """Try password for RAR archives"""
        if not RAR_SUPPORT:
            print("RAR support requires 'pip install rarfile'")
            return False
            
        try:
            with rarfile.RarFile(self.target_file) as rf:
                rf.setpassword(password)
              
                file_list = rf.namelist()
                if file_list:
                    with rf.open(file_list[0], 'r', pwd=password.encode()) as f:
                        f.read(1)  
                    return True
            return False
        except (rarfile.BadRarFile, rarfile.RarCannotExec, rarfile.RarWrongPassword, Exception):
            return False
    
    def try_password_pdf(self, password):
        """Try password for PDF files using qpdf"""
        try:
           
            cmd = [
                'qpdf', '--password=' + password, 
                '--check', self.target_file
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, Exception):
            return False
    
    def try_password_office(self, password):
        """Try password for Office documents using msoffice-crypto"""
        try:
            # Try to import msoffice-crypto
            from msoffice.crypto import OfficeCrypto
            crypto = OfficeCrypto(self.target_file)
            return crypto.load_key(password=password.encode())
        except ImportError:
            print("Office support requires 'pip install msoffice-crypto'")
            return False
        except Exception:
            return False
    
    def try_password_ssh(self, password):
        """Try password for SSH private keys"""
        if not SSH_SUPPORT:
            print("SSH key support requires 'pip install pycryptodome'")
            return False
            
        try:
            with open(self.target_file, 'rb') as f:
                key_data = f.read()
            
            
            key = RSA.import_key(key_data, passphrase=password)
            return key is not None
        except (ValueError, TypeError, Exception):
            return False
    
    def try_password(self, password):
        """Try password for various file types"""
        password = password.strip()
        if not password or self.found:
            return False
            
        with self.lock:
            self.attempts += 1
            
        try:
            if self.file_type == 'kdbx' and KDBX_SUPPORT:
                kp = PyKeePass(self.target_file, password=password)
                return True
                
            elif self.file_type == 'zip' and ZIP_SUPPORT:
                with zipfile.ZipFile(self.target_file) as zf:
                   
                    file_list = zf.namelist()
                    if file_list:
                        with zf.open(file_list[0], pwd=password.encode()) as f:
                            f.read(1)  
                        return True
                return False
                
            elif self.file_type == 'rar':
                return self.try_password_rar(password)
                
            elif self.file_type == '7z':
                return self.try_password_7z(password)
                
            elif self.file_type == 'pdf':
                return self.try_password_pdf(password)
                
            elif self.file_type == 'office':
                return self.try_password_office(password)
                
            elif self.file_type == 'ssh':
                return self.try_password_ssh(password)
                    
        except (CredentialsError, RuntimeError, Exception):
            pass
            
        if self.attempts % 100 == 0:
            elapsed = time.time() - self.start_time
            speed = self.attempts / elapsed if elapsed > 0 else 0
            if threading.active_count() > 1:
                print(f"Attempts: {self.attempts} | Speed: {speed:.1f}/s | Threads: {threading.active_count()-1}")
            else:
                print(f"Attempts: {self.attempts} | Speed: {speed:.1f}/s | Current: {password}")
            
        return False

def brute_force_single(target_file, wordlist):
    """Single-threaded brute force"""
    brute_forcer = UniversalBruteForcer(target_file)
    
    print(f"[+] Starting SINGLE-THREADED brute force on {target_file}")
    print(f"[+] Detected file type: {brute_forcer.file_type.upper()}")
    print(f"[+] Wordlist: {wordlist}")
    print("[+] Press Ctrl+C to stop\n")
    
    try:
        with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            for password in f:
                if brute_forcer.found:
                    break
                if brute_forcer.try_password(password):
                    brute_forcer.password = password.strip()
                    brute_forcer.found = True
                    break
                    
    except KeyboardInterrupt:
        print("\n[!] Brute force interrupted by user")
    
    return brute_forcer

def worker(brute_forcer, password_queue):
    """Worker thread function for multi-threaded mode"""
    while not brute_forcer.found and not password_queue.empty():
        try:
            password = password_queue.get_nowait()
            if brute_forcer.try_password(password):
                with brute_forcer.lock:
                    brute_forcer.found = True
                    brute_forcer.password = password.strip()
            password_queue.task_done()
        except queue.Empty:
            break

def brute_force_multi(target_file, wordlist, num_threads=4):
    """Multi-threaded brute force"""
    brute_forcer = UniversalBruteForcer(target_file)
    
    print(f"[+] Starting MULTI-THREADED brute force on {target_file}")
    print(f"[+] Detected file type: {brute_forcer.file_type.upper()}")
    print(f"[+] Threads: {num_threads}")
    print(f"[+] Wordlist: {wordlist}")
    print("[+] Press Ctrl+C to stop\n")
    
   
    password_queue = queue.Queue()
    try:
        with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip():
                    password_queue.put(line.strip())
    except Exception as e:
        print(f"Error reading wordlist: {e}")
        return brute_forcer
    
    total_passwords = password_queue.qsize()
    print(f"[+] Loaded {total_passwords} passwords into queue")
    
   
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(brute_forcer, password_queue))
        t.daemon = True
        threads.append(t)
        t.start()
    
  
    try:
        while any(t.is_alive() for t in threads) and not brute_forcer.found:
            time.sleep(0.1)
            if password_queue.qsize() == 0:
                break
                
    except KeyboardInterrupt:
        print("\n[!] Brute force interrupted by user")
        brute_forcer.found = False
    
  
    for t in threads:
        t.join(timeout=1)
    
    return brute_forcer

def main():
    parser = argparse.ArgumentParser(description='Dual-Mode Brute Force Tool')
    parser.add_argument('target_file', help='Path to target file')
    parser.add_argument('wordlist', help='Path to wordlist file')
    parser.add_argument('-t', '--threads', type=int, default=0, 
                       help='Number of threads (0=single-threaded, 1+=multi-threaded, default: 0)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target_file):
        print(f"Error: Target file '{args.target_file}' not found")
        return
    
    if not os.path.exists(args.wordlist):
        print(f"Error: Wordlist '{args.wordlist}' not found")
        return
    
   
    file_ext = Path(args.target_file).suffix.lower()
    
    if file_ext == '.7z':
        try:
            subprocess.run(['7z', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[+] 7z utility found")
        except (FileNotFoundError, subprocess.SubprocessError):
            print("[-] Error: 7z utility not found. Install it to support 7z files.")
            print("    On Ubuntu/Debian: sudo apt install p7zip-full")
            print("    On macOS: brew install p7zip")
            print("    On Windows: Download from https://www.7-zip.org/")
            return
    
    if file_ext == '.pdf':
        try:
            subprocess.run(['qpdf', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[+] qpdf utility found")
        except (FileNotFoundError, subprocess.SubprocessError):
            print("[-] Error: qpdf utility not found. Install it to support PDF files.")
            print("    On Ubuntu/Debian: sudo apt install qpdf")
            print("    On macOS: brew install qpdf")
            print("    On Windows: Download from https://sourceforge.net/projects/qpdf/")
            return
    
 
    print("\n[+] Dependency check:")
    if not KDBX_SUPPORT:
        print("  - Install 'pip install pykeepass' for KDBX support")
    if not RAR_SUPPORT:
        print("  - Install 'pip install rarfile' for RAR support")
    if not SSH_SUPPORT:
        print("  - Install 'pip install pycryptodome' for SSH key support")
    if file_ext in ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt']:
        print("  - Install 'pip install msoffice-crypto' for Office document support")
    print()
    
  
    if args.threads <= 0:
      
        brute_forcer = brute_force_single(args.target_file, args.wordlist)
    else:
      
        brute_forcer = brute_force_multi(args.target_file, args.wordlist, args.threads)
    
    elapsed = time.time() - brute_forcer.start_time
    
    if brute_forcer.found:
        print(f"\n[+] SUCCESS: Password found!")
        print(f"[+] Password: {brute_forcer.password}")
        print(f"[+] File type: {brute_forcer.file_type.upper()}")
        print(f"[+] Attempts: {brute_forcer.attempts}")
        print(f"[+] Time: {elapsed:.2f} seconds")
        print(f"[+] Speed: {brute_forcer.attempts/elapsed:.1f} attempts/second")
        
        if args.threads > 0:
            print(f"[+] Mode: Multi-threaded ({args.threads} threads)")
        else:
            print(f"[+] Mode: Single-threaded")
            
    else:
        print(f"\n[!] Password not found in wordlist")
        print(f"[!] Attempts: {brute_forcer.attempts}")
        print(f"[!] Time: {elapsed:.2f} seconds")
        print(f"[!] Speed: {brute_forcer.attempts/elapsed:.1f} attempts/second")

if __name__ == "__main__":
    main()

