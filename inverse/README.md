# AES Inverse MixColumns XOR Circuits

This directory provides a collection of Straight-Line Program (SLP) circuits computing the **AES Inverse MixColumns** linear transformation over $\text{GF}(2^8)$ modulo $x^8 + x^4 + x^3 + x + 1$ using 2-input XOR gates.

Every circuit in this directory is **pairwise non-isomorphic** (each computes a strictly unique set of 88 linear combinations / algebraic signatures).

---

## Circuit Format

Each file contains **one circuit per line**, formatted as a Python tuple of pairs:

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

The tables below summarize the circuit depth (critical path length in the XOR DAG) across the valid 88-XOR inverse circuits:

### Depth Summary Table

| Dataset | Circuits | XOR Gates | Min Depth | Mean Depth | Max Depth | Avg Output Depth | Max Fan-out |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`circuits_88.txt`** | 500 | 88 | **33** | 33.61 | 34 | 21.16 – 21.81 | 4 |

### Circuit Depth Distribution

| Depth | `circuits_88.txt` | Unique Classes |
| :---: | :---: | :---: |
| **33** | 194 | 194 |
| **34** | 306 | 306 |
| **Total** | **500** | **500** |

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
| **`circuits_88.txt`** | 500 | 500 | **500** | 1 instance |

*(All 500 circuits are 100% pairwise non-isomorphic and belong to 500 distinct $\mathbb{Z}_4$ rotational orbits—no two circuits are cyclic byte rotations of each other.)*

---

## Breakthrough Context: Beating the Literature SOTA

For over fifteen years, the cryptographic hardware literature reported an unyielding gap between the XOR complexity of AES Forward MixColumns (88 XORs) and Inverse MixColumns (~101–102 XORs):

| Transformation | SOTA in Literature | Reference | **This Work** |
| :--- | :---: | :--- | :---: |
| **AES Forward MixColumns** | **88 XORs** | Boyar-Peralta / Jean et al. | 88 XORs |
| **AES Inverse MixColumns** | 102 XORs | Maximov (2019), Tan & Peyrin (CHES/ToSC 2020) | **88 XORs** |
| **AES Inverse MixColumns** | 101 XORs | Liu et al. (ToSC 2021) | **88 XORs (-13 XORs)** |

### Key Takeaway
AES Inverse MixColumns can be implemented in **exactly 88 XOR gates**, closing the 13-XOR gap and matching the Forward MixColumns bound.

---

## Mathematical Technique: Why 88 XORs is Achievable

### 1. The "Density Illusion"
The Forward MixColumns binary matrix $M_{\text{fwd}} \in \mathbb{F}_2^{32 \times 32}$ has a total Hamming weight of **184** (row weights in $\{5, 7\}$). In contrast, the Inverse MixColumns binary matrix $M_{\text{inv}} \in \mathbb{F}_2^{32 \times 32}$ has a total Hamming weight of **472** (row weights in $\{11, 13, 15, 17, 19\}$) — over $2.5\times$ denser. 

Historically, this massive density disparity led researchers to assume that Inverse MixColumns inherently requires more gates.

### 2. Algebraic Equivalence (Jordan Structure over $\mathbb{F}_2$)
Despite the weight disparity, $M_{\text{fwd}}$ and $M_{\text{inv}}$ are **isomorphic as linear operators**:
- Both satisfy $M^4 = I \pmod 2 \implies M_{\text{inv}} = M_{\text{fwd}}^3$.
- Both have the minimal polynomial $(x + 1)^4 \in \mathbb{F}_2[x]$.
- Computing the ranks of $(M \oplus I)^k$ over $\mathbb{F}_2$:
  $$\text{rank}((M_{\text{fwd}} \oplus I)^k) = [24, 16, 8, 0] \quad \text{and} \quad \text{rank}((M_{\text{inv}} \oplus I)^k) = [24, 16, 8, 0]$$
- Both decompose into **identically eight Jordan blocks of size 4 ($8 \times J_4(1)$)** over $\mathbb{F}_2$. They are similar matrices in $\text{GL}(32, \mathbb{F}_2)$.

### 3. The Algebraic Core: Low-Rank Difference and Row Collapses
The technique to achieve 88 XORs exploits two structural properties:

1. **Low-Rank Difference Matrix**:
   $$M_{\text{inv}} = M_{\text{fwd}} \oplus E$$
   where:
   $$E = \begin{pmatrix} 0\text{C} & 08 & 0\text{C} & 08 \\ 08 & 0\text{C} & 08 & 0\text{C} \\ 0\text{C} & 08 & 0\text{C} & 08 \\ 08 & 0\text{C} & 08 & 0\text{C} \end{pmatrix}$$
   $E$ has rank only **16** over $\mathbb{F}_2$. Let $u = c_0 \oplus c_2$, $v = c_1 \oplus c_3$, and $s = u \oplus v = c_0 \oplus c_1 \oplus c_2 \oplus c_3$. The correction terms are generated by $04 \cdot (02 \cdot s \oplus u)$ and $04 \cdot (02 \cdot s \oplus v)$. Crucially, $02 \cdot s = \text{xtime}(s)$ is *already* the foundational intermediate wire in 88-XOR forward circuits.

2. **Row Collapses (16 Free Targets)**:
   The 4 output byte rows satisfy:
   $$\text{row}_1 = \text{row}_0 \oplus z$$
   $$\text{row}_3 = \text{row}_1 \oplus (j \oplus s)$$
   where $z = \text{xtime}^2(s) \oplus \text{xtime}(u) \oplus (c_0 \oplus c_1)$ and $j = u \oplus \text{xtime}(s)$.
   
   Once $\text{row}_0$ is computed, $\text{row}_1$ costs only **8 XORs** (1 XOR per bit with $z$), and $\text{row}_3$ costs only **8 XORs** (1 XOR per bit with $j \oplus s$). Thus, **16 of the 32 targets cost only 16 XORs total**, leaving 72 XORs to synthesize the remaining 16 targets and the shared base $s, u, \text{xtime}(s), \text{xtime}^2(s)$.

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
- **Circuit Depth:** Maximum critical path depth from inputs to any gate (33–34).
- **Target Depth:** Min, mean, and max depth across the 32 output wires (mean 21.67).
- **Max Wire Fan-out:** Maximum number of times an intermediate wire is reused (4).
- **Unique Isomorphism Classes:** Count of distinct algebraic signature sets across the file.

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
