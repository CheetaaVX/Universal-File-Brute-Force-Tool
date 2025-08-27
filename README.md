## System Requirements

### Minimum Requirements

  Operating System: Linux, Windows 10+, or macOS 10.14+

  Python Version: Python 3.6 or higher

  RAM: 2 GB minimum, 4 GB recommended

  Storage: 100 MB free space for wordlists

______________________________________________________________________________________________


### Recommended Requirements

  CPU: 4-core processor or better

  RAM: 8 GB or more for large wordlists

  Storage: SSD for faster file operations

  Python: Version 3.8 or higher


_______________________________________________________________________________________________

## Installation Steps


Install Required Packages

```bash
# Core required package
pip install pykeepass

# Optional packages for additional format support
pip install rarfile    # For RAR files
pip install py7zr      # For 7Z files
pip install pdfminer.six  # For PDF files

# For Office document support (Linux)
sudo apt install libreoffice
```
## File Structure
```bash
bruteforce_tool/
├── bruteforce.py          # Main script
├── requirements.txt       # Python dependencies
├── wordlists/            # Directory for password lists
│   ├── rockyou.txt       # Common passwords
│   └── custom.txt        # Your custom list
└── target_files/         # Files to test
    ├── database.kdbx
    ├── backup.zip
    └── document.pdf
```
## Supported File Formats

### Fully Supported (with pykeepass)

KDBX - KeePass password databases (.kdbx) - REQUIRES pip install pykeepass

### Partially Supported (may need additional tools)

ZIP - Compressed archives (.zip) - Uses built-in zipfile library

RAR - RAR archives (.rar) - REQUIRES pip install rarfile

7Z - 7-Zip archives (.7z) - REQUIRES pip install py7zr

PDF - Password-protected PDFs (.pdf) - REQUIRES pip install pdfminer.si

## Experimental Support

Office Documents - (.docx, .xlsx, .pptx) - Requires LibreOffice installed

SSH Keys - Encrypted private keys (.id_rsa) - Requires ssh-keygen tool

## Usage Examples

### Basic Single-threaded Usage

```bash
# Test a KeePass database
python bruteforce.py database.kdbx rockyou.txt

# Test a ZIP file  
python bruteforce.py backup.zip common_passwords.txt

# Test with custom wordlist
python bruteforce.py secret.rar my_passwords.txt
```
###  Multi-threaded Usage

```bash
# Use 4 threads
python bruteforce.py target.kdbx wordlist.txt -t 4

# Use 8 threads (faster)
python bruteforce.py target.kdbx wordlist.txt -t 8

# Use all available cores (adjust based on your CPU)
python bruteforce.py target.kdbx wordlist.txt -t 16
```
## Command Line Options

### Syntax
 ```bash
python bruteforce.py [TARGET_FILE] [WORDLIST_FILE] [OPTIONS]
```
### Options Table

### Options Table
| Option    | Description        | Default     | Example |
|-----------|--------------------|-------------|---------|
| -t NUM    | Number of threads  | 0 (single)  | -t 8    |
| --help    | Show help message  | N/A         | --help  |
