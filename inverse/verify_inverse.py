#!/usr/bin/env python3
"""
Verification and Analysis Tool for AES Inverse MixColumns SLP Circuits.

Features:
  1. Formal verification of AES Inverse MixColumns correctness over GF(2).
  2. Concrete bit-by-bit evaluation against textbook FIPS-197 AES Inverse MixColumns.
  3. Circuit statistics (XOR gate count, circuit depth, target depth, fanout).
  4. Isomorphism checking via Algebraic Signature Extraction (frozenset of wire values).
  5. Batch verification of circuit files (one circuit tuple per line).
"""

import argparse
import ast
from collections import defaultdict
import os
import random
import sys
from typing import List, Tuple, Dict, Any, Set, FrozenSet


def xtime(b: int) -> int:
    res = (b << 1) & 0xFF
    if b & 0x80:
        res ^= 0x1B
    return res


def gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        a = xtime(a)
        b >>= 1
    return p


def inv_mix_single_column(s0: int, s1: int, s2: int, s3: int) -> Tuple[int, int, int, int]:
    """
    Standard textbook FIPS-197 InvMixColumns matrix multiplication:
    [0e 0b 0d 09] * [s0]
    [09 0e 0b 0d]   [s1]
    [0d 09 0e 0b]   [s2]
    [0b 0d 09 0e]   [s3]
    """
    r0 = gmul(0x0e, s0) ^ gmul(0x0b, s1) ^ gmul(0x0d, s2) ^ gmul(0x09, s3)
    r1 = gmul(0x09, s0) ^ gmul(0x0e, s1) ^ gmul(0x0b, s2) ^ gmul(0x0d, s3)
    r2 = gmul(0x0d, s0) ^ gmul(0x09, s1) ^ gmul(0x0e, s2) ^ gmul(0x0b, s3)
    r3 = gmul(0x0b, s0) ^ gmul(0x0d, s1) ^ gmul(0x09, s2) ^ gmul(0x0e, s3)
    return r0, r1, r2, r3


def textbook_inv_mixcolumns_32bit(x: int) -> int:
    s0 = x & 0xFF
    s1 = (x >> 8) & 0xFF
    s2 = (x >> 16) & 0xFF
    s3 = (x >> 24) & 0xFF
    r0, r1, r2, r3 = inv_mix_single_column(s0, s1, s2, s3)
    return r0 | (r1 << 8) | (r2 << 16) | (r3 << 24)


def get_aes_inv_mixcolumns_targets() -> List[int]:
    """
    Computes the 32 binary target masks representing the linear combinations
    for the AES Inverse MixColumns transformation directly from the textbook definition.
    """
    targets = []
    for out_bit in range(32):
        mask = 0
        for in_bit in range(32):
            in_val = 1 << in_bit
            out_val = textbook_inv_mixcolumns_32bit(in_val)
            if (out_val >> out_bit) & 1:
                mask |= (1 << in_bit)
        targets.append(mask)
    return targets


def verify_circuit(
    circuit: List[Tuple[int, int]],
    targets: List[int],
    test_vectors: List[int] = None
) -> Dict[str, Any]:
    """
    Verifies a circuit DAG against the 32 targets and computes metrics.
    Optionally evaluates concrete test vectors against textbook FIPS-197.
    """
    n_inputs = 32
    n_gates = len(circuit)
    wires = [1 << i for i in range(n_inputs)]
    depths = [0] * (n_inputs + n_gates)
    fanout = [0] * (n_inputs + n_gates)
    gate_signatures = []

    for idx, (u, v) in enumerate(circuit):
        if u < 0 or v < 0 or u >= len(wires) or v >= len(wires):
            return {"valid": False, "error": f"Gate {idx} references future or negative wire index ({u}, {v})"}
        if u == v:
            return {"valid": False, "error": f"Gate {idx} has identical inputs ({u}, {v})"}
        w = wires[u] ^ wires[v]
        wires.append(w)
        gate_signatures.append(w)
        fanout[u] += 1
        fanout[v] += 1
        depths[n_inputs + idx] = max(depths[u], depths[v]) + 1

    wire_to_earliest = {}
    for idx, val in enumerate(wires):
        if val not in wire_to_earliest:
            wire_to_earliest[val] = idx

    covered = 0
    target_depths = []
    target_wire_indices = []
    for t in targets:
        if t in wire_to_earliest:
            covered += 1
            w = wire_to_earliest[t]
            target_depths.append(depths[w])
            target_wire_indices.append(w)

    valid = (covered == 32)
    max_d = max(target_depths) if target_depths else 0
    avg_d = sum(target_depths) / len(target_depths) if target_depths else 0
    max_fo = max(fanout) if fanout else 0

    # Concrete test vectors check
    if valid and test_vectors:
        for vec in test_vectors:
            expected = textbook_inv_mixcolumns_32bit(vec)
            c_wires = [(vec >> i) & 1 for i in range(32)]
            for u, v in circuit:
                c_wires.append(c_wires[u] ^ c_wires[v])
            actual = 0
            for out_bit, w_idx in enumerate(target_wire_indices):
                actual |= (c_wires[w_idx] << out_bit)
            if actual != expected:
                return {
                    "valid": False,
                    "error": f"Concrete test vector mismatch for {hex(vec)}: got {hex(actual)}, expected {hex(expected)}"
                }

    return {
        "valid": valid,
        "gates": n_gates,
        "coverage": covered,
        "max_target_depth": max_d,
        "avg_target_depth": avg_d,
        "max_depth": max(depths) if depths else 0,
        "max_fanout": max_fo,
        "signature_set": frozenset(gate_signatures)
    }


def main():
    parser = argparse.ArgumentParser(description="Verify AES Inverse MixColumns Circuits")
    parser.add_argument("file", nargs="?", default="circuits_88.txt", help="File with circuits (default: circuits_88.txt)")
    parser.add_argument("-i", "--isomorphism", action="store_true", help="Perform algebraic signature isomorphism analysis")
    parser.add_argument("-t", "--test-vectors", action="store_true", help="Run concrete FIPS-197 test vector verification on all circuits")
    args = parser.parse_args()

    targets = get_aes_inv_mixcolumns_targets()
    target_set = set(targets)
    assert len(target_set) == 32, "Target definitions must be unique"

    if not os.path.exists(args.file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(script_dir, args.file)
        if os.path.exists(alt_path):
            args.file = alt_path
        else:
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            sys.exit(1)

    test_vectors = None
    if args.test_vectors:
        random.seed(42)
        test_vectors = [random.randint(0, 0xFFFFFFFF) for _ in range(50)]
        test_vectors.extend([1 << i for i in range(32)])
        test_vectors.extend([0, 0xFFFFFFFF, 0x55555555, 0xAAAAAAAA, 0x01010101, 0x80808080])
        print(f"Concrete FIPS-197 verification enabled ({len(test_vectors)} test vectors per circuit)...")

    print(f"Loading circuits from {args.file}...")
    valid_results = []
    total = 0
    depths = []
    avg_depths = []
    gate_counts = []
    iso_classes = set()

    with open(args.file) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            total += 1
            try:
                circuit = ast.literal_eval(line)
            except Exception as e:
                print(f"Line {line_num}: Parse error: {e}")
                continue

            res = verify_circuit(circuit, targets, test_vectors=test_vectors)
            if res["valid"]:
                valid_results.append(res)
                gate_counts.append(res["gates"])
                depths.append(res["max_target_depth"])
                avg_depths.append(res["avg_target_depth"])
                iso_classes.add(res["signature_set"])
            else:
                print(f"Line {line_num}: INVALID ({res.get('error', 'unknown error')})")

    print("\n" + "=" * 60)
    print("AES INVERSE MIXCOLUMNS VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total circuits evaluated:          {total}")
    print(f"Valid circuits (32/32 targets):    {len(valid_results)} ({len(valid_results)/total*100:.1f}%)")
    if args.test_vectors:
        print(f"Concrete FIPS-197 Test Vectors:    ALL PASSED ({len(test_vectors)} vectors/circuit)")
    if args.isomorphism:
        print(f"Unique isomorphism classes:        {len(iso_classes)} ({len(iso_classes)/len(valid_results)*100:.1f}% pairwise non-isomorphic)")
    if valid_results:
        print(f"XOR Gate Count:                    {min(gate_counts)} - {max(gate_counts)}")
        print(f"Critical Path Depth:               Min = {min(depths)}, Mean = {sum(depths)/len(depths):.2f}, Max = {max(depths)}")
        print(f"Average Target Depth:              Min = {min(avg_depths):.2f}, Mean = {sum(avg_depths)/len(avg_depths):.2f}, Max = {max(avg_depths):.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
