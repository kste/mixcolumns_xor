#!/usr/bin/env python3
"""
Verification, Analysis, and Isomorphism Grouping Tool for AES MixColumns SLP Circuits.

Features:
  1. Formal verification of AES MixColumns correctness over GF(2).
  2. Circuit statistics (XOR gate count, circuit depth, output depth, wire fanout).
  3. Isomorphism checking and grouping via Algebraic Signature Extraction.
  4. Optional deduplication and export of unique isomorphism representatives.
"""

import argparse
import ast
from collections import defaultdict
import os
import sys
from typing import Dict, List, Tuple, Any, Set, FrozenSet, Optional, TypedDict


def get_aes_mixcolumns_targets() -> List[int]:
    """
    Computes the 32 binary target masks representing the linear combinations
    for the AES MixColumns transformation.

    Input column: 4 bytes (a0, a1, a2, a3) = bits 0..31.
    MixColumns matrix over GF(2^8) with irreducible polynomial x^8 + x^4 + x^3 + x + 1:
        [02 03 01 01]
        [01 02 03 01]
        [01 01 02 03]
        [03 01 01 02]
    """
    def xtime(b: int) -> int:
        res = (b << 1) & 0xFF
        if b & 0x80:
            res ^= 0x1B
        return res

    # xtime transformation matrix on 8 basis bits (bits 0..7)
    m_xtime = []
    for i in range(8):
        row_mask = 0
        for j in range(8):
            if (xtime(1 << j) >> i) & 1:
                row_mask |= (1 << j)
        m_xtime.append(row_mask)

    targets = []
    # Byte 0: 02*a0 ^ 03*a1 ^ 01*a2 ^ 01*a3
    for i in range(8):
        t = m_xtime[i] ^ ((m_xtime[i] ^ (1 << i)) << 8) ^ ((1 << i) << 16) ^ ((1 << i) << 24)
        targets.append(t)
    # Byte 1: 01*a0 ^ 02*a1 ^ 03*a2 ^ 01*a3
    for i in range(8):
        t = (1 << i) ^ (m_xtime[i] << 8) ^ ((m_xtime[i] ^ (1 << i)) << 16) ^ ((1 << i) << 24)
        targets.append(t)
    # Byte 2: 01*a0 ^ 01*a1 ^ 02*a2 ^ 03*a3
    for i in range(8):
        t = (1 << i) ^ ((1 << i) << 8) ^ (m_xtime[i] << 16) ^ ((m_xtime[i] ^ (1 << i)) << 24)
        targets.append(t)
    # Byte 3: 03*a0 ^ 01*a1 ^ 01*a2 ^ 02*a3
    for i in range(8):
        t = ((m_xtime[i] ^ (1 << i))) ^ ((1 << i) << 8) ^ ((1 << i) << 16) ^ (m_xtime[i] << 24)
        targets.append(t)

    return targets


# Precomputed 32 target masks
MIXCOLUMNS_TARGETS = get_aes_mixcolumns_targets()


class CircuitAnalysisResult(TypedDict):
    valid: bool
    targets_matched: int
    xor_count: int
    circuit_depth: int
    max_output_depth: int
    min_output_depth: int
    avg_output_depth: float
    max_fanout: int
    unique_linear_combinations: int
    output_wires: Dict[int, int]
    signature_set: FrozenSet[int]
    error: Optional[str]


def verify_circuit(circuit: Tuple[Tuple[int, int], ...]) -> CircuitAnalysisResult:
    """
    Simulates and verifies an SLP circuit.

    Args:
        circuit: A sequence of (u, v) pairs where wire 32 + i = wire[u] ^ wire[v].

    Returns:
        A CircuitAnalysisResult containing verification status and circuit statistics.
    """
    k = len(circuit)
    val = [1 << i for i in range(32)]
    depth = [0] * 32
    fanout = [0] * (32 + k)
    gate_signatures = []

    # Simulate circuit
    for idx, (u, v) in enumerate(circuit):
        wire = 32 + idx
        if u < 0 or v < 0 or u >= wire or v >= wire:
            return {
                "valid": False,
                "targets_matched": 0,
                "xor_count": k,
                "circuit_depth": 0,
                "max_output_depth": 0,
                "min_output_depth": 0,
                "avg_output_depth": 0.0,
                "max_fanout": 0,
                "unique_linear_combinations": len(set(val)),
                "output_wires": {},
                "signature_set": frozenset(),
                "error": f"Gate {idx} references invalid wire index ({u}, {v}) for wire {wire}",
            }
        w_val = val[u] ^ val[v]
        val.append(w_val)
        gate_signatures.append(w_val)
        depth.append(max(depth[u], depth[v]) + 1)
        fanout[u] += 1
        fanout[v] += 1

    # Inverted lookup for target matching in O(wires + 32)
    first_wire_of_val: Dict[int, int] = {}
    for w_idx, v_val in enumerate(val):
        if v_val not in first_wire_of_val:
            first_wire_of_val[v_val] = w_idx

    target_wires: Dict[int, int] = {}
    for t_idx, target_mask in enumerate(MIXCOLUMNS_TARGETS):
        if target_mask in first_wire_of_val:
            target_wires[t_idx] = first_wire_of_val[target_mask]

    is_valid = (len(target_wires) == 32)
    output_depths = [depth[w] for w in target_wires.values()] if is_valid else []

    return {
        "valid": is_valid,
        "targets_matched": len(target_wires),
        "xor_count": k,
        "circuit_depth": max(depth) if depth else 0,
        "max_output_depth": max(output_depths) if output_depths else 0,
        "min_output_depth": min(output_depths) if output_depths else 0,
        "avg_output_depth": (sum(output_depths) / len(output_depths)) if output_depths else 0.0,
        "max_fanout": max(fanout) if fanout else 0,
        "unique_linear_combinations": len(set(val)),
        "output_wires": target_wires,
        "signature_set": frozenset(gate_signatures),
        "error": None if is_valid else f"Matched only {len(target_wires)}/32 outputs",
    }


def parse_circuit_line(line: str) -> Optional[Tuple[Tuple[int, int], ...]]:
    """Parses a single line into a canonical tuple of 2-tuples."""
    line = line.strip()
    if not line:
        return None
    obj = ast.literal_eval(line)
    if isinstance(obj, dict):
        if "eval_feedback" in obj and isinstance(obj["eval_feedback"], (list, tuple)) and len(obj["eval_feedback"]) > 0:
            obj = obj["eval_feedback"][0].get("best_circuit", obj)
        elif "best_circuit" in obj:
            obj = obj["best_circuit"]
    if isinstance(obj, (list, tuple)):
        return tuple((min(u, v), max(u, v)) for u, v in obj)
    return None


def verify_file(
    filepath: str,
    verbose: bool = False,
    show_mapping: bool = False,
    check_isomorphism: bool = False
) -> Dict[str, Any]:
    """Verifies all circuits in a file and returns summary statistics."""
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        return {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "valid_results": [],
            "all_results": [],
        }

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"\nVerifying '{filepath}' ({len(lines)} circuits)...")
    print("-" * 70)

    valid_results = []
    invalid_results = []
    all_results = []

    for line_no, line in enumerate(lines, start=1):
        try:
            circuit = parse_circuit_line(line)
            if circuit is None:
                continue
        except Exception as e:
            invalid_results.append((line_no, {"valid": False, "error": f"Parse error: {e}"}))
            continue

        res = verify_circuit(circuit)
        res_dict = dict(res)
        res_dict["circuit"] = circuit
        res_dict["line_no"] = line_no
        all_results.append(res_dict)

        if res["valid"]:
            valid_results.append((line_no, res_dict))
            if verbose:
                print(
                    f"  [Line {line_no:4d}] VALID   | XORs: {res['xor_count']:2d} | "
                    f"Depth: {res['circuit_depth']:2d} | OutDepth: {res['max_output_depth']:2d} "
                    f"(avg: {res['avg_output_depth']:.2f}) | MaxFanout: {res['max_fanout']:2d}"
                )
                if show_mapping:
                    out_list = [res['output_wires'][i] for i in range(32)]
                    print(f"               Output wires 0..31: {out_list}")
        else:
            invalid_results.append((line_no, res_dict))
            if verbose:
                err = res.get('error', f"Matched only {res.get('targets_matched', 0)}/32 outputs")
                print(f"  [Line {line_no:4d}] INVALID | XORs: {res.get('xor_count', 0):2d} | {err}")

    # Summary report
    total = len(lines)
    num_valid = len(valid_results)
    num_invalid = len(invalid_results)

    print(f"\nSummary for '{os.path.basename(filepath)}':")
    print(f"  Total circuits tested : {total}")
    print(f"  Valid MixColumns      : {num_valid} ({num_valid/total*100:.1f}%)" if total else "  Total: 0")
    print(f"  Invalid / Partial     : {num_invalid}")

    if valid_results:
        xor_counts = [r["xor_count"] for _, r in valid_results]
        depths = [r["circuit_depth"] for _, r in valid_results]
        out_depths = [r["max_output_depth"] for _, r in valid_results]
        avg_out_depths = [r["avg_output_depth"] for _, r in valid_results]
        fanouts = [r["max_fanout"] for _, r in valid_results]

        print(f"\nStatistics for Valid Circuits:")
        print(f"  XOR count (min/avg/max)     : {min(xor_counts)} / {sum(xor_counts)/len(xor_counts):.2f} / {max(xor_counts)}")
        print(f"  Circuit depth (min/avg/max) : {min(depths)} / {sum(depths)/len(depths):.2f} / {max(depths)}")
        print(f"  Output depth (min/avg/max)  : {min(out_depths)} / {sum(out_depths)/len(out_depths):.2f} / {max(out_depths)}")
        print(f"  Avg output depth range      : {min(avg_out_depths):.2f} - {max(avg_out_depths):.2f}")
        print(f"  Max wire fanout             : {min(fanouts)} - {max(fanouts)}")

    if check_isomorphism and valid_results:
        iso_groups = defaultdict(list)
        for line_no, r in valid_results:
            iso_groups[r["signature_set"]].append((line_no, r))

        print(f"\nIsomorphism Analysis (Algebraic Signature Extraction):")
        print(f"  Total valid circuits        : {len(valid_results)}")
        print(f"  Unique isomorphism classes  : {len(iso_groups)}")
        sorted_groups = sorted(iso_groups.values(), key=len, reverse=True)
        print(f"  Group sizes (top 10)        : {[len(g) for g in sorted_groups[:10]]}")
        
        if verbose:
            print("\n  Isomorphism Groups Breakdown:")
            for g_id, g in enumerate(sorted_groups, start=1):
                lines_preview = [line_no for line_no, _ in g]
                if len(lines_preview) > 10:
                    lines_str = f"{lines_preview[:10]}... (+{len(lines_preview)-10} more)"
                else:
                    lines_str = str(lines_preview)
                rep = g[0][1]
                print(f"    Class #{g_id:3d} (size {len(g):4d}): lines {lines_str} | Depth: {rep['circuit_depth']} | XORs: {rep['xor_count']}")

    print("=" * 70)
    return {
        "total": total,
        "valid": num_valid,
        "invalid": num_invalid,
        "valid_results": valid_results,
        "all_results": all_results,
    }


def perform_global_isomorphism(file_results: Dict[str, List[Dict[str, Any]]], verbose: bool = False) -> None:
    """Performs cross-file isomorphism analysis across all verified files."""
    global_groups = defaultdict(list)
    file_signatures: Dict[str, Set[FrozenSet[int]]] = defaultdict(set)

    total_circuits = 0
    for filename, results in file_results.items():
        for r in results:
            if r["valid"]:
                sig = r["signature_set"]
                global_groups[sig].append((filename, r["line_no"], r))
                file_signatures[filename].add(sig)
                total_circuits += 1

    print("\n" + "#" * 70)
    print("GLOBAL ISOMORPHISM ANALYSIS ACROSS ALL FILES")
    print("#" * 70)
    print(f"Total valid circuits analyzed    : {total_circuits}")
    print(f"Total unique isomorphism classes : {len(global_groups)}")

    # File-by-file breakdown
    print("\nPer-file unique classes:")
    for filename, sigs in file_signatures.items():
        print(f"  - {os.path.basename(filename)}: {len(sigs)} unique classes")

    # Overlap between pairs of files
    filenames = list(file_signatures.keys())
    if len(filenames) >= 2:
        print("\nPairwise Shared Isomorphism Classes:")
        for i in range(len(filenames)):
            for j in range(i + 1, len(filenames)):
                f1, f2 = filenames[i], filenames[j]
                shared = file_signatures[f1] & file_signatures[f2]
                print(f"  - {os.path.basename(f1)} & {os.path.basename(f2)}: {len(shared)} shared classes")

    sorted_groups = sorted(global_groups.values(), key=len, reverse=True)
    limit = len(sorted_groups) if verbose else min(10, len(sorted_groups))
    title = "\nAll Global Isomorphism Classes:" if verbose else "\nLargest Isomorphism Classes (Top 10):"
    print(title)
    for g_id, g in enumerate(sorted_groups[:limit], start=1):
        file_counts = defaultdict(int)
        for fn, _, _ in g:
            file_counts[os.path.basename(fn)] += 1
        dist_str = ", ".join(f"{fn}: {cnt}" for fn, cnt in file_counts.items())
        rep = g[0][2]
        print(f"  Class #{g_id:3d}: total {len(g):4d} instances ({dist_str}) | XORs: {rep['xor_count']} | Depth: {rep['circuit_depth']}")

    print("#" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Verify AES MixColumns SLP circuits, compute metrics, and perform isomorphism grouping."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Circuit files to verify (default: circuits_1.txt circuits_2.txt)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed results for every circuit and full isomorphism groups",
    )
    parser.add_argument(
        "-m", "--mapping",
        action="store_true",
        help="Display the 32 output wire indices for valid circuits (in verbose mode)",
    )
    parser.add_argument(
        "-i", "--isomorphism",
        action="store_true",
        help="Group circuits into isomorphism equivalence classes via Algebraic Signature Extraction",
    )
    parser.add_argument(
        "-u", "--export-unique",
        type=str,
        metavar="OUTFILE",
        help="Export one representative circuit per unique isomorphism class to OUTFILE",
    )
    parser.add_argument(
        "-c", "--circuit",
        type=str,
        help="Verify a single circuit provided as a string tuple",
    )

    args = parser.parse_args()

    # Single circuit mode
    if args.circuit:
        try:
            c = parse_circuit_line(args.circuit)
            if c is None:
                raise ValueError("Could not parse circuit string.")
            res = verify_circuit(c)
            print("\nSingle Circuit Verification:")
            print(f"  Valid MixColumns : {res['valid']}")
            print(f"  Targets matched  : {res['targets_matched']}/32")
            print(f"  XOR gate count   : {res['xor_count']}")
            print(f"  Circuit depth    : {res['circuit_depth']}")
            if res['error']:
                print(f"  Status Detail    : {res['error']}")
            if res['valid']:
                print(f"  Output depth     : {res['max_output_depth']} (avg: {res['avg_output_depth']:.2f})")
                print(f"  Max wire fanout  : {res['max_fanout']}")
                print(f"  Unique exprs     : {res['unique_linear_combinations']}")
                if args.mapping:
                    out_list = [res['output_wires'][i] for i in range(32)]
                    print(f"  Output wires     : {out_list}")
            sys.exit(0 if res['valid'] else 1)
        except Exception as e:
            print(f"Error parsing circuit string: {e}", file=sys.stderr)
            sys.exit(1)

    files_to_check = args.files
    if not files_to_check:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_files = ["circuits_1.txt", "circuits_2.txt"]
        files_to_check = []
        for df in default_files:
            if os.path.exists(df):
                files_to_check.append(df)
            elif os.path.exists(os.path.join(script_dir, df)):
                files_to_check.append(os.path.join(script_dir, df))

        if not files_to_check:
            print("No circuit files found. Please specify file path(s).", file=sys.stderr)
            sys.exit(1)

    all_passed = True
    file_results = {}
    for fp in files_to_check:
        stats = verify_file(
            fp,
            verbose=args.verbose,
            show_mapping=args.mapping,
            check_isomorphism=args.isomorphism or bool(args.export_unique)
        )
        if stats["invalid"] > 0 or stats["valid"] == 0:
            all_passed = False
        if stats["valid"] > 0:
            file_results[fp] = stats["all_results"]

    if (args.isomorphism or args.export_unique) and len(file_results) >= 1:
        if len(file_results) > 1:
            perform_global_isomorphism(file_results, verbose=args.verbose)

    # Optional export of unique representatives
    if args.export_unique and file_results:
        unique_circuits = []
        seen_signatures = set()
        for results in file_results.values():
            for r in results:
                if r["valid"]:
                    sig = r["signature_set"]
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        unique_circuits.append(r["circuit"])

        with open(args.export_unique, "w") as f:
            for c in unique_circuits:
                f.write(str(c) + "\n")

        print(f"\nExported {len(unique_circuits)} unique isomorphism class representatives to '{args.export_unique}'.")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
