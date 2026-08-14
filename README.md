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
| **`circuits_2.txt`** | 1042 | 88 | **6** | 8.79 | 12 | 3.84 – 5.38 | 3 – 5 |
| **Combined** | 1089 | 88 | **6** | 8.74 | 12 | 3.84 – 5.38 | 3 – 5 |
| **Unique Classes** | 302 | 88 | **6** | 8.76 | 12 | 3.84 – 5.38 | 3 – 5 |

### Circuit Depth Distribution

| Depth | `circuits_1.txt` | `circuits_2.txt` | Combined Total | Unique Classes |
| :---: | :---: | :---: | :---: | :---: |
| **6** | 5 | 10 | 15 | 9 |
| **7** | 17 | 70 | 87 | 30 |
| **8** | 17 | 68 | 85 | 41 |
| **9** | 6 | 884 | 890 | 216 |
| **10** | 2 | 6 | 8 | 3 |
| **11** | 0 | 2 | 2 | 2 |
| **12** | 0 | 2 | 2 | 1 |
| **Total** | **47** | **1042** | **1089** | **302** |

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
| **`circuits_2.txt`** | 1100 | 1042 | **288** | 474 instances |
| **Combined** | 1147 | 1089 | **302** | 475 instances |

*(33 isomorphism classes are shared between `circuits_1.txt` and `circuits_2.txt`)*

---

## Verification & Analysis Tool (`verify_circuits.py`)

The repository includes [`verify_circuits.py`](verify_circuits.py) to formally verify correctness, compute structural metrics, and group circuits by isomorphism:

### Usage

```bash
# Verify default files (circuits_1.txt and circuits_2.txt)
python3 verify_circuits.py

# Verify correctness + run Isomorphism Analysis (grouping by signature set)
python3 verify_circuits.py -i

# Verbose breakdown of each circuit and isomorphism group
python3 verify_circuits.py circuits_1.txt -v -i

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
- **`circuits_2.txt`**: 1100 SLP circuits for AES MixColumns (288 unique isomorphism classes among valid circuits).
- **`LICENSE`**: Repository license.
