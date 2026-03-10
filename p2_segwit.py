#!/usr/bin/env python3
# part 2 - segwit p2sh-p2wpkh transactions
# A' -> B' -> C'

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
    print(f"mined {n} bloks")

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


rpc = conn()
fee = Decimal("0.0001")

print("\n--- generating segwit adresses A B C ---")
# p2sh-segwit type gives us p2sh-p2wpkh adresses
addrA2 = rpc.getnewaddress("segA", "p2sh-segwit")
addrB2 = rpc.getnewaddress("segB", "p2sh-segwit")
addrC2 = rpc.getnewaddress("segC", "p2sh-segwit")

print("addr A':", addrA2)
print("addr B':", addrB2)
print("addr C':", addrC2)

with open("segwit_addrs.json", "w") as f:
    json.dump({"A": addrA2, "B": addrB2, "C": addrC2}, f, indent=2)
print("saved to segwit_addrs.json")


print("\n--- funding addr A' ---")
fund = rpc.sendtoaddress(addrA2, 1.0)
print("funding txid:", fund)
mine_blks(6)

utxos_a2 = rpc.listunspent(1, 9999999, [addrA2])
print("\nutxos at A':")
for u in utxos_a2:
    print("  txid:", u["txid"], " amt:", u["amount"])


print("\n--- txn A' to B' ---")
utxo_a2 = utxos_a2[0]
amt_a2b2 = round(utxo_a2["amount"] - fee, 8)

raw_a2b2 = rpc.createrawtransaction(
    [{"txid": utxo_a2["txid"], "vout": utxo_a2["vout"]}],
    {addrB2: amt_a2b2}
)

# decode unsigned - see p2sh challenge script for B'
dec_u_a2b2 = rpc.decoderawtransaction(raw_a2b2)
spk_b2 = dec_u_a2b2["vout"][0]["scriptPubKey"]

print("\n[challenge script for addr B']")
print("  type:", spk_b2["type"])
print("  asm :", spk_b2["asm"])
print("  hex :", spk_b2["hex"])

# sign
sig_a2b2 = rpc.signrawtransactionwithwallet(raw_a2b2)
if not sig_a2b2["complete"]:
    print("signing failed!")
    exit(1)

hex_a2b2 = sig_a2b2["hex"]
print("signing done")

# decode signed - see scriptsig + witness
dec_s_a2b2  = rpc.decoderawtransaction(hex_a2b2)
print("\n[decoded signed A'->B']")
print(json.dumps(dec_s_a2b2, indent=2, cls=MyEncoder))

ssig_a2b2 = dec_s_a2b2["vin"][0]["scriptSig"]
wit_a2b2  = dec_s_a2b2["vin"][0].get("txinwitness", [])

print("\n[response scriptsig]")
print("  asm:", ssig_a2b2["asm"])
print("  hex:", ssig_a2b2["hex"])

print("\n[witness data - segregated]")
for i, w in enumerate(wit_a2b2):
    lbl = "signature" if i == 0 else "pubkey"
    print(f"  [{i}] {lbl}: {w}")

# brodcast
txid_a2b2 = rpc.sendrawtransaction(hex_a2b2)
print("\nbroadcasted! txid A'->B':", txid_a2b2)
mine_blks(6)


print("\n--- txn B' to C' ---")
utxos_b2 = rpc.listunspent(1, 9999999, [addrB2])
print("utxos at B':")
for u in utxos_b2:
    print("  txid:", u["txid"], " amt:", u["amount"])

utxo_b2 = utxos_b2[0]

# verify chain
if utxo_b2["txid"] != txid_a2b2:
    print("ERROR: utxo chain broken!")
    exit(1)
print("chain ok: utxo at B' came from A'->B' txn")

amt_b2c2 = round(utxo_b2["amount"] - fee, 8)

raw_b2c2 = rpc.createrawtransaction(
    [{"txid": utxo_b2["txid"], "vout": utxo_b2["vout"]}],
    {addrC2: amt_b2c2}
)

# decode unsigned
dec_u_b2c2 = rpc.decoderawtransaction(raw_b2c2)
spk_c2 = dec_u_b2c2["vout"][0]["scriptPubKey"]

print("\n[challenge script for addr C']")
print("  type:", spk_c2["type"])
print("  asm :", spk_c2["asm"])
print("  hex :", spk_c2["hex"])

# sign
sig_b2c2 = rpc.signrawtransactionwithwallet(raw_b2c2)
if not sig_b2c2["complete"]:
    print("signing failed!")
    exit(1)

hex_b2c2 = sig_b2c2["hex"]

# decode signed
dec_s_b2c2 = rpc.decoderawtransaction(hex_b2c2)
print("\n[decoded signed B'->C']")
print(json.dumps(dec_s_b2c2, indent=2, cls=MyEncoder))

ssig_b2c2 = dec_s_b2c2["vin"][0]["scriptSig"]
wit_b2c2  = dec_s_b2c2["vin"][0].get("txinwitness", [])

print("\n[response scriptsig]")
print("  asm:", ssig_b2c2["asm"])
print("  hex:", ssig_b2c2["hex"])

print("\n[witness data]")
for i, w in enumerate(wit_b2c2):
    lbl = "signature" if i == 0 else "pubkey"
    print(f"  [{i}] {lbl}: {w}")

print("\n[challenge vs response]")
print("challenge spk B':", spk_b2["asm"])
print("response ssig   :", ssig_b2c2["asm"])
print("witness sig     :", wit_b2c2[0][:40], "...")
print("witness pubkey  :", wit_b2c2[1] if len(wit_b2c2) > 1 else "na")

# brodcast
txid_b2c2 = rpc.sendrawtransaction(hex_b2c2)
print("\nbroadcasted! txid B'->C':", txid_b2c2)
mine_blks(6)


print("\n--- txn sizes ---")
info_a2b2 = rpc.decoderawtransaction(hex_a2b2)
info_b2c2 = rpc.decoderawtransaction(hex_b2c2)

for lbl, inf in [("A'->B'", info_a2b2), ("B'->C'", info_b2c2)]:
    print(f"\n{lbl}:")
    print(f"  size  : {inf.get('size')} bytes")
    print(f"  vsize : {inf.get('vsize')} vbytes")
    print(f"  weight: {inf.get('weight')} WU")


print("\n--- btcdeb command ---")
print(f"btcdeb --tx={hex_b2c2} --txin={hex_a2b2}")


# save summary
summ = {
    "addrs": {"A": addrA2, "B": addrB2, "C": addrC2},
    "txns": {
        "A_to_B": {
            "txid"   : txid_a2b2,
            "spk_b2" : spk_b2,
            "ssig"   : ssig_a2b2,
            "witness": wit_a2b2
        },
        "B_to_C": {
            "txid"   : txid_b2c2,
            "spk_c2" : spk_c2,
            "ssig"   : ssig_b2c2,
            "witness": wit_b2c2
        }
    },
    "sizes": {
        "A_to_B": {"size": info_a2b2.get("size"), "vsize": info_a2b2.get("vsize"), "weight": info_a2b2.get("weight")},
        "B_to_C": {"size": info_b2c2.get("size"), "vsize": info_b2c2.get("vsize"), "weight": info_b2c2.get("weight")}
    },
    "btcdeb": f"btcdeb --tx={hex_b2c2} --txin={hex_a2b2}"
}

with open("part2_summary.json", "w") as f:
    json.dump(summ, f, indent=2, cls=MyEncoder)

print("\nsaved to part2_summary.json")
print("\n=== part 2 done ===")
