# Scripts

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

These are my scripts and utility code for \*nix boxes.

## Quickstart &ndash; install from source

```bash
git clone https://github.com/EvanMcBroom/scripts
pip3 install ./scripts
```

## ...or run in a docker container.

```bash
docker run -it --rm evanmcbroom/scripts
```

## Commands

- [scan](#scan)
- [sserv](#sserv)
- [urlparse](#urlparse)

### scan

Scan a file or directory for a premade list of identifiers or a provided list of words.
The premade list of identifiers includes:
- emails
- domain names
- IMEIs
- IPv4 addresses
- IPv6 address
- MAC addresses
- US phone numbers

The scanner will automatically unarchive and uncompress files if necessary.
Supported archive formats include `Tar` and `Zip`.
Supported compression formats include `Bzip2`, `Gzip`, and `Lzma`.
Files are treated as plaintext by default but my be treated as raw binary data as well.

Scan a binary file for all identifiers and a provided list of words:
```
scan -ab -w wordlist.txt Program.exe
```

### sserv (https.py)

Start an HTTPS server, similar to Python's built-in HTTP server.
You may specify a key and certificate file to use with the server.
If you do not specify a key and certificate, then they will be automatically generated for you.

Start an HTTPS server on port 445:
```
sserv 445
```

### urlparse

URL encode or decode a file(s) or standard input, similar to the `base64` utility.

Decode a file:
```
cat input.txt | urlparse -d
```