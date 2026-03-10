#!/usr/bin/env python3
# part 3 - compare p2pkh vs segwit
# loads data from part1 and part2 summaries

import json

print("loading summaries...")

with open("part1_summary.json") as f:
    p1 = json.load(f)

with open("part2_summary.json") as f:
    p2 = json.load(f)


print("\n========== size comparison ==========")

# get sizes - using B->C txns for fair comparison
p1_sz = p1["sizes"]["B_to_C"]
p2_sz = p2["sizes"]["B_to_C"]

print(f"\n{'metric':<14} {'p2pkh':>10} {'segwit':>10} {'savings':>10}")
print("-" * 46)

for m, unit in [("size", "bytes"), ("vsize", "vbytes"), ("weight", "WU")]:
    v1 = p1_sz[m]
    v2 = p2_sz[m]
    diff = round(((v1 - v2) / v1) * 100, 2) if v1 else 0
    print(f"{m+' ('+unit+')':<14} {str(v1):>10} {str(v2):>10} {str(diff)+'%':>10}")


print("\n========== script structure comparison ==========")

p1_spk_b = p1["txns"]["A_to_B"]["spk_b"]
p2_spk_b = p2["txns"]["A_to_B"]["spk_b2"]
p1_ssig  = p1["txns"]["B_to_C"]["ssig"]
p2_ssig  = p2["txns"]["B_to_C"]["ssig"]
p2_wit   = p2["txns"]["B_to_C"]["witness"]

print("\np2pkh:")
print(f"  scriptpubkey : {p1_spk_b['asm']}")
print(f"  scriptsig    : {p1_ssig['asm'][:80]}...")
print(f"  witness      : none")

print("\nsegwit:")
print(f"  scriptpubkey : {p2_spk_b['asm']}")
print(f"  scriptsig    : {p2_ssig['asm']}")
print(f"  witness[0]   : {p2_wit[0][:60]}... (signature)")
print(f"  witness[1]   : {p2_wit[1]} (pubkey)")


print("\n========== script sizes in bytes ==========")

spk1_bytes = len(p1_spk_b["hex"]) // 2
sig1_bytes = len(p1_ssig["hex"]) // 2
spk2_bytes = len(p2_spk_b["hex"]) // 2
sig2_bytes = len(p2_ssig["hex"]) // 2
wit_bytes  = sum(len(w) // 2 for w in p2_wit)

print(f"\np2pkh scriptpubkey : {spk1_bytes} bytes")
print(f"p2pkh scriptsig    : {sig1_bytes} bytes (sig+pubkey all here)")
print(f"p2pkh witness      : 0 bytes")

print(f"\nsegwit scriptpubkey: {spk2_bytes} bytes")
print(f"segwit scriptsig   : {sig2_bytes} bytes (only redeemscript)")
print(f"segwit witness     : {wit_bytes} bytes (sig+pubkey moved here)")


print("\n========== why segwit is smaller ==========")
print("""
in p2pkh all data including sig is in scriptsig
scriptsig bytes are counted at weight x4

in segwit sig+pubkey moves to witness field
witness bytes counted at weight x1 (75% discount!!)

weight formula:
  weight = (non-witness bytes x 4) + (witness bytes x 1)
  vbytes = ceil(weight / 4)

p2pkh example:
  191 bytes, no witness
  weight = 191 x 4 = 764 WU
  vbytes = 764 / 4 = 191

segwit example:
  ~108 non-witness + ~107 witness
  weight = (108 x 4) + (107 x 1) = 432 + 107 = 539 WU
  vbytes = ceil(539/4) = 135
  (actual measured 533 WU -> 134 vbytes)

fee saving at 10 sat/vbyte:
  p2pkh  -> 191 x 10 = 1910 sats
  segwit -> 134 x 10 = 1340 sats
  saving -> 570 sats per txn (~30%)

other benefits:
  - fixes txn malleability (sig not in txid calc anymore)
  - enables lightning network
  - more txns per block (higher throughput)
""")


# save comparison
out = {
    "size_comparison": {
        "p2pkh_B_to_C" : p1_sz,
        "segwit_B_to_C": p2_sz,
        "vsize_saving" : f"{round(((p1_sz['vsize'] - p2_sz['vsize']) / p1_sz['vsize']) * 100, 2)}%"
    },
    "script_bytes": {
        "p2pkh_spk"  : spk1_bytes,
        "p2pkh_ssig" : sig1_bytes,
        "segwit_spk" : spk2_bytes,
        "segwit_ssig": sig2_bytes,
        "segwit_wit" : wit_bytes
    }
}
with open("part3_summary.json", "w") as f:
    json.dump(out, f, indent=2)

print("saved to part3_summary.json")
print("\n=== part 3 done ===")
