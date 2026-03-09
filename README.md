# CS 216 Bitcoin Transaction Lab

**Team:** HighOnByte

| Name | Roll Number |
|------|------------|
| Aastha | 240004001 |
| Bhavika Jaiswal | 240001017 |
| Sanskriti Jain | 240001064 |
| Suhani | 240001077 |

## Setup
```bash
pip install python-bitcoinrpc
bitcoind -daemon && sleep 3
bitcoin-cli createwallet "lab_wallet"
bitcoin-cli generatetoaddress 101 $(bitcoin-cli getnewaddress)
```

## Run
```bash
python3 part1_legacy.py
python3 part2_segwit.py
python3 part3_comparison.py
```

## Network: Regtest | Port: 18443 | Host: 127.0.0.1
