#!/bin/sh

echo '[+] Starting basic NMAP scan'
nmap -Pn $1
echo '[+] Complete with module'
