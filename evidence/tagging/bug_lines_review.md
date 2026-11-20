# Bug-line tagging: first pass for review

> **Authorship.** This file was written by Claude Code (AI) as output for the author's review, not by the author. "I" and "my" mean Claude; "you" means the author. The author reviewed it, asked for the rechecks and decisions recorded here, and adopted the tags into `data/samples/*/meta.json` (commit fa74889). All 25 proposed `bug_lines` were adopted unchanged. Apart from this note and the file paths, the text is kept as written.
>
> **Files here.** `runone.py` runs a sample's dataset tests against any Java file, giving the "tests before → after" counts. `fixes/<id>/` holds the fixed translation used for each "after" count (21 samples; the 4 with no translation bug have none). They are modified copies of the GPT-4 translations in [`data/samples/`](../../data/samples)(Pan et al., CC BY 4.0; see [`data/NOTICE`](../../data/notice)), changed only to fix the tagged bug. Each fix changes the tagged lines plus, in some samples, lines needed for it to compile; ABC150_C is the exception, fixed at L23 as its notes explain. The other scripts and logs mentioned below were run outside this repository and are not part of the submission.

Claude's first pass on the 25 buggy samples. **Nothing has been written to `meta.json` yet.** Confirm or correct each tag.

## How each tag was checked

1. Each translation was compiled (OpenJDK) and run on all its tests, with a 5 s timeout. All 25 fail at least one test.
2. The tagged Java lines were then changed in a scratch copy (the minimal fix) and the tests rerun. **A tag counts as verified only if that fix makes the failing tests pass.** Claude reran every fix independently.
3. Where a fix did not help, the Python source was run on the same tests and its output compared with the Java's.

## Summary

| Sample | Pan | Source lines | Java lines | Tests before → after | Agrees with Pan? |
|---|---|---|---|---|---|
| `avatar-atcoder_ABC123_C` | C2 | [9, 10, 11] | [7, 8, 10, 14] | 2/20 → 20/20 | yes |
| `avatar-atcoder_ABC126_D` | C2 | - | - | 0/1 → 0/1 | **no** |
| `avatar-atcoder_ABC143_D` | B6 | [9, 10, 4] | [20, 24, 15] | 3/15 → 15/15 | yes |
| `avatar-atcoder_ABC150_C` | B6 | [3] | [32, 34] | 4/13 → 13/13 | yes |
| `avatar-atcoder_ABC158_B` | C1 | [8] | [7, 8, 9, 10] | 4/29 → 29/29 | yes |
| `avatar-atcoder_ABC167_D` | C1 | [2] | [7] | 24/57 → 57/57 | yes |
| `avatar-atcoder_ABC178_B` | C1 | [13, 14] | [13] | 3/35 → 35/35 | yes |
| `avatar-atcoder_AGC010_B` | C1 | [2, 5] | [18, 21] | 25/30 → 30/30 | yes |
| `avatar-atcoder_AGC019_A` | C1 | [27, 31, 33] | [11] | 4/19 → 19/19 | yes |
| `avatar-atcoder_AGC046_B` | C1 | [7] | [19] | 12/17 → 17/17 | **no** |
| `avatar-atcoder_ARC086_B` | B6 | - | - | 0/1 → 0/1 | **no** |
| `avatar-codeforces_306_A` | C3 | - | - | 8/20 → 8/20 | **no** |
| `avatar-codeforces_30_A` | C2 | [6] | [3, 4, 5] | 0/68 → 50/68 | yes |
| `avatar-codeforces_387_A` | A4/A1 | [6] | [18] | 30/47 → 47/47 | yes |
| `avatar-codeforces_400_A` | B6 | [35] | [33] | 0/3 → 3/3 | yes |
| `avatar-codeforces_459_A` | C3 | - | - | 34/74 → 34/74 | **no** |
| `avatar-codeforces_579_A` | C2 | [4] | [10] | 35/36 → 36/36 | **no** |
| `avatar-codeforces_621_A` | C1 | [9] | [24] | 27/28 → 28/28 | yes |
| `avatar-codeforces_637_A` | B6 | [11, 13] | [22, 24] | 17/28 → 28/28 | yes |
| `avatar-codeforces_651_A` | C2 | [3, 4, 5, 6, 2] | [10, 13, 16, 17, 19, 8] | 0/39 → 39/39 | yes |
| `avatar-codeforces_665_A` | C1 | [3] | [12, 13] | 0/31 → 31/31 | **no** |
| `codenet-s259116349` | C2 | [12, 13] | [15, 16] | 0/1 → 1/1 | **no** |
| `codenet-s813548165` | B6 | [2] | [7] | 0/1 → 1/1 | yes |
| `codenet-s826716211` | C2 | [3, 4] | [47] | 0/1 → 1/1 | yes |
| `codenet-s875904659` | C3 | [8, 20] | [17, 35] | 0/1 → 1/1 | yes |

**21 samples have a verified translation bug. 4 have none**: the Java prints exactly what the Python prints on every test, and both fail only because the problem accepts more than one correct answer while the test expects one exact output.

## Claude's own recheck of the disputed and no-bug samples

You asked me to verify these myself, not just trust the agents. Here is what I did and found.

**Correction to my own earlier check.** My first Python-vs-Java comparison for 306_A, ARC086_B and 459_A used the shell `timeout` command, which macOS does not have. Both sides were the same "command not found" error, so that comparison proved nothing. Everything below was redone without it.

### The 4 no-bug samples: confirmed, no translation bug that the tests could reveal
| Sample | Java output is a *valid answer* (checker built from the problem rules) | Java = Python on 300 random valid inputs | Reading source vs translation |
|---|---|---|---|
| ABC126_D | 1/1 | 300/300 | Faithful. Java's `int distance` can overflow, but parity survives (checked on a 2,000-node chain with weights 1e9). On a 100,000-node chain **both** crash (Python RecursionError, Java StackOverflowError): a weakness of the source that the translation keeps, not a translation bug. |
| ARC086_B | 1/1 | 300/300 | Faithful. |
| 306_A | 20/20 | 300/300 | Faithful, including the trailing space. |
| 459_A | 74/74 | 300/300 | **Latent difference:** line 9 uses `split(" ")` where Python uses `split()`. A double space, a leading space or a tab crashes the Java and not the Python. Outside the problem's input format, so no test triggers it. |

The checkers accept every official expected output and reject 6 deliberately wrong answers, so they are not lenient.

### The 4 Pan-category disputes: confirmed with my own fixes; Pan's implied fix does not work
| Sample | Pan | Pan-implied fix | My fix | Verified category |
|---|---|---|---|---|
| AGC046_B | C1 | `long[][]`: 12/17 (no change) | normalise `% m`: 17/17 | A4, operator (`%` sign) |
| 579_A | C2 | `nextLong`: 35/36 (still infinite loop) | `Integer.bitCount(n) != 1` on line 10 only: 36/36 | B6, `log2` replaced by `log/log` |
| 665_A | C1 | `long` everywhere: 0/31 | `:` as a delimiter: 31/31 | C2, input parsing |
| s259116349 | C2 | n/a (only reads one int) | loop over a copy of `i`: 1/1 | Loop-variable semantics (no exact Pan code; closest A1/E) |

### Latent bugs (compile, give output, no test catches them)
| Sample | Bug | Confirmed how |
|---|---|---|
| AGC010_B | Java `%` can be negative (lines 24, 26), so remainders cancel in the sum | **Still present after the verified fix:** Java says YES where Python says NO on 60/595 random valid inputs, e.g. `4 / 2 8 11 9` |
| codeforces_637_A | `Integer == Integer` on line 22 | Correct up to a tie of 127; **wrong from 128** (10/15 random ties), Java's Integer cache boundary |
| codenet-s875904659 | `Arrays.equals` on objects without `equals()` (line 53) | Input `3 / H1 C2 S3`: Java prints "Not stable", Python prints "Stable" |
| codeforces_459_A | `split(" ")` vs `split()` (line 9) | Crashes on a double space, leading space or tab |

**Decision for you:** these latent bugs matter for scoring. If the detector flags a latent-bug line, that is not a false alarm. I suggest recording them in a separate `latent` field in `meta.json` (same shape as `bug_lines`), so the evaluation can score them separately instead of counting them as false positives.

## Decisions for you

1. **The 4 no-bug samples** (`avatar-atcoder_ABC126_D`, `avatar-atcoder_ARC086_B`, `avatar-codeforces_306_A`, `avatar-codeforces_459_A`). Options:
   - (a) Keep them, with empty `bug_lines` and a note saying "no translation bug: test expects one of several valid answers". Exclude them from precision and recall, and report the finding. *(Recommended: it is evidence that Pan's file-level labels need re-checking.)*
   - (b) Swap in 4 replacements from the remaining 43 buggy candidates.
2. **Bugs no test exposes:** `s875904659` Java line 53 (`Arrays.equals` without `equals()`), `codeforces_637_A` line 22 (`Integer == Integer` above 127), `AGC010_B` (negative `%`). Recommended: tag only bugs a test exposes, and mention the others in `notes`, so every tag has a verified fix behind it.
3. **Category disagreements with Pan:** `AGC046_B` (C1 → really modulo sign), `codeforces_579_A` (C2 → `log2` replaced by `log/log`, B6), `codeforces_665_A` (C1 → parsing `hh:mm`, C2), `s259116349` (C2 → loop variable changed inside the loop), plus `ABC123_C`/`ABC143_D`/`651_A`, which each have an extra bug Pan did not record. Recommended: leave `pan_labels` untouched and record the verified category in `notes`.

## Per sample

### `avatar-atcoder_ABC123_C`: Pan C2, confidence high

Python reads N and the five capacities as unbounded ints (up to 1e15) and prints ceil(N/min(A))+4. Java reads them with nextInt() into int/int[] and casts the result to int, so inputs above 2^31-1 throw InputMismatchException and large quotients overflow.

Source (`source.py`):
```
  9 | N = int ( input ( ) )
 10 | A = [ int ( input ( ) ) for i in range ( 5 ) ]
 11 | print ( math.ceil ( N / min ( A ) ) + 4 )
```
Translation (`translation.java`):
```
  7 |         int N = scanner.nextInt();
  8 |         int[] A = new int[5];
 10 |             A[i] = scanner.nextInt();
 14 |         System.out.println((int) Math.ceil((double) N / minA) + 4);
```
**Fix used to verify:** L7 `int N = scanner.nextInt();` -> `long N = scanner.nextLong();`; L8 `int[] A` -> `long[] A`; L10 nextInt -> nextLong; L14 `(int) Math.ceil` -> `(long) Math.ceil` (L13 int/getAsInt -> long/getAsLong needed to compile)  
**Tests:** 2/20 → 20/20

*Notes:* Staged: N-only fix 3/20; +L14 cast 13/20; +A array reads 20/20. All three decisions needed. L13 changed only as a consequence of L8. The L14 int cast is arguably C1 rather than C2.

- [x] Confirmed by me

### `avatar-atcoder_ABC126_D`: Pan C2, confidence high

The Java faithfully reproduces the Python: both print 1 1 0 on the single test. The test expects 0 0 1, which is the other valid 2-colouring of a problem with many correct answers, so the failure is not caused by the translation.

**No translation bug.** Tests: 0/1.

*Notes:* Ran source.py on atcoder_ABC126_D_0.in: output 1\n1\n0, same as Java. The test oracle checks one exact answer. Pan's C2 label is not supported by this evidence. Possible latent issues not exercised: int distance (parity is still correct under overflow) and deep recursion for n=1e5 (harness uses -Xss64m). Recommend excluding or marking as an oracle problem.

- [x] Confirmed by me

### `avatar-atcoder_ABC143_D`: Pan B6, confidence high

Python uses bisect_left(l, a+b) and bisect_right(l, |a-b|) on a sorted list with many duplicates. Java replaced both with Arrays.binarySearch, which returns an arbitrary matching index, not the leftmost or rightmost insertion point, so the counts are wrong. Separately, `int ans` overflows when the triangle count times 3 exceeds 2^31-1 (test 5: 1331334000*3).

Source (`source.py`):
```
  4 | ans = 0
  9 |         right = bisect_left ( l , a + b )
 10 |         left = bisect_right ( l , max ( a - b , b - a ) )
```
Translation (`translation.java`):
```
 15 |         int ans = 0;
 20 |                 int right = Arrays.binarySearch(l, a + b);
 24 |                 int left = Arrays.binarySearch(l, Math.max(a - b, b - a));
```
**Fix used to verify:** L20 `Arrays.binarySearch(l, a + b)` (+ L21-23 negative handling) -> lowerBound(l, a+b); L24 `Arrays.binarySearch(l, max(...))` (+ L25-27) -> upperBound(l, max(...)); L15 `int ans = 0;` -> `long ans = 0;`  
**Tests:** 3/15 → 15/15

*Notes:* Second bug (C1, not in Pan's label): int ans overflow at L15, which alone causes test 5 to fail after the bisect fix (14/15 -> 15/15). Both binarySearch lines are needed: with long ans, fixing only right gives 4/15 and fixing only left gives 6/15. The negative-index conversions on L21-23 and L25-27 belong to the same API replacement.

- [x] Confirmed by me

### `avatar-atcoder_ABC150_C`: Pan B6, confidence high

Python's itertools.permutations yields permutations in lexicographic order, so the list index is the lexicographic rank. Java replaced it with a swap-based recursive generator, whose output order is not lexicographic for n>=3, so the indices and their difference are wrong.

Source (`source.py`):
```
  3 | orig = list ( itertools.permutations ( list ( range ( 1 , n + 1 ) ) ) )
```
Translation (`translation.java`):
```
 32 |                 swap(arr, pos, i);
 34 |                 swap(arr, pos, i);
```
**Fix used to verify:** L23 `permutation(array, 0, permutations);` -> `permutation(array, 0, permutations); permutations.sort(Arrays::compare);` (restores lexicographic order)  
**Tests:** 4/13 → 13/13

*Notes:* The wrong decision is the swap/backtrack algorithm (L32 swap, L33 recurse, L34 swap-back, in permutation() L27-37). The verifying fix was applied at L23 by sorting the generated list instead of rewriting the generator. If a single line is preferred, L23 (the call that replaces itertools.permutations) is the alternative.

- [x] Confirmed by me

### `avatar-atcoder_ABC158_B`: Pan C1, confidence high

Python reads N, A, B as unbounded ints (up to about 1e18). Java declares them as int and reads them with nextInt(), so large values throw InputMismatchException (and rep*A etc. would overflow).

Source (`source.py`):
```
  8 |     N , A , B = MI ( )
```
Translation (`translation.java`):
```
  7 |         int N, A, B, mod = 1000000007, ans = 0, rep, res;
  8 |         N = sc.nextInt();
  9 |         A = sc.nextInt();
 10 |         B = sc.nextInt();
```
**Fix used to verify:** L7 `int N, A, B, ... ;` -> `long N, A, B, ... ;`; L8-10 `sc.nextInt()` -> `sc.nextLong()`  
**Tests:** 4/29 → 29/29

*Notes:* The type decision is at L7 and the reads at L8-10 must change with it. A minimal tag could be [7] plus the reads. The crash is technically input parsing (nextInt), but the root cause is the int type, which is consistent with C1.

- [x] Confirmed by me

### `avatar-atcoder_ABC167_D`: Pan C1, confidence high

Python reads K as an arbitrary-precision int (up to ~1e18); Java reads it with sc.nextInt() into an int, so Scanner throws InputMismatchException on large K.

Source (`source.py`):
```
  2 | N , K = map ( int , input ( ).split ( ) )
```
Translation (`translation.java`):
```
  7 |         int K = sc.nextInt();
```
**Fix used to verify:** `int K = sc.nextInt();` → `long K = sc.nextLong();` (plus required (int) casts on the index uses at lines 35, 39, 42 so it compiles)  
**Tests:** 24/57 → 57/57

*Notes:* Stack trace points directly to line 7. Casts at 35/39/42 are compile-only consequences, not separate bugs.

- [x] Confirmed by me

### `avatar-atcoder_ABC178_B`: Pan C1, confidence high

Python multiplies the inputs (|x| up to 1e9) as unbounded ints; Java multiplies them as int inside maxProduct and returns int, so a*c etc. overflow and the max is wrong.

Source (`source.py`):
```
 13 |     a , b , c , d = LI ( )
 14 |     return max ( a * c , b * d , a * d , b * c )
```
Translation (`translation.java`):
```
 13 |     public static int maxProduct(int a, int b, int c, int d) {
```
**Fix used to verify:** `public static int maxProduct(int a, int b, int c, int d)` → `public static long maxProduct(long a, long b, long c, long d)`  
**Tests:** 3/35 → 35/35

*Notes:* The int reads at lines 6-9 are the same wrong type assumption; changing only the method signature (line 13) is sufficient because args widen. Could alternatively tag 6-9+13; line 13 is where the products are typed.

- [x] Confirmed by me

### `avatar-atcoder_AGC010_B`: Pan C1, confidence high

Python computes n*(n+1)/2 without overflow (as a float); Java computes n * (n + 1) in int, which overflows for n=100000, so the divisibility check and k are wrong.

Source (`source.py`):
```
  2 | if sum ( a ) % ( n * ( n + 1 ) / 2 ) :
  5 |     k = sum ( a ) / ( n * ( n + 1 ) / 2 )
```
Translation (`translation.java`):
```
 18 |         if (sum % (n * (n + 1) / 2) != 0) {
 21 |             long k = sum / (n * (n + 1) / 2);
```
**Fix used to verify:** `(n * (n + 1) / 2)` → `((long) n * (n + 1) / 2)` on lines 18 and 21  
**Tests:** 25/30 → 30/30

*Notes:* Latent second divergence: Java % can be negative and integer / truncates toward zero, unlike Python's % and true division on line 7 (Java lines 24/26/35), so negative remainders could cancel in sumDiff. Not exercised by any test (all pass after the overflow fix); not tagged.

- [x] Confirmed by me

### `avatar-atcoder_AGC019_A`: Pan C1, confidence medium

Python's best2L * (n // 2) is an unbounded int (up to ~5e16); Java holds n and best2L as int so the product overflows 32 bits.

Source (`source.py`):
```
 27 | n = INT ( )
 31 |     print ( best2L * ( n // 2 ) )
 33 |     print ( best2L * ( n // 2 ) + best1L )
```
Translation (`translation.java`):
```
 11 |         int n = sc.nextInt();
```
**Fix used to verify:** `int n = sc.nextInt();` → `long n = sc.nextLong();`  
**Tests:** 4/19 → 19/19

*Notes:* Changing line 13 (`int best2L` → `long best2L`) alone also gives 19/19, so the bug location is either the int type of n (line 11) or best2L (line 13); overflow happens in the products at lines 15/17. Tagged 11 as the read decision; 13 is an equally valid alternative (source line 29).

- [x] Confirmed by me

### `avatar-atcoder_AGC046_B`: Pan C1, confidence high

Python's % always returns a non-negative result, but Java's % keeps the sign of the (often negative) dividend, so cells become negative residues and the final answer is off by -m.

Source (`source.py`):
```
  7 |         d [ i ] [ j ] += ( d [ i ] [ j - 1 ] * i + d [ i - 1 ] [ j ] * j - d [ i - 1 ] [ j - 1 ] * ( i - 1 ) * ( j - 1 ) ) % m
```
Translation (`translation.java`):
```
 19 |                 d[i][j] += (int)(((long)d[i][j - 1] * i + (long)d[i - 1][j] * j - (long)d[i - 1][j - 1] * (i - 1) * (j - 1)) % m);
```
**Fix used to verify:** `(int)((...) % m)` → `(int)Math.floorMod((...), (long) m)` on line 19  
**Tests:** 12/17 → 17/17

*Notes:* Label disagreement: Pan says C1 (data type), but the actual fault is modulo semantics (closer to A4/A3). The long casts already prevent overflow; switching d to long[][] (C1-style fix) still gives 12/17. Expected 823951039 vs got -174293314 = exactly expected - 998244353.

- [x] Confirmed by me

### `avatar-atcoder_ARC086_B`: Pan B6, confidence high

No translation bug found: the Java output is byte-identical (modulo trailing spaces) to the Python source on the only test. The test expects '0' (the input is already sorted, a different valid answer), and the Python source itself prints the same 7-line answer as the Java.

**No translation bug.** Tests: 0/1.

*Notes:* Python source also fails 0/1. Problem accepts multiple valid answers; oracle mismatch, not a translation error. Integer.signum == my_sign; reversed range loop (lines 43-44) is equivalent. Pan's B6 label is not supported by execution evidence. Recommend excluding or tagging as 'no translation bug'.

- [x] Confirmed by me

### `avatar-codeforces_306_A`: Pan C3, confidence high

No translation bug found: Java prints the same sequence as Python (larger values first, trailing space, no newline) on all 20 tests. The 12 failing tests expect the values in ascending order, which the Python source does not produce either.

**No translation bug.** Tests: 8/20.

*Notes:* Python source also scores 8/20 with identical outputs; any order is a valid answer, so failures are oracle mismatches. Pan's C3 label not supported by execution. Recommend excluding or tagging as 'no translation bug'.

- [x] Confirmed by me

### `avatar-codeforces_30_A`: Pan C2, confidence high

Python reads A, B, n from one stdin line via input().split(); the Java reads them from command-line args[], which are empty, so it throws ArrayIndexOutOfBoundsException at line 3 on every test.

Source (`source.py`):
```
  6 | [ A , B , n ] = input ( ).split ( )
```
Translation (`translation.java`):
```
  3 |         int A = Integer.parseInt(args[0]);
  4 |         int B = Integer.parseInt(args[1]);
  5 |         int n = Integer.parseInt(args[2]);
```
**Fix used to verify:** `int A = Integer.parseInt(args[0]);` (and args[1], args[2]) → read the line from stdin: `String[] args2 = new Scanner(System.in).nextLine().trim().split("\\s+");` and parse args2[0..2]  
**Tests:** 0/68 → 50/68

*Notes:* The remaining 18 failures are not translation bugs: the Python source also scores 50/68, and fixed Java output equals Python output on all 68 tests (e.g. test 13 '1 961 2': both print -31, oracle expects 31; multiple valid answers). Math.pow on line 11 did not cause any divergence.

- [x] Confirmed by me

### `avatar-codeforces_387_A`: Pan A4/A1, confidence high

Python's % always returns a non-negative result for a positive modulus, so m2 %= 1440 wraps a negative time difference into 0..1439; Java's % keeps the sign of the dividend, so a negative difference stays negative and prints e.g. '-1:00'.

Source (`source.py`):
```
  6 | m2 %= 1440
```
Translation (`translation.java`):
```
 18 |         m2 %= 1440;
```
**Fix used to verify:** `m2 %= 1440;` → `m2 = Math.floorMod(m2, 1440);`  
**Tests:** 30/47 → 47/47

*Notes:* Both Pan labels (A4 operator, A1 target-language semantics) describe the same single line.

- [x] Confirmed by me

### `avatar-codeforces_400_A`: Pan B6, confidence high

Python iterates over sorted(tot), so pairs print in ascending order (1x12 ... 12x1); the Java iterates tot unsorted in insertion order (12x1 ... 1x12), dropping the sorted() call.

Source (`source.py`):
```
 35 |     for a , b in sorted ( tot ) :
```
Translation (`translation.java`):
```
 33 |             for (List<Integer> a : tot) {
```
**Fix used to verify:** `for (List<Integer> a : tot) {` → sort tot first: `tot.sort((u, v) -> u.get(0) != v.get(0).intValue() ? u.get(0) - v.get(0) : u.get(1) - v.get(1)); for (List<Integer> a : tot) {`  
**Tests:** 0/3 → 3/3

*Notes:* Missing sort when replacing the Python loop; B6 fits loosely (an API call, sorted(), was dropped rather than replaced). Since 12//i strictly decreases as i increases, sorting by the first element alone would be enough.

- [x] Confirmed by me

### `avatar-codeforces_459_A`: Pan C3, confidence high

The Java reproduces the Python exactly: on all 74 tests its stdout is byte-identical to the Python source's output. The 40 failures are tests where the problem (Pashmak and Garden) has several valid answers and the reference .out holds a different valid square than the one the Python prints; the Python source fails the same 40 tests.

**No translation bug.** Tests: 34/74.

*Notes:* Pan's C3 (output formatting) label is not supported: the print lines (31/38/44/50/52) produce the same text as the f-strings. Recommend excluding from ground truth or marking 'no translation bug / oracle issue'. Only latent difference: line 9 given.split(" ") vs Python split() would break on repeated/leading spaces (C2-type), but no test triggers it.

- [x] Confirmed by me

### `avatar-codeforces_579_A`: Pan C2, confidence high

Python's math.log2(n) is exact for powers of two, so for n=536870912 (2^29) the loop never runs. Java replaced it with Math.log(n)/Math.log(2), which gives 29.000000000000004, so the loop runs, n becomes 0, log(0)=-inf makes the condition NaN!=0 (always true), and n keeps decreasing forever.

Source (`source.py`):
```
  4 | while math.log2 ( n ) % 1 :
```
Translation (`translation.java`):
```
 10 |         while (Math.log(n) / Math.log(2) % 1 != 0) {
```
**Fix used to verify:** `while (Math.log(n) / Math.log(2) % 1 != 0) {` -> `while ((n & (n - 1)) != 0) {`  
**Tests:** 35/36 → 36/36

*Notes:* Genuine infinite loop (Pan's impact is right), not a slow-input artefact: the Python source finishes this test in ~0.02s with output 1. But the cause is a replaced API (log2 -> log ratio, B6/A3-type), not input parsing: input.nextInt() on line 8 is fine. Line 12 uses the same log-ratio idiom but needs no change (only line 10 fix -> 36/36), since floor of the ratio is correct for non-powers of two.

- [x] Confirmed by me

### `avatar-codeforces_621_A`: Pan C1, confidence high

Python's sum is an unbounded int; Java declares it as int, so summing five values of 999999999 overflows to -294967300 instead of 3999999996.

Source (`source.py`):
```
  9 | sum = 0
```
Translation (`translation.java`):
```
 24 |         int sum = 0;
```
**Fix used to verify:** `int sum = 0;` -> `long sum = 0;`  
**Tests:** 27/28 → 28/28

*Notes:* Element values fit in int (<=1e9), so line 10's nextInt() is fine; only the accumulator overflows.

- [x] Confirmed by me

### `avatar-codeforces_637_A`: Pan B6, confidence high

Python compares s.index(i) on the reversed list, i.e. how far from the end the word's last occurrence is, so it picks the max-count word whose last occurrence comes first. Java replaced s.index with the raw loop index i (iterating from the end), so the first max-count word seen from the end wins and later ones never satisfy i > c.

Source (`source.py`):
```
 11 |         if s.index ( i ) > c :
 13 |             c = s.index ( i )
```
Translation (`translation.java`):
```
 22 |             if (w.get(word) == Collections.max(w.values()) && i > c) {
 24 |                 c = i;
```
**Fix used to verify:** line 22 `&& i > c` -> `&& (s.length - 1 - java.util.Arrays.asList(s).lastIndexOf(word)) > c`; line 24 `c = i;` -> `c = s.length - 1 - java.util.Arrays.asList(s).lastIndexOf(word);`  
**Tests:** 17/28 → 28/28

*Notes:* Line 20 (reverse loop over positions instead of the Counter's keys) is the structural cause, but the wrong decision is the index used on 22/24. Latent second bug on line 22: `w.get(word) == Collections.max(...)` compares Integer objects by reference, which breaks for counts >127 (n up to 1000 in the problem); tests have n<=40 so it is not triggered.

- [x] Confirmed by me

### `avatar-codeforces_651_A`: Pan C2, confidence high

Python lines 3-6 only define unused helper lambdas; Java turned them into actual reads (lines 10-19), which hit end of input and throw NoSuchElementException after the answer is printed. Second bug: Python's (y-x)%3 is never negative, but Java's % is, so when y<x the +1 term is lost.

Source (`source.py`):
```
  2 | print ( max ( x + y - 3 + ( ( y - x ) % 3 > 0 ) , 0 ) )
  3 | num_inp = lambda : int ( input ( ) )
  4 | arr_inp = lambda : list ( map ( int , input ( ).split ( ) ) )
  5 | sp_inp = lambda : map ( int , input ( ).split ( ) )
  6 | str_inp = lambda : input ( )
```
Translation (`translation.java`):
```
  8 |         System.out.println(Math.max(x + y - 3 + ((y - x) % 3 > 0 ? 1 : 0), 0));
 10 |         int num_inp = scanner.nextInt();
 13 |             arr_inp[i] = scanner.nextInt();
 16 |         int sp_inp1 = scanner.nextInt();
 17 |         int sp_inp2 = scanner.nextInt();
 19 |         String str_inp = scanner.next();
```
**Fix used to verify:** delete lines 10-19 (the extra reads); and line 8 `((y - x) % 3 > 0` -> `(Math.floorMod(y - x, 3) > 0`  
**Tests:** 0/39 → 39/39 (deleting reads alone: 29/39; floorMod alone: 0/39)

*Notes:* Two bugs. Bug 1 (C2, Pan's label, crash at line 10 per stack trace): source 3-6 -> translation 10,13,16,17,19 (reads; 11-12,14 are dependent declarations/loop). Bug 2 (unlabelled by Pan, A4/A3-type modulo semantics): source line 2 -> translation line 8; it causes 10 wrong outputs once the crash is removed. Tag both.

- [x] Confirmed by me

### `avatar-codeforces_665_A`: Pan C1, confidence high

Python reads the departure time 'hh:mm' as one token and splits it on ':' into two ints; the Java assumes t1 and t2 are separate whitespace-delimited integers and calls sc.nextInt() on '21:15', which throws InputMismatchException.

Source (`source.py`):
```
  3 | t1 , t2 = map ( int , input ( ).split ( ':' ) )
```
Translation (`translation.java`):
```
 12 |         t1 = sc.nextInt();
 13 |         t2 = sc.nextInt();
```
**Fix used to verify:** `t1 = sc.nextInt(); t2 = sc.nextInt();` -> `String[] tt = sc.next().split(":"); t1 = Integer.parseInt(tt[0]); t2 = Integer.parseInt(tt[1]);`  
**Tests:** 0/31 → 31/31

*Notes:* Location is certain (stack trace at line 12, and the fix passes all 31 tests). The bug is about reading the ':'-separated time token, which fits C2 (incorrect input parsing) better than Pan's C1 (data type). A C1 reading is possible only if you argue it wrongly assumed the token is an int. Line 12 throws first; line 13 is the same mistake for t2.

- [x] Confirmed by me

### `codenet-s259116349`: Pan C2, confidence high

In Python, `i = i//p` rebinds i only until the for-loop's next iteration sets it again from range(). Java's `i /= p` changes the for-loop counter itself, so i keeps being divided back down to 1 (for example 2 -> 1 -> i++ -> 2) and the loop never ends.

Source (`source.py`):
```
 12 |         while(i//p==i/p):
 13 |             i = i//p
```
Translation (`translation.java`):
```
 15 |                 while (i % p == 0) {
 16 |                     i /= p;
```
**Fix used to verify:** add `int x = i;` before the j-loop and use `while (x % p == 0) { x /= p; ...}` instead of mutating i  
**Tests:** 0/1 (timeout) → 1/1

*Notes:* This is a genuine infinite loop, not a slow environment. The mutated i also makes line 19 (`divs[i - 1][j] = tmp`) write to the wrong row, but that clears up once 15-16 are fixed, so line 19 is not tagged. The real cause is changing the loop variable (Python for-range rebinding semantics). It has nothing to do with input parsing, so Pan's C2 label looks wrong. A4/A3-style 'behaviour mismatch' fits better.

- [x] Confirmed by me

### `codenet-s813548165`: Pan B6, confidence high

Python's input().split() reads the whole line 'ip cc' and splits it into S and T. Java's scanner.next() returns only the first token 'ip', so splitting it gives a 1-element array and input[1] throws ArrayIndexOutOfBoundsException.

Source (`source.py`):
```
  2 | S,T = input().split()
```
Translation (`translation.java`):
```
  7 |     String[] input = scanner.next().split(" ");
```
**Fix used to verify:** `String[] input = scanner.next().split(" ");` -> `String[] input = {scanner.next(), scanner.next()};`  
**Tests:** 0/1 → 1/1

*Notes:* The exception is raised at line 9 (input[1]), but the wrong decision is the scanner.next() call on line 7. Replacing input() with Scanner.next(), which behaves differently, fits B6; C2 would also be defensible.

- [x] Confirmed by me

### `codenet-s826716211`: Pan C2, confidence high

Python's input() reads lines from stdin whatever it is connected to. The Java replaced it with System.console().readLine(), and System.console() returns null when stdin is piped or redirected, which is how judges supply input, so the first read throws a NullPointerException.

Source (`source.py`):
```
  3 |     S_d = list(input())
  4 |     T = list(input())
```
Translation (`translation.java`):
```
 47 |         return System.console().readLine();
```
**Fix used to verify:** `return System.console().readLine();` -> `return SC.nextLine();` (with `static java.util.Scanner SC = new java.util.Scanner(System.in);`)  
**Tests:** 0/1 → 1/1

*Notes:* This counts as a translation bug, not a harness artifact. Any non-interactive judge (AtCoder included) pipes stdin, so System.console() is null there too. It is an input-reading API swap with different behaviour, so C2 or B6 both fit. The rest of the logic (the for-else replaced by the t_i==T.length check plus first<0) is correct.

- [x] Confirmed by me

### `codenet-s875904659`: Pan C3, confidence high

Python prints the cards with ' '.join(...), giving 'D2 C3 H4'. Java uses Arrays.toString, which adds brackets and commas ('[D2, C3, H4]'), so the output doesn't match.

Source (`source.py`):
```
  8 |     print( " ".join( map( str, cards ) ) )
 20 | 	print( " ".join( map( str, cards ) ) )
```
Translation (`translation.java`):
```
 17 |         System.out.println(Arrays.toString(cards));
 35 |         System.out.println(Arrays.toString(cards));
```
**Fix used to verify:** `System.out.println(Arrays.toString(cards));` -> `System.out.println(String.join(" ", Arrays.stream(cards).map(Card::toString).toArray(String[]::new)));` (both lines 17 and 35)  
**Tests:** 0/1 → 1/1

*Notes:* SECOND, LATENT BUG at translation line 53 (source line 29): Arrays.equals(cards, cards2) compares Card objects by reference because Card does not override equals, so it always prints 'Not stable'. The one test expects 'Not stable', so this bug doesn't show there. With the formatting fix applied, input '3\nH1 C2 S3' gives 'Not stable' while Python gives 'Stable'. Line 53 is left out of the tags because no test exposes it; add it if ground truth should cover latent bugs.

- [x] Confirmed by me

## Full latent-bug review (2026-11-20)

All 21 buggy samples (starting from the test-bug-fixed Java) and all 10 controls were read line by line and fuzzed on constraint-valid inputs. The agent brief, per-sample scripts and logs were kept outside the repository (see the note at the top).

| Sample | Result | Lines (src / java) | Evidence (before -> after fixing only those lines) |
|---|---|---|---|
| AGC010_B | latent (known) | 7 / 24, 26 | 3/100 random -> 0; "3\n6 13 11": Java YES, Python NO |
| 637_A | latent (known) | 5, 10 / 10, 22 | 117/200 ties >= 128 -> 0; repro (2 1)x128 |
| s875904659 | latent (known) | 29 / 53 | 164/304 -> 0 |
| ABC150_C, 459_A, 108_B | split(" ") only (known, format-only) | as before | - |
| **codenet-s662673721 (control)** | **new latent** | 4, 11 / 7, 14 | nextInt on N up to 1e12: 204/306 -> 0; N=10000000019 crashes Java. Only test has N=10 |
| **codenet-s764169243 (control)** | **new latent** | 50, 53, 57, 60 / 58, 75 | int ans/sum overflow from N=2999: 13/305 -> 0; N=2e5 gives -2083774016. Only test has N=3 |
| other 22 samples | none | - | 0 divergences (several exhaustive: 30_A, 387_A, 400_A, 579_A, 651_A, s259116349) |

Claude re-ran the two new ones by hand (N=2147483648, 1e10+19, 999999999999; N=2999, 3000, 200000) and both fixed versions still pass their dataset test.

Side findings, not tagged: ABC123_C's source imports `fractions.gcd` (removed in Python 3.9) and numpy, both unused, so it won't run on modern Python as-is. 637_A's Python `input()[:-1]` drops a real character if the last line has no newline (a quirk in the source, not the translation).

So 3 of 10 controls (Pan: no bug) hide a latent divergence; 2 of them are real overflow/range bugs that a judge with larger tests would catch.
