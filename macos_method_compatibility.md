# macOS Compatibility for Class II Binding Methods

## Summary

Based on analysis of the `ng_tc2-0.2.2-beta` package, here's the macOS compatibility status for each method:

### ✅ **Fully Compatible (Pure Python/Perl)**

1. **TEPITOPE** ✅
   - Pure Python implementation using pickle data files
   - No platform-specific binaries
   - **Status**: Works on macOS

2. **Comblib** ✅
   - Pure Python implementation using pickle data files
   - No platform-specific binaries
   - **Status**: Works on macOS

### ⚠️ **Potentially Compatible (with Rosetta 2 or modifications)**

3. **NN_align** ⚠️
   - **Binaries available**: Darwin_x86_64 (found in `src/nnalign/bin/Darwin_x86_64/`)
   - **Issue**: Platform detection script checks for "Darwin x86_64" but your Mac reports "Darwin arm64"
   - **Solution**: 
     - Option A: Use Rosetta 2 to run x86_64 binaries (may require modifying platform detection)
     - Option B: Modify `nnalign-1.4.SA.pl` to handle "Darwin arm64" and use Darwin_x86_64 binaries via Rosetta
   - **Status**: Should work with Rosetta 2 or script modification

### ❌ **Not Compatible (Linux-only binaries)**

4. **NetMHCIIpan_EL** ❌
   - Uses shell script wrapper (tcsh) but calls Linux binaries
   - Only Linux_x86_64 binaries available
   - **Status**: Requires Linux (or Docker/WSL)

5. **NetMHCIIpan_BA** ❌
   - Same as NetMHCIIpan_EL
   - Only Linux_x86_64 binaries available
   - **Status**: Requires Linux (or Docker/WSL)

6. **SMM_align** ❌
   - Uses `netmhcii-1.1-executable` which only has Linux_x86_64 binaries
   - No macOS binaries found
   - **Status**: Requires Linux (or Docker/WSL)

## Comparison with Class I (Anastasia)

In the Class I workflow (`1_ng_tc1-0.1.2-beta`):
- **SMM** (Class I): Worked on Mac ✅
- **ANN** (Class I): Worked on Mac ✅

However, for Class II:
- **SMM_align**: Uses different executable (netmhcii-1.1) that only has Linux binaries ❌
- **NN_align**: Has Darwin_x86_64 binaries but needs script modification for ARM64 ⚠️

## Recommendations

### For immediate testing on macOS:
1. **Enable TEPITOPE** - Pure Python, will work immediately
2. **Enable Comblib** - Pure Python, will work immediately
3. **Try NN_align** - Modify platform detection in `nnalign-1.4.SA.pl` to handle "Darwin arm64" and use Darwin_x86_64 binaries

### For full functionality:
- Run on Linux system, or
- Use Docker container with Linux environment, or
- Use WSL (Windows Subsystem for Linux) on Windows

## Technical Details

### Platform Detection Issue (NN_align)
The `nnalign-1.4.SA.pl` script uses:
```perl
my $platform = qx(uname -sm);
```
This returns "Darwin arm64" on Apple Silicon Macs, but the script only checks for:
- "Linux x86_64"
- "Linux ia64"
- "Darwin i386"
- "Darwin x86_64"

**Solution**: Add a check for "Darwin arm64" that maps to "Darwin_x86_64" (to use Rosetta 2)

### NetMHCIIpan
The NetMHCIIpan executable is a tcsh shell script that calls underlying binaries. The binaries are Linux-only.

### SMM_align
Uses `netmhcii_11_executable` which has:
- `binaries_Linux_x86_64/` directory with Linux executables
- No macOS binaries

