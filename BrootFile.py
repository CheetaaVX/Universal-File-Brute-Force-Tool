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
        elif ext in ['.docx', '.xlsx', '.pptx']:
            return 'office'
        elif ext in ['.id_rsa', '.ssh']:
            return 'ssh'
        return 'unknown'
    
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
                    zf.testzip()  # Quick test
                    return True
                    
            # Add more file type handlers here as needed
                    
        except (CredentialsError, RuntimeError, Exception):
            pass
            
        # Progress reporting
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
                brute_forcer.try_password(password)
                    
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
    
    # Read passwords into queue
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
    
    # Start worker threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(brute_forcer, password_queue))
        t.daemon = True
        threads.append(t)
        t.start()
    
    # Wait for completion or interrupt
    try:
        while any(t.is_alive() for t in threads) and not brute_forcer.found:
            time.sleep(0.1)
            if password_queue.qsize() == 0:
                break
                
    except KeyboardInterrupt:
        print("\n[!] Brute force interrupted by user")
        brute_forcer.found = False
    
    # Wait for threads to finish
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
    
    # Check dependencies
    if not KDBX_SUPPORT:
        print("Note: Install 'pip install pykeepass' for KDBX support")
    print()
    
    # Choose mode based on thread count
    if args.threads <= 0:
        # Single-threaded mode
        brute_forcer = brute_force_single(args.target_file, args.wordlist)
    else:
        # Multi-threaded mode
        brute_forcer = brute_force_multi(args.target_file, args.wordlist, args.threads)
    
    # Display results
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
