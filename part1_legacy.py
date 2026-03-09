#!/usr/bin/env python3
import json
from decimal import Decimal as D
from bitcoinrpc.authproxy import AuthServiceProxy
from decimal import Decimal

RPC_USER     = "student"
RPC_PASSWORD = "cs216bitcoin"
RPC_HOST     = "127.0.0.1"
RPC_PORT     = 18443

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, D): return float(o)
        return super().default(o)

def get_rpc():
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

def mine(n=6):
    rpc = get_rpc()
    addr = rpc.getnewaddress()
    rpc.generatetoaddress(n, addr)
    print(f"  ✓ Mined {n} blocks")

def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ── STEP 1: Generate 3 Legacy Addresses ──
sep("STEP 1: Generate Legacy (P2PKH) Addresses A, B, C")
rpc = get_rpc()

addr_A = rpc.getnewaddress("address_A", "legacy")
addr_B = rpc.getnewaddress("address_B", "legacy")
addr_C = rpc.getnewaddress("address_C", "legacy")

print(f"Address A: {addr_A}")
print(f"Address B: {addr_B}")
print(f"Address C: {addr_C}")

with open("legacy_addresses.json", "w") as f:
    json.dump({"A": addr_A, "B": addr_B, "C": addr_C}, f, indent=2, cls=DecimalEncoder)
print("✓ Saved to legacy_addresses.json")

# ── STEP 2: Fund Address A ──
sep("STEP 2: Fund Address A")

txid_fund = rpc.sendtoaddress(addr_A, 1.0)
print(f"Funding txid: {txid_fund}")
print(f"Sent 1.0 BTC → Address A")
mine(6)

utxos_A = rpc.listunspent(1, 9999999, [addr_A])
print(f"\nUTXOs at A:")
for u in utxos_A:
    print(f"  txid: {u['txid']}")
    print(f"  vout: {u['vout']}")
    print(f"  amount: {u['amount']} BTC")

# ── STEP 3: Transaction A → B ──
sep("STEP 3: Transaction A → B")

utxo_A   = utxos_A[0]
fee      = Decimal("0.0001")
send_AB  = round(utxo_A["amount"] - fee, 8)

print(f"Input:  {utxo_A['txid']}:{utxo_A['vout']}")
print(f"Amount: {utxo_A['amount']} BTC  |  Fee: {fee}  |  Sending: {send_AB} BTC")

raw_AB = rpc.createrawtransaction(
    [{"txid": utxo_A["txid"], "vout": utxo_A["vout"]}],
    {addr_B: send_AB}
)

# Decode UNSIGNED — shows scriptPubKey (challenge script for B)
dec_unsigned_AB = rpc.decoderawtransaction(raw_AB)
spk_B = dec_unsigned_AB["vout"][0]["scriptPubKey"]

print(f"\n[CHALLENGE SCRIPT — scriptPubKey for Address B]")
print(f"  type: {spk_B['type']}")
print(f"  asm:  {spk_B['asm']}")
print(f"  hex:  {spk_B['hex']}")

# Sign
signed_AB     = rpc.signrawtransactionwithwallet(raw_AB)
assert signed_AB["complete"], "Signing failed!"
hex_signed_AB = signed_AB["hex"]
print(f"\n✓ Signed successfully")

# Decode SIGNED — shows scriptSig
dec_signed_AB = rpc.decoderawtransaction(hex_signed_AB)
print(f"\n[Full decoded SIGNED A→B tx]")
print(json.dumps(dec_signed_AB, indent=2, cls=DecimalEncoder))

# Broadcast
txid_AB = rpc.sendrawtransaction(hex_signed_AB)
print(f"\n✓ Broadcast! txid A→B: {txid_AB}")
mine(6)

# ── STEP 4: Transaction B → C ──
sep("STEP 4: Transaction B → C")

utxos_B = rpc.listunspent(1, 9999999, [addr_B])
print("UTXOs at B:")
for u in utxos_B:
    print(f"  txid: {u['txid']}  vout: {u['vout']}  amount: {u['amount']}")

utxo_B   = utxos_B[0]
assert utxo_B["txid"] == txid_AB, "ERROR: UTXO chain broken!"
print(f"\n✓ Confirmed: UTXO at B came from txid A→B")

send_BC = round(utxo_B["amount"] - fee, 8)

raw_BC = rpc.createrawtransaction(
    [{"txid": utxo_B["txid"], "vout": utxo_B["vout"]}],
    {addr_C: send_BC}
)

# Decode UNSIGNED B→C
dec_unsigned_BC = rpc.decoderawtransaction(raw_BC)
spk_C = dec_unsigned_BC["vout"][0]["scriptPubKey"]
print(f"\n[CHALLENGE SCRIPT — scriptPubKey for Address C]")
print(f"  type: {spk_C['type']}")
print(f"  asm:  {spk_C['asm']}")
print(f"  hex:  {spk_C['hex']}")

# Sign
signed_BC     = rpc.signrawtransactionwithwallet(raw_BC)
assert signed_BC["complete"], "Signing failed!"
hex_signed_BC = signed_BC["hex"]

# Decode SIGNED B→C — shows scriptSig (RESPONSE script)
dec_signed_BC = rpc.decoderawtransaction(hex_signed_BC)
print(f"\n[Full decoded SIGNED B→C tx]")
print(json.dumps(dec_signed_BC, indent=2, cls=DecimalEncoder))

ssig_BC = dec_signed_BC["vin"][0]["scriptSig"]
print(f"\n[RESPONSE SCRIPT — scriptSig spending B's UTXO]")
print(f"  asm: {ssig_BC['asm']}")
print(f"  hex: {ssig_BC['hex']}")

print(f"\n[CHALLENGE vs RESPONSE CHECK]")
print(f"  Challenge (scriptPubKey B): {spk_B['asm']}")
print(f"  Response  (scriptSig B→C):  {ssig_BC['asm']}")
print(f"  → scriptSig provides <sig> and <pubKey>")
print(f"  → scriptPubKey hashes pubKey and checks it matches stored hash")

# Broadcast
txid_BC = rpc.sendrawtransaction(hex_signed_BC)
print(f"\n✓ Broadcast! txid B→C: {txid_BC}")
mine(6)

# ── STEP 5: Size Info ──
sep("STEP 5: Transaction Sizes")

info_AB = rpc.getrawtransaction(txid_AB, True)
info_BC = rpc.getrawtransaction(txid_BC, True)

for label, info in [("A→B", info_AB), ("B→C", info_BC)]:
    print(f"\nTx {label}:")
    print(f"  size:   {info.get('size')} bytes")
    print(f"  vsize:  {info.get('vsize')} vbytes")
    print(f"  weight: {info.get('weight')} WU")

# ── STEP 6: btcdeb commands ──
sep("STEP 6: btcdeb Validation Commands (run these separately)")
print(f"\nTo validate B→C script execution, run:")
print(f"\nbtcdeb --tx={hex_signed_BC} --txin={hex_signed_AB}")

# ── Save summary ──
sep("Saving Summary")
summary = {
    "addresses": {"A": addr_A, "B": addr_B, "C": addr_C},
    "transactions": {
        "A_to_B": {
            "txid": txid_AB,
            "challenge_script_B": spk_B,
        },
        "B_to_C": {
            "txid": txid_BC,
            "challenge_script_C": spk_C,
            "response_script": ssig_BC,
        }
    },
    "sizes": {
        "A_to_B": {"size": info_AB.get("size"), "vsize": info_AB.get("vsize"), "weight": info_AB.get("weight")},
        "B_to_C": {"size": info_BC.get("size"), "vsize": info_BC.get("vsize"), "weight": info_BC.get("weight")},
    },
    "btcdeb_command": f"btcdeb --tx={hex_signed_BC} --txin={hex_signed_AB}"
}

with open("part1_summary.json", "w") as f:
    json.dump(summary, f, indent=2, cls=DecimalEncoder)

print("✓ Saved to part1_summary.json")
print("\n" + "="*60)
print("  PART 1 COMPLETE ✓")
print("="*60)
