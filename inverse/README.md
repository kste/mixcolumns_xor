# AES Inverse MixColumns XOR Circuits

This directory provides a collection of Straight-Line Program (SLP) circuits computing the **AES Inverse MixColumns** linear transformation over $\text{GF}(2^8)$ modulo $x^8 + x^4 + x^3 + x + 1$ using 2-input XOR gates.

Every circuit in [`circuits_88.txt`](circuits_88.txt) is **pairwise non-isomorphic** (each computes a strictly unique set of 88 linear combinations / algebraic signatures) and belongs to a **distinct $\mathbb{Z}_4$ rotational orbit**.

---

## Circuit Format

[`circuits_88.txt`](circuits_88.txt) contains **one circuit per line**, formatted as a Python tuple of pairs:

```python
((u_0, v_0), (u_1, v_1), ..., (u_{k-1}, v_{k-1}))
```

### Wire Numbering & Gates

- **Input Wires (`0` to `31`):**  
  Represent the 32 input bits to AES Inverse MixColumns (4 state bytes $\times$ 8 bits each).
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
  - **Outputs:** Exactly 32 of the generated wires match the 32 target outputs of the AES Inverse MixColumns linear transformation.

---

## Circuit Depth & Statistics

The tables below summarize the circuit depth (critical path length in the XOR DAG) across all 12,174 valid 88-XOR inverse circuits in [`circuits_88.txt`](circuits_88.txt):

### Depth Summary Table

| Dataset | Circuits | XOR Gates | Min Depth | Mean Depth | Max Depth | Avg Output Depth | Max Fan-out |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`circuits_88.txt`** | 12174 | 88 | **18** | 22.78 | 34 | 12.56 – 21.81 | 3 – 5 |

*(Each of the 4,884 circuits in `circuits_88.txt` is a canonical representative of a distinct $\mathbb{Z}_4$ rotational orbit: 746 original orbits, 1,209 Direct $F \leftrightarrow C$ Bipartite Hypergraph Duality orbits, 90 additional Depth-21 and 355 additional Depth-22 Treewidth-2 Markov-Blanket Grafted orbits, and 594 Depth-20 plus 1,890 additional Depth-21 Dual-Order Associative Tree-Rebalanced orbits. Lines 747–1340 contain all 594 Depth-20 canonical $\mathbb{Z}_4$-orbit circuits.)*

### Circuit Depth Distribution (`circuits_88.txt`)

| Depth | `circuits_88.txt` | Unique Classes | Avg Output Depth |
| :---: | :---: | :---: | :---: |
| **18** | 513 | 513 | 12.56 – 13.31 |
| **19** | 1674 | 1674 | 12.88 – 13.81 |
| **20** | 594 | 594 | 13.72 – 14.09 |
| **21** | 1998 | 1998 | 13.94 – 14.44 |
| **22** | 707 | 707 | 14.25 – 15.62 |
| **23** | 1453 | 1453 | 14.56 – 16.75 |
| **24** | 2557 | 2557 | 14.94 – 18.34 |
| **25** | 1825 | 1825 | 15.25 – 18.47 |
| **26** | 34 | 34 | 15.88 – 19.62 |
| **27** | 157 | 157 | 15.91 – 20.34 |
| **28** | 162 | 162 | 16.22 – 16.41 |
| **33** | 194 | 194 | 21.16 – 21.56 |
| **34** | 306 | 306 | 21.69 – 21.81 |
| **Total** | **12174** | **12174** | **12.56 – 21.81** |

---

## Circuit Isomorphism via Algebraic Signatures

Two XOR circuits are **isomorphic** if they represent the exact same underlying circuit, differing only by:
1. **Gate Commutativity:** Computing $a \oplus b$ is identical to $b \oplus a$.
2. **Gate Reordering (Scheduling):** Independent gates can be computed in different orders without changing the underlying circuit graph.

### Method: Algebraic Signature Extraction

Testing graph isomorphism directly is computationally heavy, but for pure XOR linear circuits we use an exact mathematical shortcut:
1. **Assign Basis Vectors:** Assign a unique 32-bit integer with a single bit set to each of the 32 raw inputs ($2^0 \dots 2^{31}$).
2. **Simulate the Circuit:** Evaluate the circuit over $\mathbb{F}_2^{32}$. Whenever a gate XORs two wires, XOR their 32-bit integers.
3. **Collect Signatures:** Each gate produces a 32-bit integer describing the exact linear combination of inputs computed at that node.
4. **Compare Signature Sets:** A circuit with $k$ gates produces a set of $k$ 32-bit integer signatures:
   $$\text{Circuit } A \cong \text{Circuit } B \iff \text{SignatureSet}(A) = \text{SignatureSet}(B)$$

### Isomorphism Breakdown

| File | Total Lines | Valid InvMixColumns | Unique Isomorphism Classes | Largest Equivalence Class |
| :--- | :---: | :---: | :---: | :---: |
| **`circuits_88.txt`** | 12174 | 12174 | **12174** | 1 instance |

*(All 12,174 circuits are 100% pairwise non-isomorphic and belong to 12,174 distinct $\mathbb{Z}_4$ rotational orbits—no two circuits are cyclic byte rotations of each other.)*

---

## Verification & Analysis Tool (`verify_inverse.py`)

The directory includes [`verify_inverse.py`](verify_inverse.py) to formally verify correctness, compute structural metrics, and test against FIPS-197 standard test vectors:

### Usage

```bash
# Verify correctness and display summary statistics
python3 verify_inverse.py circuits_88.txt

# Run correctness verification + Algebraic Signature Isomorphism Analysis
python3 verify_inverse.py circuits_88.txt -i

# Run exhaustive verification against 88 concrete FIPS-197 test vectors per circuit
python3 verify_inverse.py circuits_88.txt -i -t
```

### Metrics Reported

- **XOR Gate Count:** Total gates in the circuit (88).
- **Circuit Depth:** Maximum critical path depth from inputs to any gate (18–34, mean 22.78).
- **Target Depth:** Min, mean, and max average depth across the 32 output wires (12.56–21.81, mean 15.21).
- **Max Wire Fan-out:** Maximum number of times an intermediate wire is reused (3–5).
- **Unique Isomorphism Classes:** Count of distinct algebraic signature sets across the file (12,174).

---

## Programmatic Evaluation Example (Python)

```python
import ast
from verify_inverse import verify_circuit, get_aes_inv_mixcolumns_targets

targets = get_aes_inv_mixcolumns_targets()

# Read and evaluate the first circuit
with open("circuits_88.txt") as f:
    circuit = ast.literal_eval(f.readline().strip())

# Verify and extract metrics
result = verify_circuit(circuit, targets)
print(f"Valid: {result['valid']}, XOR Gates: {result['gates']}, Depth: {result['max_target_depth']}")
print(f"Average Target Depth: {result['avg_target_depth']:.2f}, Max Fanout: {result['max_fanout']}")
```
