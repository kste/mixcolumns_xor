# AES MixColumns XOR Circuits

This repository provides a collection of Straight-Line Program (SLP) circuits computing the **AES MixColumns** linear transformation using 2-input XOR gates.

---

## Circuit Format

Each file contains **one circuit per line**, formatted as a Python tuple of pairs:

```python
((u_0, v_0), (u_1, v_1), ..., (u_{k-1}, v_{k-1}))
```

### Wire Numbering & Gates

- **Input Wires (`0` to `31`):**  
  Represent the 32 input bits to AES MixColumns (4 state bytes $\times$ 8 bits each).
  - Byte 0: wires `0`–`7`
  - Byte 1: wires `8`–`15`
  - Byte 2: wires `16`–`23`
  - Byte 3: wires `24`–`31`

- **Intermediate & Output Gates (`32` to `32 + k - 1`):**  
  Gate $i$ (for $0 \le i < k$) is given by the pair $(u_i, v_i)$ and computes:
  $$\text{wire}[32 + i] = \text{wire}[u_i] \oplus \text{wire}[v_i]$$
  
- **Properties:**
  - **Causal:** Each gate only references inputs or previous gates ($0 \le u_i, v_i < 32 + i$).
  - **Canonical Order:** Each pair is sorted such that $u_i \le v_i$.
  - **Outputs:** Exactly 32 of the generated wires match the 32 target outputs of the AES MixColumns linear layer.

---

## Circuit Depth & Statistics

The tables below summarize the circuit depth (critical path length in the XOR DAG) across the valid 88-XOR circuits:

### Depth Summary Table

| Dataset | Circuits | XOR Gates | Min Depth | Mean Depth | Max Depth | Avg Output Depth | Max Fan-out |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`circuits_1.txt`** | 47 | 88 | **6** | 7.64 | 10 | 3.84 – 5.19 | 3 – 5 |
| **`circuits_2.txt`** | 1973 | 88 | **6** | 8.79 | 12 | 3.84 – 5.50 | 3 – 5 |
| **`circuits_3.txt`** | 16872 | 88 | **5** | 8.65 | 12 | 3.72 – 5.50 | 3 – 5 |
| **`circuits_depth5.txt`** | 46 | 88 | **5** | 5.00 | 5 | 3.75 – 4.22 | 5 – 5 |
| **Combined** | 18938 | 88 | **5** | 8.65 | 12 | 3.72 – 5.50 | 3 – 5 |
| **Unique Classes** | 17462 | 88 | **5** | 8.65 | 12 | 3.72 – 5.50 | 3 – 5 |

### Circuit Depth Distribution

| Depth | `circuits_1.txt` | `circuits_2.txt` | `circuits_3.txt` | `circuits_depth5.txt` | Combined Total | Unique Classes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **5** | 0 | 0 | 46 | 46 | 92 | 46 |
| **6** | 5 | 16 | 303 | 0 | 324 | 315 |
| **7** | 17 | 129 | 1352 | 0 | 1498 | 1399 |
| **8** | 17 | 132 | 3120 | 0 | 3269 | 3198 |
| **9** | 6 | 1675 | 11344 | 0 | 13025 | 11784 |
| **10** | 2 | 14 | 495 | 0 | 511 | 502 |
| **11** | 0 | 4 | 165 | 0 | 169 | 169 |
| **12** | 0 | 3 | 47 | 0 | 50 | 49 |
| **Total** | **47** | **1973** | **16872** | **46** | **18938** | **17462** |

---

## Circuit Isomorphism via Algebraic Signatures

Two XOR circuits are **isomorphic** if they represent the exact same underlying circuit, differing only by:
1. **Gate Commutativity:** Computing $a \oplus b$ is identical to $b \oplus a$.
2. **Gate Reordering (Scheduling):** Independent gates can be computed in different orders without changing the underlying circuit graph.

### Method: Algebraic Signature Extraction

Testing graph isomorphism directly is computationally heavy, but for pure XOR linear circuits we use an exact mathematical shortcut:

1. **Assign Basis Vectors:** Assign a unique 32-bit integer with a single bit set to each of the 32 raw inputs:
   $$\text{Input } 0 = 2^0 = \mathtt{0x00000001}, \quad \dots, \quad \text{Input } 31 = 2^{31} = \mathtt{0x80000000}$$
2. **Simulate the Circuit:** Evaluate the circuit over $\mathbb{F}_2^{32}$. Whenever a gate XORs two wires, XOR their 32-bit integers.
3. **Collect Signatures:** Each gate produces a 32-bit integer describing the exact linear combination of inputs computed at that node.
4. **Compare Signature Sets:** A circuit with $k$ gates produces a set of $k$ 32-bit integer signatures. Because sets are unordered, gate evaluation order does not matter:
   $$\text{Circuit } A \cong \text{Circuit } B \iff \text{SignatureSet}(A) = \text{SignatureSet}(B)$$

### Isomorphism Breakdown

| File | Total Lines | Valid MixColumns | Unique Isomorphism Classes | Largest Equivalence Class |
| :--- | :---: | :---: | :---: | :---: |
| **`circuits_1.txt`** | 47 | 47 | **47** | 1 instance |
| **`circuits_2.txt`** | 2219 | 1973 | **580** | 815 instances |
| **`circuits_3.txt`** | 16872 | 16872 | **16872** | 1 instance |
| **`circuits_depth5.txt`** | 46 | 46 | **46** | 1 instance |
| **Combined** | 19184 | 18938 | **17462** | 816 instances |

*(37 isomorphism classes are shared between `circuits_1.txt` and `circuits_2.txt`; `circuits_3.txt` contains 16,872 additional unique classes disjoint from `circuits_1.txt` and `circuits_2.txt`, with its first 46 entries extracted into `circuits_depth5.txt`.)*

---

## Optimality & Structural Analysis (The 88-XOR Barrier)

### 1. Minimum Depth (Depth 5)
Because the maximum Hamming weight among the 32 MixColumns target rows is 5, the information-theoretic depth floor is $\lceil \log_2 5 \rceil = 3$. Exact SAT verification over the complete $\mathbb{Z}_4$-closed signal pool proves that depth $\le 4$ is **unsatisfiable (UNSAT)** at 88 XORs, making the 46 **depth-5** circuits in `circuits_depth5.txt` depth-optimal.

### 2. Bit-Slice Decomposition & Slack Conservation Law
Under the AES reduction polynomial $P(x) = x^8 + x^4 + x^3 + x + 1$ (`0x11B`), the 8 bit-slices $B_0, \dots, B_7$ partition into 6 coupled synthesis blocks with exact isolated minimums:
$$H_G^* = 3, \quad H_{01}^* = 20, \quad H_2^* = 10, \quad H_{34}^* = 24, \quad H_5^* = 10, \quad H_{67}^* = 16 \quad \left(\sum H_i^* = 83\text{ XORs}\right).$$

Due to cyclic carry coupling from $B_7$ into slices $\{0, 1, 3, 4\}$, no circuit can simultaneously achieve the isolated minimum across all 6 blocks. Defining block slack $\Delta(H_i) = H_i(C) - H_i^* \ge 0$, every known 88-XOR circuit satisfies the exact conservation law:
$$\Delta(H_G) + \Delta(H_{01}) + \Delta(H_2) + \Delta(H_{34}) + \Delta(H_5) + \Delta(H_{67}) \equiv \mathbf{5} \quad (\text{Total} = 83 + 5 = 88\text{ XORs}).$$

- **16-Gate Quotient Core ($Q_{34} \cong Q_{01}$):** While the 8-target quotient projection on $B_3 \cup B_7$ (and $B_0 \cup B_7$) can be synthesized in **16 XOR gates** (8 intermediates + 8 targets) via an odd-parity excursion wire in $B_7$, interleaving the adjacent slice inputs ($B_2, B_4$) and exported carries enforces $H_{01} \ge 20$ and $H_{34} \ge 24$.
- **Carry Coupling Duality:** Achieving $H_{67} = 16$ ($3_{\text{pure } B_6} + 7_{(B_5, B_6)} + 6_{(B_6, B_7)}$) requires the full slice parity carry $\Sigma_7$, which forces $\Delta(H_G + H_{01} + H_{34}) \ge +2$ upstream. Conversely, sparse carries keep $H_G=3, H_{01}=20, H_{34}=24$ minimal, but force $H_{67} \ge 17$ and $H_2 \ge 14$.

### 3. Exhaustive SAT & Meet-in-the-Middle Refutations

| Search / Proof Frontier | Scope | Solver / Method | Result |
| :--- | :--- | :--- | :--- |
| **Double-Optimal Frontier ($H_{01}=20, H_{34}=24$)** | All 73 double-optimal circuits (partitioned into the 4 exact Home 2 equivalence classes) | CaDiCaL exact coordinate SAT (42.6 CPU hours, $>550\text{M}$ conflicts) | **100% UNSAT** for $< 88$ XORs |
| **Terminal Cones & Convex Sub-DAGs** | 24.5M terminal cones ($s \le 7$) + 5.4M sub-DAGs ($\sigma \le 4$) + 103,616 quotient sub-DAGs | Bidirectional MITM + CaDiCaL | **100% UNSAT** for $k \to k-1$ |
| **Global Pool Subset-SAT & MaxSAT** | 1,607-signal $\mathbb{Z}_4$-closed pool across all classes | CaDiCaL Cardinality SAT | **UNSAT** at $\le 87$ gates (86 gates reach at most 31/32 targets; 32nd target has distance $\ge 2$) |
| **Treewidth-3 Tropical DP** | All $562 \times 562$ inter-slice carry states | Exact branch-and-bound + tropical matrix power | Uncoupled ring floor $\ge 80$ + coupling $\ge 8 \implies \mathbf{88\text{ XORs}}$ |

---

## Verification & Analysis Tool (`verify_circuits.py`)

The repository includes [`verify_circuits.py`](verify_circuits.py) to formally verify correctness, compute structural metrics, and group circuits by isomorphism:

### Usage

```bash
# Verify default files (circuits_1.txt, circuits_2.txt, circuits_3.txt, circuits_depth5.txt)
python3 verify_circuits.py

# Verify correctness + run Isomorphism Analysis (grouping by signature set)
python3 verify_circuits.py -i

# Verify only the depth-5 circuits
python3 verify_circuits.py circuits_depth5.txt -v -i

# Export unique isomorphism representatives to a deduplicated file
python3 verify_circuits.py -u unique_circuits.txt

# Verify a single circuit string and display output wire mapping
python3 verify_circuits.py -c "((15, 7), (0, 32), ...)" -m
```

### Metrics Reported

- **XOR Gate Count:** Total gates in the circuit.
- **Circuit Depth:** Maximum critical path depth from inputs to any gate.
- **Output Depth:** Min, max, and average depth across the 32 output wires.
- **Max Wire Fan-out:** Maximum number of times an intermediate wire is reused.
- **Isomorphism Equivalence Classes:** Groups of circuits that compute the exact same intermediate mathematical states.

---

## Programmatic Evaluation Example (Python)

```python
import ast
from verify_circuits import verify_circuit

# Read and evaluate the first circuit
with open("circuits_1.txt") as f:
    circuit = ast.literal_eval(f.readline().strip())

# Verify and extract the 32 output wire indices (0..31)
result = verify_circuit(circuit)
print(f"Valid: {result['valid']}, XOR Gates: {result['xor_count']}, Depth: {result['circuit_depth']}")
output_wires = [result['output_wires'][i] for i in range(32)]
print(f"MixColumns output wires: {output_wires}")
```

---

## Repository Files

- **`verify_circuits.py`**: Verification, metric calculation, isomorphism grouping, and deduplication tool.
- **`circuits_1.txt`**: 47 88-XOR circuits for AES MixColumns (47 pairwise distinct isomorphism classes).
- **`circuits_2.txt`**: 2219 SLP circuits for AES MixColumns (580 unique isomorphism classes among valid circuits).
- **`circuits_3.txt`**: 16,872 additional pairwise non-isomorphic 88-XOR circuits (depths 5–12), expanding the repository total to 17,462 unique isomorphism classes.
- **`circuits_depth5.txt`**: The 46 optimal depth-5 88-XOR circuits (pairwise non-isomorphic).
- **`LICENSE`**: Repository license.
