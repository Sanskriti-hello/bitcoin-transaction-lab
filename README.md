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

- **Part 1a** — Generate legacy addresses, fund A, send A → B
- **Part 1b** — listunspent at B, send B → C, analyze scripts
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
bitcoin-cli getbalance
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

Make sure bitcoind is running and venv is active before each run.

```bash
source venv/bin/activate
```

```bash
# Part 1a — generate addresses, fund A, send A->B
python3 p1_addr_and_send.py

# Part 1b — listunspent at B, send B->C, analyze scripts
python3 p1_spend_b.py

# Part 2 — full segwit A'->B'->C'
python3 p2_segwit.py

# Part 3 — size and script comparison
python3 p3_compare.py
```

Part 1b reads state from Part 1a output so run them in order. Each script saves results to a `*_summary.json` file.

---

## Repository Structure

```
bitcoin-transaction-lab/
├── p1_addr_and_send.py      # Part 1a: generate addresses, fund A, A->B
├── p1_spend_b.py            # Part 1b: listunspent, B->C, script analysis
├── p2_segwit.py             # Part 2: segwit A'->B'->C'
├── p3_compare.py            # Part 3: size and script comparison
├── p1_state.json            # state passed from Part 1a to 1b
├── part1_summary.json       # Part 1 output data
├── part2_summary.json       # Part 2 output data
├── part3_summary.json       # Part 3 comparison data
├── legacy_addrs.json        # generated P2PKH addresses
├── segwit_addrs.json        # generated SegWit addresses
├── screenshots/             # btcdeb execution screenshots
│   ├── p1_btcdeb_*.png      # Part 1 P2PKH script steps
│   └── p2_btcdeb_*.png      # Part 2 SegWit script steps
├── report.pdf               # full lab report
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
