# CS 216: Bitcoin Transaction Lab

**Team HighOnByte** | 2nd Programming Assignment | March 2026

| Name | Roll Number |
|------|------------|
| Aastha | 240004001 |
| Bhavika Jaiswal | 240001017 |
| Sanskriti Jain | 240001064 |
| Suhani | 240001077 |

---

## Overview

This project implements Bitcoin transactions on a local regtest network using Python and Bitcoin Core RPC. It covers:

- **Part 1** — Legacy P2PKH transactions (A → B → C)
- **Part 2** — SegWit P2SH-P2WPKH transactions (A' → B' → C')
- **Part 3** — Comparative analysis of transaction sizes and script structures

---

## Prerequisites

- Ubuntu 22.04 (or WSL2 on Windows)
- Bitcoin Core 26.0
- Python 3.10+
- btcdeb (Bitcoin Script Debugger)

---

## Setup

### 1. Install Bitcoin Core

```bash
wget https://bitcoincore.org/bin/bitcoin-core-26.0/bitcoin-26.0-x86_64-linux-gnu.tar.gz
tar -xzf bitcoin-26.0-x86_64-linux-gnu.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin bitcoin-26.0/bin/*
```

### 2. Configure Bitcoin

```bash
mkdir -p ~/.bitcoin
cat > ~/.bitcoin/bitcoin.conf << 'EOF'
regtest=1
server=1
txindex=1

[regtest]
rpcuser=student
rpcpassword=cs216bitcoin
rpcport=18443
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
paytxfee=0.0001
fallbackfee=0.0002
mintxfee=0.00001
txconfirmtarget=6
EOF
```

### 3. Start Bitcoin and create wallet

```bash
bitcoind -daemon
sleep 5
bitcoin-cli createwallet "lab_wallet"
bitcoin-cli generatetoaddress 101 $(bitcoin-cli getnewaddress)
bitcoin-cli getbalance   # should show 50.0 BTC
```

### 4. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install python-bitcoinrpc
```

### 5. Install btcdeb

```bash
sudo apt install -y autoconf libtool pkg-config libssl-dev git make g++
git clone https://github.com/bitcoin-core/btcdeb.git
cd btcdeb && ./autogen.sh && ./configure && make -j$(nproc) && sudo make install
```

---

## Running the Code

Make sure bitcoind is running and the venv is active before each run.

```bash
source venv/bin/activate
```

```bash
# Part 1 — Legacy P2PKH
python3 part1_legacy.py

# Part 2 — SegWit P2SH-P2WPKH
python3 part2_segwit.py

# Part 3 — Comparison
python3 part3_comparison.py
```

Each script saves its output to a `*_summary.json` file and prints all decoded scripts, TXIDs, and sizes to the terminal.

---

## Repository Structure

```
bitcoin-transaction-lab/
├── part1_legacy.py          # Part 1: P2PKH transactions
├── part2_segwit.py          # Part 2: SegWit transactions
├── part3_comparison.py      # Part 3: Size and script comparison
├── part1_summary.json       # Part 1 output data
├── part2_summary.json       # Part 2 output data
├── part3_summary.json       # Part 3 comparison data
├── legacy_addresses.json    # Generated P2PKH addresses
├── segwit_addresses.json    # Generated SegWit addresses
├── screenshots/             # btcdeb execution screenshots
│   ├── p1_btcdeb_*.png      # Part 1 P2PKH script steps
│   └── p2_btcdeb_*.png      # Part 2 SegWit script steps
├── report.pdf               # Full lab report
└── README.md
```

---

## Network Details

| Parameter | Value |
|-----------|-------|
| Network | Regtest |
| RPC Host | 127.0.0.1 |
| RPC Port | 18443 |
| RPC User | student |
| Wallet | lab_wallet |
