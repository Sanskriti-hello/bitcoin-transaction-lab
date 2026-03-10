#!/usr/bin/env python3
# part 1 continued - spend from B to C
# reads state from p1_addr_and_send.py output

import json
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy

usr  = "student"
pwd  = "cs216bitcoin"
host = "127.0.0.1"
port = 18443

def conn():
    return AuthServiceProxy(f"http://{usr}:{pwd}@{host}:{port}")

def mine_blks(n=6):
    c = conn()
    c.generatetoaddress(n, c.getnewaddress())
    print(f"mined {n} blocks")

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# load state from previous script
print("loading state from p1_state.json...")
with open("p1_state.json") as f:
    st = json.load(f)

addrA   = st["addrs"]["A"]
addrB   = st["addrs"]["B"]
addrC   = st["addrs"]["C"]
txid_ab = st["txid_ab"]
hex_ab  = st["signed_hex"]
spk_b   = st["spk_b"]

rpc = conn()
fee = Decimal("0.0001")


print("\n--- listunspent at B (from prev txn A->B) ---")
# get utxos at addrB - should show output from A->B txn
utxos_b = rpc.listunspent(1, 9999999, [addrB])

print("utxos at addr B:")
for u in utxos_b:
    print("  txid  :", u["txid"])
    print("  vout  :", u["vout"])
    print("  amount:", u["amount"])

if not utxos_b:
    raise RuntimeError("No UTXOs found at address B")

utxo_b = utxos_b[0]

# verify chain
assert utxo_b["txid"] == txid_ab, "ERROR: txid mismatch - wrong UTXO"
assert utxo_b["amount"] > 0, "ERROR: UTXO amount is zero"

print(f"\nconfirmed: utxo at B came from txn A->B")
print(f"txid: {txid_ab}")


print("\n--- making txn B to C ---")
amt_bc = (utxo_b["amount"] - fee).quantize(Decimal("0.00000001"))

inp = [{"txid": utxo_b["txid"], "vout": utxo_b["vout"]}]
out = {addrC: amt_bc}
raw_bc = rpc.createrawtransaction(inp, out)

# decode unsigned to see challenge script for C
dec_unsigned = rpc.decoderawtransaction(raw_bc)
spk_c = dec_unsigned["vout"][0]["scriptPubKey"]

print("\n[challenge script for addr C]")
print("  type:", spk_c["type"])
print("  asm :", spk_c["asm"])
print("  hex :", spk_c["hex"])

# sign
signed_bc = rpc.signrawtransactionwithwallet(raw_bc)
if not signed_bc["complete"]:
    print("ERROR: signing failed")
    exit(1)

hex_bc = signed_bc["hex"]

# decode signed - this shows scriptSig (response script)
dec_signed = rpc.decoderawtransaction(hex_bc)
print("\n[decoded signed B->C txn]")
print(json.dumps(dec_signed, indent=2, cls=MyEncoder))

ssig = dec_signed["vin"][0]["scriptSig"]

print("\n[response script / scriptSig that unlocks B utxo]")
print("  asm:", ssig["asm"])
print("  hex:", ssig["hex"])


print("\n--- checking challenge vs response ---")
print("challenge (spk from A->B):")
print(" ", spk_b["asm"])
print("\nresponse (ssig in B->C):")
print(" ", ssig["asm"])
print("\nscriptSig gives <sig> and <pubkey>")
print("scriptPubKey does hash160(pubkey) and checks it matches")
print("then checksig verifies the signature -> if ok txn is valid")

# broadcast
txid_bc = rpc.sendrawtransaction(hex_bc)
print("\nbroadcasted B->C:", txid_bc)
mine_blks(6)


print("\n--- txn sizes ---")
info_ab = rpc.decoderawtransaction(hex_ab)
info_bc = rpc.decoderawtransaction(hex_bc)

for lbl, inf in [("A->B", info_ab), ("B->C", info_bc)]:
    print(f"\n{lbl}:")
    print(f"  size  : {inf.get('size')} bytes")
    print(f"  vsize : {inf.get('vsize')} vbytes")
    print(f"  weight: {inf.get('weight')} WU")


print("\n--- btcdeb command to validate scripts ---")
print(f"btcdeb --tx={hex_bc} --txin={hex_ab}")


# save summary
summ = {
    "addrs": {"A": addrA, "B": addrB, "C": addrC},
    "txns": {
        "A_to_B": {"txid": txid_ab, "spk_b": spk_b},
        "B_to_C": {
            "txid"  : txid_bc,
            "spk_c" : spk_c,
            "ssig"  : ssig
        }
    },
    "sizes": {
        "A_to_B": {"size": info_ab.get("size"), "vsize": info_ab.get("vsize"), "weight": info_ab.get("weight")},
        "B_to_C": {"size": info_bc.get("size"), "vsize": info_bc.get("vsize"), "weight": info_bc.get("weight")}
    },
    "btcdeb": f"btcdeb --tx={hex_bc} --txin={hex_ab}"
}

with open("part1_summary.json", "w") as f:
    json.dump(summ, f, indent=2, cls=MyEncoder)

print("\nsaved to part1_summary.json")
print("\n=== part 1 done ===")
