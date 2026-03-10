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

This project implements and compares two types of Bitcoin transactions on a local **regtest** network using Python and Bitcoin Core RPC:

- **Part 1a** — Generate 3 legacy P2PKH addresses (A, B, C), fund A, send A → B
- **Part 1b** — Use `listunspent` to find UTXO at B, send B → C, decode and analyze scripts
- **Part 2** — Same flow with SegWit P2SH-P2WPKH addresses (A', B', C')
- **Part 3** — Compare transaction sizes, weight, and script structure between both types

Each transaction's **challenge script** (scriptPubKey) and **response script** (scriptSig + witness) are decoded and explained. btcdeb is used to step through the script execution opcode-by-opcode and verify both transactions are valid.

---

## What We Found

| Metric | P2PKH (B→C) | SegWit (B'→C') | Savings |
|--------|-------------|----------------|---------|
| Size (bytes) | 191 | 215 | SegWit larger raw |
| vSize (vbytes) | 191 | 134 | **29.8% smaller** |
| Weight (WU) | 764 | 533 | **30.2% smaller** |

SegWit moves the signature and pubkey (~104 bytes) from `scriptSig` into the `witness` field. Witness bytes are counted at **weight ×1** instead of ×4, giving a 75% discount and making SegWit cheaper to broadcast despite being larger in raw bytes.

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
cat > ~/.bitcoin/bitcoin.conf << 'CONF'
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
CONF
```

### 3. Start Bitcoin and create wallet

```bash
bitcoind -daemon
sleep 5
bitcoin-cli createwallet "lab_wallet"
bitcoin-cli generatetoaddress 101 $(bitcoin-cli getnewaddress)
bitcoin-cli getbalance   # should show ~50 BTC
```

The 101 blocks are needed because coinbase rewards require 100 confirmations before they can be spent.

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

Run scripts **in order** — Part 1b reads state saved by Part 1a, and Part 3 reads both summary JSONs.

```bash
# Part 1a — generate legacy addresses A B C, fund A, send A->B
python3 p1_addr_and_send.py

# Part 1b — listunspent at B, build B->C, decode scripts
python3 p1_spend_b.py

# Part 2 — generate segwit addresses A' B' C', full A'->B'->C' chain
python3 p2_segwit.py

# Part 3 — compare sizes, weights, script bytes
python3 p3_compare.py
```

Each script prints decoded scripts, TXIDs, and sizes to the terminal and saves results to a `*_summary.json` file.

---

## Addresses Generated

### Legacy P2PKH (Part 1)
| Label | Address |
|-------|---------|
| A | `msHDz1o3mFxQjKBw7CAxrLW1crF2TTpr7b` |
| B | `mxnRfURkaEPpGdmf6EqkmgGg9ggJGJU5cN` |
| C | `mtqvSHwe7fC6Eux36REkK9P7iDHk8H3Gjo` |

### SegWit P2SH-P2WPKH (Part 2)
| Label | Address |
|-------|---------|
| A' | `2NB1Cu2NFNCcSznZKNoR9iMa4nbn9PpiJyz` |
| B' | `2NCnYAi5GMLZy5ZdKykoQjM6LfNXSuJE7yc` |
| C' | `2N595UZAVXjsRDH9XowziXSqDf9USSseyuo` |

---

## Transaction IDs

### Part 1 — Legacy P2PKH
| Transaction | TXID |
|-------------|------|
| Fund → A | `899317b6f6cf0d1412e8c04aaabaa1730747e399b5c937e54b3a1876adbb1941` |
| A → B | `105e2c9e37135a3ab0404843b6df6452f5368bd40f64500ea93b8feb050a2e1a` |
| B → C | `160f61723c69bb41cd3a1bdace88b556760cca76189d35c28b68deb48b34cad3` |

### Part 2 — SegWit P2SH-P2WPKH
| Transaction | TXID |
|-------------|------|
| Fund → A' | `4919888a7cfb58e37cf80ee308edd94e8987f8b0393cb1e3257dc662090806bc` |
| A' → B' | `a450765063eaee4fc9a9ddc5af4f1ce1ec88255054f0187ff920719ae83fb872` |
| B' → C' | `c2531d0daa98f93eb7656946a4793fecd8c877d3b4f3b1cdfa079678339fa8f9` |

---

## Script Analysis

### P2PKH Scripts (Part 1)

**Challenge script (scriptPubKey) — locks output to B:**
```
OP_DUP OP_HASH160 bd67397892887d1af275e31173a53cd8a376107d OP_EQUALVERIFY OP_CHECKSIG
hex: 76a914bd67397892887d1af275e31173a53cd8a376107d88ac  (25 bytes)
```

**Response script (scriptSig) — unlocks B's UTXO in B→C tx:**
```
<sig 304402200bde2b...acf551[ALL]> <pubkey 031888c85e...ae333005>
hex: 47304402200bde...  (106 bytes — signature + pubkey all in scriptSig)
```

### SegWit Scripts (Part 2)

**Challenge script (scriptPubKey) — locks output to B':**
```
OP_HASH160 d65675dc37e796a31825573b45d20467b48fc3cf OP_EQUAL
hex: a914d65675dc37e796a31825573b45d20467b48fc3cf87  (23 bytes)
```

**Response scriptSig — only the redeemScript (23 bytes):**
```
hex: 16001404e5bad950f4ee912914c9d9eee8c173b7826102
decoded redeemScript: OP_0 <hash160(pubKey)>  (P2WPKH witness program)
```

**Witness data (segregated, 75% weight discount):**
```
[0] signature: 304402203d1089a2...dc3fe01  (~71 bytes)
[1] pubkey:    038019cda07cd3b7...c193f    (33 bytes)
```

---

## btcdeb Screenshots

### Part 1 — P2PKH Script Execution (8 steps)

btcdeb was run with the signed B→C transaction and A→B as the input UTXO. It confirms `sigversion=SIGVERSION_BASE` and final stack `[01]` = valid.

| Step | Screenshot | What Happens |
|------|-----------|--------------|
| Initial load | ![](screenshots/p1_btcdeb_00_initial.png) | 8 op script loaded, witness stack size 0 |
| Step 0 | ![](screenshots/p1_btcdeb_01_sig_pushed.png) | Signature pushed from scriptSig |
| Step 1 | ![](screenshots/p1_btcdeb_02_pubkey_pushed.png) | Public key pushed |
| Step 2 | ![](screenshots/p1_btcdeb_03_OP_DUP.png) | OP_DUP: pubkey duplicated |
| Step 3 | ![](screenshots/p1_btcdeb_04_OP_HASH160.png) | OP_HASH160: pubkey hashed |
| Step 4 | ![](screenshots/p1_btcdeb_05_hash_pushed.png) | Expected hash pushed |
| Step 5 | ![](screenshots/p1_btcdeb_06_OP_EQUALVERIFY.png) | OP_EQUALVERIFY: hashes match |
| Step 6 | ![](screenshots/p1_btcdeb_07_OP_CHECKSIG_before.png) | OP_CHECKSIG executing |
| Step 7 ✅ | ![](screenshots/p1_btcdeb_08_OP_CHECKSIG_success.png) | result: success — stack [01] |

### Part 2 — SegWit Script Execution (5 steps)

btcdeb detects `witness stack of size 2`, extracts the P2WPKH payload, and runs the inner 5-opcode script. Confirms `sigversion=SIGVERSION_WITNESS_V0`.

| Step | Screenshot | What Happens |
|------|-----------|--------------|
| Initial load | ![](screenshots/p2_btcdeb_00_initial.png) | 5 ops, witness stack 2, P2WPKH extracted |
| Step 0 | ![](screenshots/p2_btcdeb_01_OP_DUP.png) | OP_DUP: pubkey duplicated |
| Step 1 | ![](screenshots/p2_btcdeb_02_OP_HASH160.png) | OP_HASH160: pubkey hashed |
| Step 2 | ![](screenshots/p2_btcdeb_03_hash_pushed.png) | Expected hash pushed |
| Step 3 | ![](screenshots/p2_btcdeb_04_OP_EQUALVERIFY.png) | OP_EQUALVERIFY: hashes match |
| Step 4 ✅ | ![](screenshots/p2_btcdeb_05_OP_CHECKSIG_success.png) | result: success — stack [01] |

---

## Repository Structure

```
bitcoin-transaction-lab/
├── p1_addr_and_send.py      # Part 1a: generate addresses, fund A, A->B
├── p1_spend_b.py            # Part 1b: listunspent, B->C, script analysis
├── p2_segwit.py             # Part 2: segwit A'->B'->C'
├── p3_compare.py            # Part 3: size and script comparison
├── p1_state.json            # state passed from Part 1a to 1b
├── part1_summary.json       # Part 1 decoded scripts, TXIDs, sizes
├── part2_summary.json       # Part 2 decoded scripts, TXIDs, sizes
├── part3_summary.json       # comparison output
├── legacy_addrs.json        # generated P2PKH addresses
├── segwit_addrs.json        # generated SegWit addresses
├── screenshots/             # btcdeb execution screenshots
│   ├── p1_btcdeb_00_initial.png
│   ├── p1_btcdeb_01_sig_pushed.png
│   ├── p1_btcdeb_02_pubkey_pushed.png
│   ├── p1_btcdeb_03_OP_DUP.png
│   ├── p1_btcdeb_04_OP_HASH160.png
│   ├── p1_btcdeb_05_hash_pushed.png
│   ├── p1_btcdeb_06_OP_EQUALVERIFY.png
│   ├── p1_btcdeb_07_OP_CHECKSIG_before.png
│   ├── p1_btcdeb_08_OP_CHECKSIG_success.png
│   ├── p2_btcdeb_00_initial.png
│   ├── p2_btcdeb_01_OP_DUP.png
│   ├── p2_btcdeb_02_OP_HASH160.png
│   ├── p2_btcdeb_03_hash_pushed.png
│   ├── p2_btcdeb_04_OP_EQUALVERIFY.png
│   └── p2_btcdeb_05_OP_CHECKSIG_success.png
├── Bitcoin.pdf               # full lab report with all analysis
└── README.md
```

---

## Network Details

| Parameter | Value |
|-----------|-------|
| Network | Regtest (local, no real BTC) |
| RPC Host | 127.0.0.1 |
| RPC Port | 18443 |
| RPC User | student |
| Wallet | lab_wallet |
