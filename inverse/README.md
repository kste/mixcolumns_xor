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

The tables below summarize the circuit depth (critical path length in the XOR DAG) across all 4,884 valid 88-XOR inverse circuits in [`circuits_88.txt`](circuits_88.txt):

### Depth Summary Table

| Dataset | Circuits | XOR Gates | Min Depth | Mean Depth | Max Depth | Avg Output Depth | Max Fan-out |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`circuits_88.txt`** | 4884 | 88 | **20** | 23.25 | 34 | 13.72 – 21.81 | 3 – 5 |

*(Each of the 4,884 circuits in `circuits_88.txt` is a canonical representative of a distinct $\mathbb{Z}_4$ rotational orbit: 746 original orbits, 1,209 Direct $F \leftrightarrow C$ Bipartite Hypergraph Duality orbits, 90 additional Depth-21 and 355 additional Depth-22 Treewidth-2 Markov-Blanket Grafted orbits, and 594 Depth-20 plus 1,890 additional Depth-21 Dual-Order Associative Tree-Rebalanced orbits. Lines 747–1340 contain all 594 Depth-20 canonical $\mathbb{Z}_4$-orbit circuits.)*

### Circuit Depth Distribution (`circuits_88.txt`)

| Depth | `circuits_88.txt` | Unique Classes | Avg Output Depth |
| :---: | :---: | :---: | :---: |
| **20** | 594 | 594 | 13.72 – 14.09 |
| **21** | 1998 | 1998 | 13.94 – 14.44 |
| **22** | 464 | 464 | 14.25 – 15.56 |
| **23** | 400 | 400 | 14.56 – 16.75 |
| **24** | 532 | 532 | 14.94 – 18.34 |
| **25** | 43 | 43 | 15.25 – 18.47 |
| **26** | 34 | 34 | 15.88 – 19.62 |
| **27** | 157 | 157 | 15.91 – 20.34 |
| **28** | 162 | 162 | 16.22 – 16.41 |
| **33** | 194 | 194 | 21.16 – 21.56 |
| **34** | 306 | 306 | 21.69 – 21.81 |
| **Total** | **4884** | **4884** | **13.72 – 21.81** |

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
| **`circuits_88.txt`** | 4884 | 4884 | **4884** | 1 instance |

*(All 4,884 circuits are 100% pairwise non-isomorphic and belong to 4,884 distinct $\mathbb{Z}_4$ rotational orbits—no two circuits are cyclic byte rotations of each other.)*

---

## Breakthrough Context: Beating the Literature SOTA

For over fifteen years, the cryptographic hardware literature reported an unyielding gap between the XOR complexity of AES Forward MixColumns (88 XORs) and Inverse MixColumns (~101–102 XORs):

| Transformation | SOTA in Literature | Reference | **This Work** |
| :--- | :---: | :---: | :---: |
| **AES Forward MixColumns** | **88 XORs** | Boyar-Peralta / Jean et al. | 88 XORs (min depth 5) |
| **AES Inverse MixColumns** | 102 XORs | Maximov (2019), Tan & Peyrin (CHES/ToSC 2020) | **88 XORs (min depth 20)** |
| **AES Inverse MixColumns** | 101 XORs | Liu et al. (ToSC 2021) | **88 XORs (-13 XORs)** |

### Key Takeaway
AES Inverse MixColumns can be implemented in **exactly 88 XOR gates** with a critical path depth as low as **20** (average output depth **13.72** = $439/32$), closing the 13-XOR gap and matching the Forward MixColumns gate bound.

---

## Mathematical Techniques: Why 88 XORs at Depth 20 is Achievable

### 1. The "Density Illusion" & Jordan Equivalence over $\mathbb{F}_2$
The Forward MixColumns binary matrix $M_{\text{fwd}} \in \mathbb{F}_2^{32 \times 32}$ has a total Hamming weight of **184** (row weights in $\{5, 7\}$). In contrast, the Inverse MixColumns binary matrix $M_{\text{inv}} \in \mathbb{F}_2^{32 \times 32}$ has a total Hamming weight of **472** (row weights in $\{11, 13, 15, 17, 19\}$) — over $2.5\times$ denser.

Despite the weight disparity, $M_{\text{fwd}}$ and $M_{\text{inv}}$ are **isomorphic as linear operators**:
- Both satisfy $M^4 = I \pmod 2 \implies M_{\text{inv}} = M_{\text{fwd}}^3 = M_{\text{fwd}}^{-1}$.
- Both have the minimal polynomial $(x + 1)^4 \in \mathbb{F}_2[x]$ and identical nilpotent rank profiles $\text{rank}((M \oplus I)^k) = [24, 16, 8, 0]$, decomposing into **eight Jordan blocks of size 4 ($8 \times J_4(1)$)** over $\mathbb{F}_2$.

### 2. Low-Rank Difference and Row Collapses
1. **Low-Rank Difference Matrix**:
   $$M_{\text{inv}} = M_{\text{fwd}} \oplus E, \quad \text{rank}_{\mathbb{F}_2}(E) = 16.$$
   Let $u = c_0 \oplus c_2$, $v = c_1 \oplus c_3$, and $s = u \oplus v = c_0 \oplus c_1 \oplus c_2 \oplus c_3$. The correction terms are generated by $04 \cdot (02 \cdot s \oplus u)$ and $04 \cdot (02 \cdot s \oplus v)$.
2. **Row Collapses (16 Free Targets)**:
   The 4 output byte rows satisfy $\text{row}_1 = \text{row}_0 \oplus z$ and $\text{row}_3 = \text{row}_1 \oplus (j \oplus s)$, where $z = \text{xtime}^2(s) \oplus \text{xtime}(u) \oplus (c_0 \oplus c_1)$ and $j = u \oplus \text{xtime}(s)$. Once $\text{row}_0$ and the shared base are computed, 16 of the 32 targets cost only 16 XORs total.

### 3. Target-to-Target Recurrence & $F \leftrightarrow C$ Bipartite Hypergraph Inversion Duality
Because $M_{\text{fwd}} \cdot M_{\text{inv}} = I$, the 4 output bytes $T = (T_0, T_1, T_2, T_3)^T = M_{\text{inv}} F$ satisfy $M_{\text{fwd}} T = F$, which yields the exact bit-slice recurrence over $\mathbb{F}_2[x]/(x^8+x^4+x^3+x+1)$:
$$\text{xtime}(T_b \oplus T_{b+1}) = T_b \oplus q_b, \quad q_b = f_{b+1} \oplus f_{b+2} \oplus f_{b+3}.$$
Every 88-XOR Forward circuit ($F = M_{\text{fwd}} C$) defines a 120-wire set $W = C \cup F \cup I$ with 88 3-term linear relations (triangles) $u \oplus v \oplus w = 0$. Mapping every wire mask from the $C$-basis to the $F$-basis via $w \mapsto M_{\text{inv}} w$ swaps inputs and outputs ($F \mapsto \{2^0, \dots, 2^{31}\}$ and $C \mapsto T_{\text{inv}}$). Whenever the 88 triangles are **orientable (acyclic/peelable) starting from $F$**, the inverted hypergraph yields an exact 88-XOR `InvMixColumns` circuit. Across the 17,462 unique Forward MixColumns circuits, **1,227 circuits** (**1,209 distinct $\mathbb{Z}_4$ rotational orbits**) peel directly from $F$ at depths **21–27** (reducing max fan-out to **3**).

### 4. Two-Wave Treewidth-2 Markov-Blanket Slice-Module Grafting
In 99.87% of all 88-XOR circuits (69,256 of 69,348 $\mathbb{Z}_4$-closed wire sets), the 88 inverse gates decompose along pure-slice Markov blankets $P_k \subseteq \text{span}(C[k])$ into five conditionally independent slice modules:
$$\text{Mod}_{01}(P_7, P_1) \longleftrightarrow \text{Mod}_2(P_7, P_1, P_2) \longleftrightarrow \text{Mod}_{34}(P_7, P_2, P_4) \longleftrightarrow \text{Mod}_5(P_7, P_4, P_5) \longleftrightarrow \text{Mod}_{67}(P_7, P_5).$$
In the minimum-depth family (`Family (7, 5)` with $|P_7| = 4$), global peeling interleaves across **two causal waves**:
- **Wave 1 ($d = 1\dots 11$)**: $\text{Mod}_{67}$ unlocks the full slice-7 parity $c_{0123}[7]$ at $d=3$; $\text{Mod}_{34}$ unlocks two early slice-4 carries $\{c_{0123}[4], c_{02}[4]\}$ at $d=3, 5$; $\text{Mod}_5$ consumes those two carries to unlock all three pure slice-5 carries $P_5 = \{c_{02}[5], c_{13}[5], c_{01}[5]\}$ at $d=5\dots 6$; and $\text{Mod}_{67}$ uses $P_5$ to unlock the remaining slice-7 boundary $B_7 = C[7] \cup P_7$ at $d=8\dots 12$, while $\text{Mod}_{012}$ concurrently unlocks $P_2 = \{c_{23}[2], c_{13}[2], c_{01}[2]\}$ at $d=9\dots 11$.
- **Wave 2 ($d = 10\dots 20$)**: Once $B_7$ and $P_2$ are unlocked, $\text{Mod}_{012}$ completes $C[0..2]$ at $d=10\dots 16$, $\text{Mod}_{34}$ completes $C[3..4]$ and the late slice-4 carry $c_{03}[4]$ at $d=11\dots 16$, and $\text{Mod}_5$ completes $C[5]$ at $d=17\dots 20$.

Grafting locally peelable modules across all 69,348 $\mathbb{Z}_4$-closed forward wire sets yields **108 $\mathbb{Z}_4$ orbits** at Depth 21 (90 new beyond direct $F \leftrightarrow C$ duality) and **432 $\mathbb{Z}_4$ orbits** at Depth 22 (355 new beyond direct duality).

### 5. Dual-Order Associative Tree Re-balancing & Proof of the Depth-20 Barrier
In Forward synthesis ($C \to F$), 3-input XOR cones $w = (a \oplus b) \oplus c$ are balanced for arrival times $d_C(\cdot)$ from $C$. Under $F \leftrightarrow C$ inversion ($F \to C$), wire arrival times $d_F(\cdot)$ reverse: when a fanout-1 intermediate wire $u = a \oplus b$ feeding $w = u \oplus c$ has $d_F(b) > \max(d_F(a), d_F(c))$, applying the associative rotation
$$(a \oplus b) \oplus c \;\longmapsto\; (a \oplus c) \oplus b \quad (\text{replacing } u = a \oplus b \text{ with } u' = a \oplus c)$$
pre-combines the two early-arriving wires under $d_F(\cdot)$ and shaves **1 full critical-path layer** off $w$ and all downstream slices without changing the gate count (88 XORs):
- In $\text{Mod}_{34}$, rotating the fanout-1 intermediate $u = c_{23}[3] \oplus c_{23}[7]$ ($d=15$) against the depth-0 input $c_{23}[3] \oplus c_{013}[4] \oplus c_{23}[7]$ replaces $u$ with $u' = c_3[3] \oplus c_{013}[4]$ ($d=11$), dropping $c_{013}[4]$ from $d=16 \to 15$, $c_{03}[4]$ from $d=17 \to 16$, and all four slice-5 targets by 1 layer ($d=21 \to 20$).
- Pairs of the 108 Depth-21 Markov-blanket grafted $\mathbb{Z}_4$ orbits merge under this rotation into 54 connected components, each supporting 11 Depth-20 associative variants across $\text{Mod}_{01}$ and $\text{Mod}_{34}$, yielding **$54 \times 11 = 594$ distinct Depth-20 $\mathbb{Z}_4$ rotational orbits** (2,376 individual Depth-20 circuits; minimum average output depth **$13.7188 = 439/32$**) and **1,998 total Depth-21 $\mathbb{Z}_4$ orbits**.
- **Why Depth 20 is the Exact Minimum for this 10-Gate $\text{Mod}_5$ Architecture**: In $\text{Mod}_5$ (10 gates total: 3 cross-slice gates $M_5$, 3 pure-slice carries $P_5$, and 4 target gates $C[5]$), unlocking $P_5 = \{c_{02}[5], c_{13}[5], c_{01}[5]\}$ in Wave 1 ($d \le 6$) consumes all 6 non-target gates of $\text{Mod}_5$, leaving zero spare intermediate gates for Wave 2. Consequently, when $c_{03}[4]$ arrives at $d=16$ and unlocks $c_3[5] = (c_{03}[4] \oplus c_3[5]) \oplus c_{03}[4]$ at $d=17$, the remaining three targets of $C[5]$ must be unlocked along the path graph $c_3[5] \xrightarrow{c_{13}[5]} c_1[5] \xrightarrow{c_{01}[5]} c_0[5] \xrightarrow{c_{02}[5]} c_2[5]$ at layers $18, 19, 20$. Exhaustive 2-wire replacement search across all critical-path and $\text{Mod}_{34} \cup \text{Mod}_5$ intermediates confirms that 0 replacements reach Depth $\le 19$.

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
- **Circuit Depth:** Maximum critical path depth from inputs to any gate (20–34, mean 23.25).
- **Target Depth:** Min, mean, and max average depth across the 32 output wires (13.72–21.81, mean 15.53).
- **Max Wire Fan-out:** Maximum number of times an intermediate wire is reused (3–5).
- **Unique Isomorphism Classes:** Count of distinct algebraic signature sets across the file (4,884).

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
