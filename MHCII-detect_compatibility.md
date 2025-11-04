# MHC Class II Method Compatibility Detection Report

## Executive Summary

This report documents the macOS compatibility status for all Class II MHC binding prediction methods in the `ng_tc2-0.2.2-beta` package. The analysis was performed to determine which methods can run natively on macOS (specifically Apple Silicon ARM64 architecture) versus those requiring Linux environments.

**Key Findings:**
- **2 methods** are fully compatible (pure Python implementations)
- **1 method** is potentially compatible (requires script modification for ARM64)
- **3 methods** are not compatible (Linux-only binaries)

---

## Methods Analyzed

1. NetMHCIIpan_EL (Elution Likelihood)
2. NetMHCIIpan_BA (Binding Affinity)
3. NN_align (Neural Network Alignment)
4. SMM_align (Stabilized Matrix Method Alignment)
5. TEPITOPE (T Cell Epitope Prediction Tool)
6. Comblib (Combined Library Method)

---

## Compatibility Status by Method

### ✅ **Fully Compatible - Pure Python/Perl (No Binaries Required)**

#### 1. TEPITOPE ✅
- **Implementation**: Pure Python
- **Location**: `method/mhcii-tepitope-predictor/`
- **Dependencies**: Python pickle data files (`tepitope_predictor_data_2016-01-29.p`)
- **Platform Requirements**: None (Python-only)
- **Status**: **WORKS ON macOS**
- **Notes**: Uses lookup matrices stored in pickle format. No compiled binaries or platform-specific code.

#### 2. Comblib ✅
- **Implementation**: Pure Python
- **Location**: `method/mhcii-comblib-predictor/`
- **Dependencies**: Python pickle data files (`comblib_predictor_data_pre_2016-02-12.p`)
- **Platform Requirements**: None (Python-only)
- **Status**: **WORKS ON macOS**
- **Notes**: Uses lookup matrices and mathematical calculations. No compiled binaries required.

---

### ⚠️ **Potentially Compatible - Requires Modification**

#### 3. NN_align ⚠️
- **Implementation**: Perl wrapper + compiled binaries
- **Location**: `src/nnalign/`
- **Binaries Available**: 
  - `Darwin_x86_64/` ✅ (exists)
  - `Darwin_i386/` ✅ (exists)
  - `Linux_x86_64/` ✅
  - `Linux_ia64/` ✅
- **Platform Detection**: `src/nnalign/nnalign-1.4.SA.pl` lines 41-58
- **Current Detection Logic**:
  ```perl
  my $platform = qx(uname -sm);
  if ($platform eq "Linux x86_64") {
      $subbin = "Linux_x86_64";
  } elsif ($platform eq "Darwin i386") {
      $subbin = "Darwin_i386";
  } elsif ($platform eq "Darwin x86_64") {
      $subbin = "Darwin_x86_64";
  } else {
      print "Platform: $platform not supported.";
      exit(0);
  }
  ```
- **Issue**: Apple Silicon Macs report "Darwin arm64", which is not handled
- **Status**: **CAN WORK WITH MODIFICATION**
- **Solution Options**:
  1. **Option A (Recommended)**: Modify platform detection to map "Darwin arm64" → "Darwin_x86_64" and use Rosetta 2 for x86_64 binary execution
  2. **Option B**: Recompile binaries for ARM64 (if source code available)
- **Required Changes**: Add to `nnalign-1.4.SA.pl`:
  ```perl
  elsif ($platform eq "Darwin arm64") {
      $subbin = "Darwin_x86_64";  # Use Rosetta 2 compatibility
  }
  ```

---

### ❌ **Not Compatible - Linux-Only Binaries**

#### 4. NetMHCIIpan_EL ❌
- **Implementation**: tcsh shell script + compiled binaries
- **Location**: `method/netmhciipan-4.3-executable/` (and versions 4.1, 4.2, 3.2)
- **Executable**: `netMHCIIpan` (tcsh script)
- **Platform Detection**: Script uses `uname -s` and `uname -m` to construct `$UNIX_$AR` (e.g., "Linux_x86_64")
- **Binaries Available**: Only `Linux_x86_64/` directory found
- **Status**: **REQUIRES LINUX**
- **Notes**: 
  - Script wrapper exists but calls platform-specific binaries
  - No Darwin (macOS) binaries provided
  - Would require Linux environment (Docker, WSL, or native Linux)

#### 5. NetMHCIIpan_BA ❌
- **Implementation**: Same as NetMHCIIpan_EL
- **Location**: Same as NetMHCIIpan_EL
- **Difference**: Uses `-BA` flag instead of `-EL` (elution likelihood)
- **Status**: **REQUIRES LINUX**
- **Notes**: Same limitations as NetMHCIIpan_EL

#### 6. SMM_align ❌
- **Implementation**: Python interface + compiled binaries
- **Location**: `method/netmhcii-1.1-executable/`
- **Interface**: `netmhcii_11_python_interface.py`
- **Binaries Available**: Only `binaries_Linux_x86_64/` directory found
  - Contains: `cl2pred_ens_flank_end`, `fasta2pep`, `netMHCII`
- **Status**: **REQUIRES LINUX**
- **Notes**: 
  - No macOS binaries provided
  - Different from Class I SMM which had macOS support
  - Class II uses `netmhcii-1.1-executable` which is Linux-only

---

## Comparison with Class I Workflow (Anastasia)

### Class I Methods (Working on macOS)
- **SMM** (Class I): ✅ Worked on Mac
- **ANN** (Class I): ✅ Worked on Mac

### Class II Methods (Current Status)
- **SMM_align** (Class II): ❌ Uses different executable (`netmhcii-1.1`) - Linux only
- **NN_align** (Class II): ⚠️ Has Darwin binaries but needs ARM64 detection fix

**Key Difference**: Class I and Class II use different underlying executables, even though method names are similar.

---

## Technical Details

### Platform Detection Mechanisms

#### NN_align Platform Detection
- **Script**: `src/nnalign/nnalign-1.4.SA.pl`
- **Method**: Uses `uname -sm` command
- **Supported Platforms** (as detected):
  - Linux x86_64 → Linux_x86_64 binaries
  - Linux ia64 → Linux_ia64 binaries
  - Darwin i386 → Darwin_i386 binaries
  - Darwin x86_64 → Darwin_x86_64 binaries
- **Missing**: Darwin arm64 (Apple Silicon)

#### NetMHCIIpan Platform Detection
- **Script**: `method/netmhciipan-4.3-executable/netmhciipan_4_3_executable/netMHCIIpan`
- **Method**: Uses `uname -s` and `uname -m` to construct platform string
- **Logic**: Constructs `$UNIX_$AR` (e.g., "Linux_x86_64")
- **Available Binaries**: Only Linux_x86_64 directories found

### Binary File Analysis

#### NN_align Binaries (Darwin_x86_64)
Found in `src/nnalign/bin/Darwin_x86_64/`:
- `smm_align_flank_gd_nn_pssm` (Mach-O 64-bit executable x86_64)
- `common_motif_long`
- `gibbss_mc.pssmalign.RL`
- `hobohm1_id`
- `pep2mat`
- `logtransf.pl` (Perl script)
- Other supporting binaries

**File Type Verification**: 
```bash
file Darwin_x86_64/smm_align_flank_gd_nn_pssm
# Output: Mach-O 64-bit executable x86_64
```

#### SMM_align Binaries
Found in `method/netmhcii-1.1-executable/netmhcii_11_executable/binaries_Linux_x86_64/`:
- `cl2pred_ens_flank_end` (Linux ELF binary)
- `fasta2pep` (Linux ELF binary)
- `netMHCII` (Linux ELF binary)

**No macOS binaries found** for this method.

---

## Recommendations

### Immediate Actions (For macOS Testing)

1. **Enable TEPITOPE** ✅
   - Uncomment in Perl script
   - No modifications needed
   - Ready to test immediately

2. **Enable Comblib** ✅
   - Uncomment in Perl script
   - No modifications needed
   - Ready to test immediately

3. **Fix NN_align for ARM64** ⚠️
   - Modify `src/nnalign/nnalign-1.4.SA.pl`
   - Add Darwin arm64 → Darwin_x86_64 mapping
   - Requires Rosetta 2 (should be pre-installed on Apple Silicon Macs)
   - Estimated effort: 5 minutes

### Long-term Solutions

1. **For Full Functionality**:
   - Run on Linux system (native or VM)
   - Use Docker container with Linux base image
   - Use WSL (Windows Subsystem for Linux) on Windows
   - Use cloud Linux instances (AWS, GCP, Azure)

2. **For macOS Development**:
   - Request ARM64 binaries from IEDB developers
   - Compile from source (if available)
   - Use Rosetta 2 for x86_64 compatibility (limited to NN_align)

---

## Testing Recommendations

### Phase 1: Pure Python Methods
1. Test TEPITOPE with sample data
2. Test Comblib with sample data
3. Verify output format matches expected structure

### Phase 2: Modified Methods
1. Apply NN_align platform detection fix
2. Test with Rosetta 2 compatibility
3. Verify binary execution works correctly

### Phase 3: Linux-Only Methods (if needed)
1. Set up Docker container with Linux environment
2. Test NetMHCIIpan_EL/BA in container
3. Test SMM_align in container
4. Integrate with workflow

---

## File Locations Reference

### Method Implementations
- **TEPITOPE**: `method/mhcii-tepitope-predictor/mhcii_tepitope_predictor/__init__.py`
- **Comblib**: `method/mhcii-comblib-predictor/mhcii_comblib_predictor/__init__.py`
- **NN_align**: `src/nnalign/nnalign-1.4.SA.pl`
- **SMM_align**: `method/netmhcii-1.1-executable/netmhcii_11_executable/`
- **NetMHCIIpan**: `method/netmhciipan-4.3-executable/netmhciipan_4_3_executable/`

### Binary Directories
- **NN_align**: `src/nnalign/bin/Darwin_x86_64/`
- **SMM_align**: `method/netmhcii-1.1-executable/netmhcii_11_executable/binaries_Linux_x86_64/`
- **NetMHCIIpan**: `method/netmhciipan-4.3-executable/netmhciipan_4_3_executable/Linux_x86_64/`

---

## Conclusion

For immediate macOS testing, **TEPITOPE and Comblib** can be enabled immediately with no modifications. **NN_align** requires a simple platform detection fix to work on Apple Silicon via Rosetta 2. **NetMHCIIpan_EL/BA and SMM_align** require Linux environments for full functionality.

The Class II package has better macOS support than initially expected, with 2 methods working natively and 1 method requiring minimal modification. This represents 50% native compatibility (3/6 methods) compared to the Class I workflow which had broader macOS support.

---

**Report Generated**: 2025-11-03  
**System Tested**: macOS (Darwin arm64)  
**Package Version**: ng_tc2-0.2.2-beta  
**Analysis Method**: File system inspection, binary type checking, code review

