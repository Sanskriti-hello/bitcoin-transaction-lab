#!/usr/bin/env python3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal): return float(o)
        return super().default(o)

def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# Load both summaries
with open("part1_summary.json") as f:
    p1 = json.load(f)
with open("part2_summary.json") as f:
    p2 = json.load(f)

sep("PART 3: Transaction Size Comparison")

p1_ab = p1["sizes"]["A_to_B"]
p1_bc = p1["sizes"]["B_to_C"]
p2_ab = p2["sizes"]["A_prime_to_B_prime"]
p2_bc = p2["sizes"]["B_prime_to_C_prime"]

print(f"\n{'Metric':<12} {'P2PKH A→B':<16} {'SegWit A→B':<16} {'P2PKH B→C':<16} {'SegWit B→C':<16} {'Savings (B→C)'}")
print("-"*90)

for metric, unit in [("size","bytes"), ("vsize","vbytes"), ("weight","WU")]:
    v1ab = p1_ab[metric]
    v2ab = p2_ab[metric]
    v1bc = p1_bc[metric]
    v2bc = p2_bc[metric]
    savings = f"{((v1bc - v2bc) / v1bc * 100):.1f}%" if v1bc else "N/A"
    print(f"{metric+' ('+unit+')':<12} {str(v1ab):<16} {str(v2ab):<16} {str(v1bc):<16} {str(v2bc):<16} {savings}")

sep("Script Structure Comparison")

p1_scripts = p1["transactions"]
p2_scripts = p2["transactions"]

print("\n── P2PKH (Legacy) Scripts ──")
print(f"  scriptPubKey (challenge): {p1_scripts['A_to_B']['challenge_script_B']['asm']}")
print(f"  scriptSig    (response):  {p1_scripts['B_to_C']['response_script']['asm']}")
print(f"  Witness:                  NONE — all data on-chain in scriptSig")

print("\n── P2SH-P2WPKH (SegWit) Scripts ──")
print(f"  scriptPubKey (challenge): {p2_scripts['A_prime_to_B_prime']['challenge_script_B_prime']['asm']}")
print(f"  scriptSig    (response):  {p2_scripts['B_prime_to_C_prime']['response_scriptsig']['asm']}")
w = p2_scripts["B_prime_to_C_prime"]["witness"]
print(f"  Witness[0]   (signature): {w[0] if w else 'N/A'}")
print(f"  Witness[1]   (pubkey):    {w[1] if len(w)>1 else 'N/A'}")

sep("Script Size Breakdown")

p1_spk = p1_scripts["A_to_B"]["challenge_script_B"]["hex"]
p1_sig = p1_scripts["B_to_C"]["response_script"]["hex"]
p2_spk = p2_scripts["A_prime_to_B_prime"]["challenge_script_B_prime"]["hex"]
p2_sig = p2_scripts["B_prime_to_C_prime"]["response_scriptsig"]["hex"]

print(f"\n  P2PKH scriptPubKey hex length: {len(p1_spk)//2} bytes  ({p1_spk})")
print(f"  P2PKH scriptSig    hex length: {len(p1_sig)//2} bytes")
print(f"\n  SegWit scriptPubKey hex length: {len(p2_spk)//2} bytes  ({p2_spk})")
print(f"  SegWit scriptSig    hex length: {len(p2_sig)//2} bytes")
w_bytes = sum(len(x)//2 for x in w)
print(f"  SegWit witness      total size: {w_bytes} bytes (counted at 1/4 weight)")

sep("Why SegWit is Smaller — Explanation")

print("""
  1. WEIGHT DISCOUNT
     ─────────────────────────────────────────────────────
     P2PKH: signature lives in scriptSig → counted ×4 weight
     SegWit: signature lives in witness  → counted ×1 weight
     
     Formula:
       weight  = (non-witness bytes × 4) + (witness bytes × 1)
       vbytes  = ceil(weight / 4)

  2. SCRIPT SIZE
     ─────────────────────────────────────────────────────
     P2PKH scriptPubKey:  25 bytes
       OP_DUP OP_HASH160 <20B hash> OP_EQUALVERIFY OP_CHECKSIG
     
     P2SH scriptPubKey:   23 bytes
       OP_HASH160 <20B hash> OP_EQUAL
     
     P2PKH scriptSig:     ~107 bytes  (sig ~72B + pubkey 33B + pushdata)
     SegWit scriptSig:    ~23 bytes   (just redeemScript push)
     SegWit witness:      ~107 bytes  (sig + pubkey moved here at ×1 weight)

  3. FEE BENEFIT
     ─────────────────────────────────────────────────────
     Bitcoin fees = fee_rate × vbytes
     Fewer vbytes = lower fees
     SegWit saves ~25-30% in fees compared to P2PKH

  4. BLOCK CAPACITY
     ─────────────────────────────────────────────────────
     Block limit = 4,000,000 weight units
     SegWit txs use fewer weight units per tx
     → More transactions fit per block
     → Higher throughput without increasing block size
""")

sep("Saving Comparison Summary")

comparison = {
    "size_comparison": {
        "P2PKH_B_to_C":   p1_bc,
        "SegWit_B_to_C":  p2_bc,
        "savings_vsize":  f"{((p1_bc['vsize'] - p2_bc['vsize']) / p1_bc['vsize'] * 100):.1f}%"
    },
    "script_sizes_bytes": {
        "P2PKH_scriptPubKey": len(p1_spk)//2,
        "P2PKH_scriptSig":    len(p1_sig)//2,
        "SegWit_scriptPubKey": len(p2_spk)//2,
        "SegWit_scriptSig":    len(p2_sig)//2,
        "SegWit_witness":      w_bytes
    }
}

with open("part3_summary.json", "w") as f:
    json.dump(comparison, f, indent=2)

print("✓ Saved to part3_summary.json")
print("\n" + "="*60)
print("  PART 3 COMPLETE ✓")
print("="*60)
