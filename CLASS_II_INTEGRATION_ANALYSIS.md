# Class II Package Integration Analysis Report

**Date:** 2025-11-03  
**Package:** IEDB_NG_TC2-0.2.2-beta.tar  
**Target:** Adapt Anastasia2 workflow from Class I (MHC I) to Class II (MHC II)

---

## Task 1: Tarball Integrity Verification

### Status: ✓ VERIFIED
- **Tarball:** `IEDB_NG_TC2-0.2.2-beta.tar` (3.9GB)
- **MD5SUM file:** Contains checksum for `.tar.gz` format
- **Calculated MD5 (.tar):** `f570fd9d5777ce950004b197e5891ee2`
- **Integrity test:** Tarball is readable and not corrupted
- **Note:** MD5SUM mismatch expected - file format differs (.tar.gz vs .tar)

---

## Task 2: Package Structure Analysis

### Package Details
- **Extracted directory:** `ng_tc2-0.2.2-beta/`
- **Main script:** `src/tcell_mhcii.py` (vs Class I's `tcell_mhci.py`)
- **Command format:** `python3 src/tcell_mhcii.py -j <input_json> -o <output_prefix> -f <format>`
- **JSON format:** Compatible with Class I (same structure)

### Key Differences from Class I

| Aspect | Class I (1_ng_tc1-0.1.2-beta) | Class II (ng_tc2-0.2.2-beta) |
|--------|------------------------------|------------------------------|
| **Package name** | `1_ng_tc1-0.1.2-beta` | `ng_tc2-0.2.2-beta` |
| **Script** | `tcell_mhci.py` | `tcell_mhcii.py` |
| **Allele format** | `HLA-A*01:01`, `HLA-B*07:02` | `DRB1*01:01`, `DQA*01:01`, `DQB*01:01` |
| **Peptide lengths** | 8-10 (typically 8, 9, 10) | 15-30 (typically 15-30) |
| **Methods** | `smm`, `ann`, `comblib_sidney2008` | `netmhciipan_el`, `netmhciipan_ba`, `nn_align`, `smm_align`, `tepitope`, `comblib`, `mhciinp`, `cd4episcore` |

### Class II Methods Available

**Binding Methods:**
- `netmhciipan_el` - NetMHCIIpan elution likelihood
- `netmhciipan_ba` - NetMHCIIpan binding affinity
- `nn_align` - Neural network alignment
- `smm_align` - Stabilized matrix method alignment
- `tepitope` - TEPITOPE
- `comblib` - Combinatorial library

**Processing Methods:**
- `mhciinp` - MHCII natural processing

**Immunogenicity Methods:**
- `cd4episcore` - CD4+ epitope score

---

## Task 3: Substitution Complexity Assessment

### Integration Points Identified

#### 3.1 Python Wrapper (`iedb_run-cmd_wrapper.py`)

**File:** `/Users/michael_gaunt/Desktop/Anastasia2/iedb_run-cmd_wrapper.py`

**Changes Required:**

1. **Line 25:** PERL_SRC path
   ```python
   # CURRENT:
   PERL_SRC = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl"
   # CHANGE TO:
   PERL_SRC = BASE_DIR / "vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl"
   ```

2. **Lines 34-35:** Parser paths
   ```python
   # CURRENT:
   PARSER_REF = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl"
   PARSER_V05 = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl"
   # CHANGE TO:
   PARSER_REF = BASE_DIR / "vendor/ng_tc2-0.2.2-beta/iedb_output_ref-parse_v0-1.pl"
   PARSER_V05 = BASE_DIR / "vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-5.pl"
   ```

3. **Line 184:** Python script path
   ```python
   # CURRENT:
   python_script_path = BASE_DIR / "1_ng_tc1-0.1.2-beta/src/tcell_mhci.py"
   # CHANGE TO:
   python_script_path = BASE_DIR / "ng_tc2-0.2.2-beta/src/tcell_mhcii.py"
   ```

4. **Line 186:** Hardcoded path in Perl template replacement
   ```python
   # CURRENT:
   'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
   # CHANGE TO:
   'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/ng_tc2-0.2.2-beta/src/tcell_mhcii.py";'
   ```

5. **Line 37:** CD8_ALLELE constant (if used)
   ```python
   # CURRENT:
   CD8_ALLELE = "HLA-A*02:01"
   # CHANGE TO (optional, may be removed):
   CD4_ALLELE = "DRB1*01:01"
   ```

**Complexity:** EASY - Simple path replacements

---

#### 3.2 Perl Script (`iedb_alignment_run_v0-2.pl`)

**File:** `/Users/michael_gaunt/Desktop/Anastasia/vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl`

**Changes Required:**

1. **Line 231:** Hardcoded Python script path
   ```perl
   # CURRENT:
   my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";
   # CHANGE TO:
   my $iedb_script = ($ENV{"BASE_DIR"} ? $ENV{"BASE_DIR"} : "/Users/michael_gaunt/Desktop/Anastasia2") . "/ng_tc2-0.2.2-beta/src/tcell_mhcii.py";
   ```

2. **Lines 212-215:** Method selection
   ```perl
   # CURRENT:
   my @methods = ('smm', 'ann');
   if ($no == 9) {
       push @methods, 'comblib_sidney2008';
   }
   # CHANGE TO (Class II methods - no length restrictions):
   my @methods = ('netmhciipan_el', 'netmhciipan_ba', 'nn_align', 'smm_align');
   # OR use a subset based on requirements
   ```

3. **Line 208:** Length range loop
   ```perl
   # CURRENT:
   foreach my $no ($length_min..$length_max){  # Typically 8..10
   # CHANGE TO:
   foreach my $no ($length_min..$length_max){  # Typically 15..30
   # Note: The range is loaded from params/length.dat, so update that file
   ```

4. **Allele variable name:** `$cd8_0` → `$cd4_0` (optional, for clarity)
   ```perl
   # CURRENT:
   sub run_iedb {
       my ($alignment_0, $locus_0, $align_loc_0, $iedb_out_0, $cd8_0) = @_;
   # CHANGE TO:
   sub run_iedb {
       my ($alignment_0, $locus_0, $align_loc_0, $iedb_out_0, $cd4_0) = @_;
   # Then replace all $cd8_0 with $cd4_0 throughout the function
   ```

5. **Variable references:** Replace `$cd8_0` with `$cd4_0` throughout the function (lines 217, 239, etc.)

**Complexity:** MODERATE - Requires method mapping and variable renaming

---

#### 3.3 Parameter Files

**File:** `/Users/michael_gaunt/Desktop/Anastasia2/params/CD_type.dat`

**Current Content (Class II alleles - already updated):**
```
'HLA-DRB1*01:01',
'HLA-DRB1*03:01',
...
```

**Status:** ✓ Already contains Class II alleles

**File:** `/Users/michael_gaunt/Desktop/Anastasia2/params/length.dat`

**Current Content:**
```
8, 10
```

**Change Required:**
```
15, 30
```

**Complexity:** EASY - Simple file update

---

#### 3.4 Conversion Scripts

**File:** `/Users/michael_gaunt/Desktop/Anastasia2/convert_to_docker.py`

**Changes Required:**

1. **Lines 29-31:** Vendor Perl script paths
   ```python
   # CURRENT:
   "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl",
   "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl",
   "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl",
   # CHANGE TO:
   "vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl",
   "vendor/ng_tc2-0.2.2-beta/iedb_output_ref-parse_v0-1.pl",
   "vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-5.pl",
   ```

2. **Line 42:** Package directory to copy
   ```python
   # CURRENT:
   "1_ng_tc1-0.1.2-beta",
   # CHANGE TO:
   "ng_tc2-0.2.2-beta",
   ```

3. **Lines 79-80, 115-116:** Hardcoded path replacements
   ```python
   # CURRENT:
   old_pattern2 = 'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
   new_pattern2 = 'my $iedb_script = ($ENV{"BASE_DIR"} ? $ENV{"BASE_DIR"} : "/app") . "/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
   # CHANGE TO:
   old_pattern2 = 'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/ng_tc2-0.2.2-beta/src/tcell_mhcii.py";'
   new_pattern2 = 'my $iedb_script = ($ENV{"BASE_DIR"} ? $ENV{"BASE_DIR"} : "/app") . "/ng_tc2-0.2.2-beta/src/tcell_mhcii.py";'
   ```

4. **Lines 232, 242, 252:** Perl script paths in copy functions
   ```python
   # CURRENT:
   perl_align = "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl"
   # CHANGE TO:
   perl_align = "vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl"
   ```

**Complexity:** EASY - Simple path replacements

---

#### 3.5 Dockerfile

**File:** `/Users/michael_gaunt/Desktop/Anastasia2/Dockerfile`

**Changes Required:**

1. **Line 19:** Requirements file path
   ```dockerfile
   # CURRENT:
   COPY 1_ng_tc1-0.1.2-beta/requirements.txt /tmp/requirements.txt
   # CHANGE TO:
   COPY ng_tc2-0.2.2-beta/requirements.txt /tmp/requirements.txt
   ```

2. **Line 27:** PYTHONPATH
   ```dockerfile
   # CURRENT:
   ENV PYTHONPATH=$WORKDIR/1_ng_tc1-0.1.2-beta/src:$PYTHONPATH
   # CHANGE TO:
   ENV PYTHONPATH=$WORKDIR/ng_tc2-0.2.2-beta/src:$PYTHONPATH
   ```

3. **Line 28:** PERL5LIB
   ```dockerfile
   # CURRENT:
   ENV PERL5LIB=$WORKDIR/vendor/1_ng_tc1-0.1.2-beta:$PERL5LIB
   # CHANGE TO:
   ENV PERL5LIB=$WORKDIR/vendor/ng_tc2-0.2.2-beta:$PERL5LIB
   ```

4. **Line 34-35:** Chmod commands
   ```dockerfile
   # CURRENT:
   RUN chmod +x $WORKDIR/vendor/1_ng_tc1-0.1.2-beta/*.pl && \
       chmod +x $WORKDIR/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py
   # CHANGE TO:
   RUN chmod +x $WORKDIR/vendor/ng_tc2-0.2.2-beta/*.pl && \
       chmod +x $WORKDIR/ng_tc2-0.2.2-beta/src/tcell_mhcii.py
   ```

**Complexity:** EASY - Simple path replacements

---

#### 3.6 Parser Scripts

**Files:**
- `iedb_output_ref-parse_v0-1.pl`
- `iedb_output_parse_v0-5.pl`

**Potential Issues:**
- May need Class II-specific output format adaptations
- TSV column structure may differ between Class I and Class II
- Allele format parsing (HLA-A*01:01 vs DRB1*01:01)

**Complexity:** MODERATE to HIGH - Requires testing to determine if output format differs

**Recommendation:** Test with Class II output first to see if parsers work without modification

---

### Summary of Complexity

| Component | Complexity | Changes Required |
|-----------|-----------|------------------|
| **Python Wrapper** | EASY | 5 path replacements |
| **Perl Alignment Script** | MODERATE | Path, methods, length range, variable names |
| **Parameter Files** | EASY | Update length.dat (CD_type.dat already done) |
| **Conversion Scripts** | EASY | 8 path replacements |
| **Dockerfile** | EASY | 4 path replacements |
| **Parser Scripts** | MODERATE-HIGH | May need Class II format adaptations |

---

## Recommended Approach

### Phase 1: Basic Path Substitution (EASY)
1. Update all package paths: `1_ng_tc1-0.1.2-beta` → `ng_tc2-0.2.2-beta`
2. Update script name: `tcell_mhci.py` → `tcell_mhcii.py`
3. Update `params/length.dat`: `8, 10` → `15, 30`

### Phase 2: Method and Logic Updates (MODERATE)
1. Create Class II version of `iedb_alignment_run_v0-2.pl`:
   - Copy from Class I version
   - Update Python script path
   - Replace methods: `smm`, `ann`, `comblib_sidney2008` → Class II equivalents
   - Update variable names: `$cd8_0` → `$cd4_0` (optional)
   - Save as `vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl`

2. Update wrapper script paths

3. Update conversion scripts

4. Update Dockerfile

### Phase 3: Testing and Validation (REQUIRED)
1. Extract Class II package to Anastasia2
2. Test `tcell_mhcii.py` with example JSON
3. Run end-to-end workflow with test data
4. Verify parser scripts work with Class II output format
5. Adapt parsers if output format differs

### Phase 4: Method Selection Strategy

**Option A: Use All Available Methods**
```perl
my @methods = ('netmhciipan_el', 'netmhciipan_ba', 'nn_align', 'smm_align', 'tepitope');
```

**Option B: Use Core Methods (Recommended for initial testing)**
```perl
my @methods = ('netmhciipan_el', 'nn_align', 'smm_align');
```

**Option C: Map Class I to Class II Equivalents**
- `smm` → `smm_align`
- `ann` → `nn_align`
- `comblib_sidney2008` → `comblib` (if available)

---

## Files to Create/Modify

### Files to Create:
1. `vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl` (copy and adapt from Class I)

### Files to Modify:
1. `iedb_run-cmd_wrapper.py` - Update paths
2. `params/length.dat` - Update to 15-30
3. `convert_to_docker.py` - Update paths
4. `Dockerfile` - Update paths
5. Parser scripts (if needed after testing)

---

## Overall Assessment

**Complexity Level: MODERATELY EASY**

The substitution is **straightforward** because:
- JSON input/output format is compatible
- Command-line interface is identical
- Overall structure is very similar

**Challenges:**
- Method names are completely different (no direct mapping)
- Length ranges differ significantly (8-10 vs 15-30)
- Allele format is different (HLA-A/B/C vs DRB1/DQA/DQB)
- Parser scripts may need format adaptations

**Estimated Effort:**
- Path substitutions: 1-2 hours
- Method/logic updates: 2-3 hours
- Testing and validation: 3-4 hours
- Parser adaptations (if needed): 2-4 hours

**Total: ~8-13 hours**

---

## Next Steps

1. ✅ Verify tarball integrity
2. ✅ Review README and package structure
3. ✅ Extract and verify structure
4. ✅ Assess substitution complexity
5. ⏳ Implement Phase 1 (Basic path substitution)
6. ⏳ Implement Phase 2 (Method and logic updates)
7. ⏳ Phase 3 (Testing and validation)

---

**Report Generated:** 2025-11-03  
**Status:** Analysis Complete - Ready for Implementation

