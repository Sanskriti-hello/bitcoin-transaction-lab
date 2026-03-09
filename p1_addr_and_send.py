#!/usr/bin/env python3
# part 1 - genarate adresses and send from A to B
# CS216 assignment 2

import json
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy

# rpc creds
usr  = "student"
pwd  = "cs216bitcoin"
host = "127.0.0.1"
port = 18443

# helper to get connectoin
def conn():
    return AuthServiceProxy(f"http://{usr}:{pwd}@{host}:{port}")

# mine some bloks to confirm txns
def mine_blks(n=6):
    c = conn()
    addr = c.getnewaddress()
    c.generatetoaddress(n, addr)
    print(f"mined {n} bloks")

# custom encoder bcz decimal not json serializable
class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


print("\n--- generating 3 legacy adresses ---")
rpc = conn()

# generate legacy (p2pkh) adresses
addrA = rpc.getnewaddress("myA", "legacy")
addrB = rpc.getnewaddress("myB", "legacy")
addrC = rpc.getnewaddress("myC", "legacy")

print("addr A:", addrA)
print("addr B:", addrB)
print("addr C:", addrC)

# save adresses to file
addrs = {"A": addrA, "B": addrB, "C": addrC}
with open("legacy_addrs.json", "w") as f:
    json.dump(addrs, f, indent=2)
print("saved adresses to legacy_addrs.json")


print("\n--- funding addr A ---")
# send 1 btc to addr A
fund_txid = rpc.sendtoaddress(addrA, 1.0)
print("funding txid:", fund_txid)

# mine to confirm
mine_blks(6)

# check utxos at A
utxos = rpc.listunspent(1, 9999999, [addrA])
print("\nutxos at A:")
for u in utxos:
    print("  txid:", u["txid"])
    print("  vout:", u["vout"])
    print("  amt:", u["amount"])


print("\n--- making txn A to B ---")
utxo = utxos[0]
fee  = Decimal("0.0001")
amt  = round(utxo["amount"] - fee, 8)

print(f"input: {utxo['txid']}:{utxo['vout']}")
print(f"sending {amt} btc to B")

# create raw txn
inp = [{"txid": utxo["txid"], "vout": utxo["vout"]}]
out = {addrB: amt}
raw = rpc.createrawtransaction(inp, out)

# decode unsigned to see scriptpubkey (challenge script)
decoded_unsigned = rpc.decoderawtransaction(raw)
spk_b = decoded_unsigned["vout"][0]["scriptPubKey"]

print("\n[challenge script / scriptPubKey for addr B]")
print("  type :", spk_b["type"])
print("  asm  :", spk_b["asm"])
print("  hex  :", spk_b["hex"])

# sign the txn using wallet
signed = rpc.signrawtransactionwithwallet(raw)
if not signed["complete"]:
    print("ERROR: signing failed!")
    exit(1)

signed_hex = signed["hex"]
print("\nsigning done")

# decode signed txn
decoded_signed = rpc.decoderawtransaction(signed_hex)
print("\n[decoded signed A->B txn]")
print(json.dumps(decoded_signed, indent=2, cls=MyEncoder))

# brodcast txn
txid_ab = rpc.sendrawtransaction(signed_hex)
print("\nbroadcasted! txid A->B:", txid_ab)
mine_blks(6)

# save state so part2 script can use it
state = {
    "addrs"      : {"A": addrA, "B": addrB, "C": addrC},
    "txid_ab"    : txid_ab,
    "signed_hex" : signed_hex,
    "spk_b"      : spk_b
}
with open("p1_state.json", "w") as f:
    json.dump(state, f, indent=2, cls=MyEncoder)

print("\nsaved state -> p1_state.json")
print("run p1_spend_b.py next")
