#!/usr/bin/env python3
import json
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy

RPC_USER     = "student"
RPC_PASSWORD = "cs216bitcoin"
RPC_HOST     = "127.0.0.1"
RPC_PORT     = 18443

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal): return float(o)
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

# ── STEP 1: Generate 3 SegWit Addresses ──
sep("STEP 1: Generate P2SH-SegWit Addresses A', B', C'")
rpc = get_rpc()

addr_A2 = rpc.getnewaddress("segwit_A", "p2sh-segwit")
addr_B2 = rpc.getnewaddress("segwit_B", "p2sh-segwit")
addr_C2 = rpc.getnewaddress("segwit_C", "p2sh-segwit")

print(f"Address A': {addr_A2}")
print(f"Address B': {addr_B2}")
print(f"Address C': {addr_C2}")

with open("segwit_addresses.json", "w") as f:
    json.dump({"A_prime": addr_A2, "B_prime": addr_B2, "C_prime": addr_C2}, f, indent=2, cls=DecimalEncoder)
print("✓ Saved to segwit_addresses.json")

# ── STEP 2: Fund Address A' ──
sep("STEP 2: Fund Address A'")

txid_fund = rpc.sendtoaddress(addr_A2, 1.0)
print(f"Funding txid: {txid_fund}")
print(f"Sent 1.0 BTC → Address A'")
mine(6)

utxos_A2 = rpc.listunspent(1, 9999999, [addr_A2])
print(f"\nUTXOs at A':")
for u in utxos_A2:
    print(f"  txid: {u['txid']}")
    print(f"  vout: {u['vout']}")
    print(f"  amount: {u['amount']} BTC")

# ── STEP 3: Transaction A' → B' ──
sep("STEP 3: Transaction A' → B'")

utxo_A2  = utxos_A2[0]
fee      = Decimal("0.0001")
send_A2B2 = round(utxo_A2["amount"] - fee, 8)

print(f"Input:  {utxo_A2['txid']}:{utxo_A2['vout']}")
print(f"Amount: {utxo_A2['amount']} BTC  |  Fee: {fee}  |  Sending: {send_A2B2} BTC")

raw_A2B2 = rpc.createrawtransaction(
    [{"txid": utxo_A2["txid"], "vout": utxo_A2["vout"]}],
    {addr_B2: send_A2B2}
)

# Decode UNSIGNED — shows P2SH scriptPubKey (challenge script for B')
dec_unsigned_A2B2 = rpc.decoderawtransaction(raw_A2B2)
spk_B2 = dec_unsigned_A2B2["vout"][0]["scriptPubKey"]

print(f"\n[CHALLENGE SCRIPT — scriptPubKey for Address B']")
print(f"  type: {spk_B2['type']}")
print(f"  asm:  {spk_B2['asm']}")
print(f"  hex:  {spk_B2['hex']}")

# Sign
signed_A2B2     = rpc.signrawtransactionwithwallet(raw_A2B2)
assert signed_A2B2["complete"], "Signing failed!"
hex_signed_A2B2 = signed_A2B2["hex"]
print(f"\n✓ Signed successfully")

# Decode SIGNED — shows scriptSig + witness
dec_signed_A2B2 = rpc.decoderawtransaction(hex_signed_A2B2)
print(f"\n[Full decoded SIGNED A'→B' tx]")
print(json.dumps(dec_signed_A2B2, indent=2, cls=DecimalEncoder))

ssig_A2B2    = dec_signed_A2B2["vin"][0]["scriptSig"]
witness_A2B2 = dec_signed_A2B2["vin"][0].get("txinwitness", [])

print(f"\n[RESPONSE SCRIPT — scriptSig]")
print(f"  asm: {ssig_A2B2['asm']}")
print(f"  hex: {ssig_A2B2['hex']}")

print(f"\n[WITNESS DATA (segregated signature)]")
for i, w in enumerate(witness_A2B2):
    label = "signature" if i == 0 else "public key"
    print(f"  [{i}] ({label}): {w}")

# Broadcast
txid_A2B2 = rpc.sendrawtransaction(hex_signed_A2B2)
print(f"\n✓ Broadcast! txid A'→B': {txid_A2B2}")
mine(6)

# ── STEP 4: Transaction B' → C' ──
sep("STEP 4: Transaction B' → C'")

utxos_B2 = rpc.listunspent(1, 9999999, [addr_B2])
print("UTXOs at B':")
for u in utxos_B2:
    print(f"  txid: {u['txid']}  vout: {u['vout']}  amount: {u['amount']}")

utxo_B2 = utxos_B2[0]
assert utxo_B2["txid"] == txid_A2B2, "ERROR: UTXO chain broken!"
print(f"\n✓ Confirmed: UTXO at B' came from txid A'→B'")

send_B2C2 = round(utxo_B2["amount"] - fee, 8)

raw_B2C2 = rpc.createrawtransaction(
    [{"txid": utxo_B2["txid"], "vout": utxo_B2["vout"]}],
    {addr_C2: send_B2C2}
)

# Decode UNSIGNED B'→C'
dec_unsigned_B2C2 = rpc.decoderawtransaction(raw_B2C2)
spk_C2 = dec_unsigned_B2C2["vout"][0]["scriptPubKey"]
print(f"\n[CHALLENGE SCRIPT — scriptPubKey for Address C']")
print(f"  type: {spk_C2['type']}")
print(f"  asm:  {spk_C2['asm']}")
print(f"  hex:  {spk_C2['hex']}")

# Sign
signed_B2C2     = rpc.signrawtransactionwithwallet(raw_B2C2)
assert signed_B2C2["complete"], "Signing failed!"
hex_signed_B2C2 = signed_B2C2["hex"]

# Decode SIGNED B'→C' — shows scriptSig + witness (response)
dec_signed_B2C2 = rpc.decoderawtransaction(hex_signed_B2C2)
print(f"\n[Full decoded SIGNED B'→C' tx]")
print(json.dumps(dec_signed_B2C2, indent=2, cls=DecimalEncoder))

ssig_B2C2    = dec_signed_B2C2["vin"][0]["scriptSig"]
witness_B2C2 = dec_signed_B2C2["vin"][0].get("txinwitness", [])

print(f"\n[RESPONSE SCRIPT — scriptSig]")
print(f"  asm: {ssig_B2C2['asm']}")
print(f"  hex: {ssig_B2C2['hex']}")

print(f"\n[WITNESS DATA (segregated signature)]")
for i, w in enumerate(witness_B2C2):
    label = "signature" if i == 0 else "public key"
    print(f"  [{i}] ({label}): {w}")

print(f"\n[CHALLENGE vs RESPONSE CHECK]")
print(f"  Challenge (scriptPubKey B'): {spk_B2['asm']}")
print(f"  Response  (scriptSig B'→C'): {ssig_B2C2['asm']}")
print(f"  Witness[0] signature:        {witness_B2C2[0] if witness_B2C2 else 'N/A'}")
print(f"  Witness[1] pubkey:           {witness_B2C2[1] if len(witness_B2C2)>1 else 'N/A'}")

# Broadcast
txid_B2C2 = rpc.sendrawtransaction(hex_signed_B2C2)
print(f"\n✓ Broadcast! txid B'→C': {txid_B2C2}")
mine(6)

# ── STEP 5: Size Info ──
sep("STEP 5: Transaction Sizes")

info_A2B2 = rpc.getrawtransaction(txid_A2B2, True)
info_B2C2 = rpc.getrawtransaction(txid_B2C2, True)

for label, info in [("A'→B'", info_A2B2), ("B'→C'", info_B2C2)]:
    print(f"\nTx {label}:")
    print(f"  size:   {info.get('size')} bytes")
    print(f"  vsize:  {info.get('vsize')} vbytes")
    print(f"  weight: {info.get('weight')} WU")

# ── STEP 6: btcdeb command ──
sep("STEP 6: btcdeb Validation Command (run separately)")
print(f"\nbtcdeb --tx={hex_signed_B2C2} --txin={hex_signed_A2B2}")

# ── Save summary ──
sep("Saving Summary")
summary = {
    "addresses": {"A_prime": addr_A2, "B_prime": addr_B2, "C_prime": addr_C2},
    "transactions": {
        "A_prime_to_B_prime": {
            "txid": txid_A2B2,
            "challenge_script_B_prime": spk_B2,
            "response_scriptsig": ssig_A2B2,
            "witness": witness_A2B2
        },
        "B_prime_to_C_prime": {
            "txid": txid_B2C2,
            "challenge_script_C_prime": spk_C2,
            "response_scriptsig": ssig_B2C2,
            "witness": witness_B2C2
        }
    },
    "sizes": {
        "A_prime_to_B_prime": {"size": info_A2B2.get("size"), "vsize": info_A2B2.get("vsize"), "weight": info_A2B2.get("weight")},
        "B_prime_to_C_prime": {"size": info_B2C2.get("size"), "vsize": info_B2C2.get("vsize"), "weight": info_B2C2.get("weight")},
    },
    "btcdeb_command": f"btcdeb --tx={hex_signed_B2C2} --txin={hex_signed_A2B2}"
}

with open("part2_summary.json", "w") as f:
    json.dump(summary, f, indent=2, cls=DecimalEncoder)

print("✓ Saved to part2_summary.json")
print("\n" + "="*60)
print("  PART 2 COMPLETE ✓")
print("="*60)
