# Wrapper Alignment Issues Analysis

## 1. Does `iedb_run-cmd_wrapper.py` read parameters from `params/`?

**Answer: NO**

The wrapper does NOT read from `params/CD_type.dat` or `params/length.dat`. These are read by the Perl scripts:
- `iedb_alignment_run_v0-2.pl` reads `params/CD_type.dat` and `params/length.dat`
- `iedb_output_parse_v0-51.pl` reads `params/CD_type.dat` and `params/length.dat`
- `iedb_output_ref-parse_v0-12.pl` reads `params/CD_type.dat` and `params/length.dat`

**Issue**: The wrapper hardcodes `percentile_threshold="2.5"` and doesn't validate that params files exist or are consistent.

## 2. Percentile vs Adjusted Percentile Threshold Mismatch

**Critical Issue Found:**

The wrapper passes `percentile_threshold="2.5"` to `iedb_output_parse_v0-51.pl` as ARGV[1], which sets `$PERCENTILE_THRESHOLD`.

However, in `v0-51.pl`:
- **Homology mode** (line 381): Filters by `percentile <= $PERCENTILE_THRESHOLD` ✓ (correct)
- **Relaxed mode** (line 864-874): Filters by `adjusted_percentile <= 2.5` ✗ (hardcoded, ignores CLI threshold!)

**Problem**: The relaxed mode uses a hardcoded `2.5` instead of using the CLI-provided threshold for `adjusted_percentile` filtering.

**Impact**: 
- If wrapper passes `percentile_threshold="10.0"`, homology mode will use 10.0, but relaxed mode will still use hardcoded 2.5
- The threshold should be configurable for both modes

## 3. Alignment Issues Summary

### Path Alignment
- ✓ BASE_DIR is passed correctly via environment variable
- ✓ Perl scripts read from `$ENV{'BASE_DIR'}` or default
- ✓ Data directory paths align (`data/`)
- ✓ Output directory structure is correct

### Parameter Alignment
- ✓ Wrapper now validates `params/CD_type.dat` exists - FIXED
- ✓ Wrapper now validates `params/length.dat` exists and format - FIXED
- Note: Wrapper still doesn't read params (Perl scripts do), but validates they exist
- Note: Percentile threshold is still hardcoded in wrapper (could read from params file in future)

### Threshold Alignment
- ✓ Homology mode uses `PERCENTILE_THRESHOLD` (percentile) - correct
- ✓ Relaxed mode now uses `$PERCENTILE_THRESHOLD` (adjusted_percentile) - FIXED (was hardcoded 2.5)
- Note: Both modes use the same CLI threshold; if different thresholds needed, would require separate CLI args

### File Path Alignment
- ✓ `iedb_alignment_run_v0-2.pl` reads from `data/` correctly
- ✓ Parsers read from correct input directories
- ✓ Output directories are correctly structured

## Fixes Applied

1. ✅ **Added params validation**: Wrapper now validates that `params/CD_type.dat` and `params/length.dat` exist before running
2. ✅ **Fixed relaxed mode threshold**: Updated `v0-51.pl` line 871 to use `$PERCENTILE_THRESHOLD` instead of hardcoded `2.5`
3. ✅ **Added documentation**: Comments clarify that Perl scripts read params, wrapper validates

## Remaining Considerations

1. **Optional enhancement**: Wrapper could read percentile threshold from params file instead of hardcoding
2. **Optional enhancement**: Could add separate thresholds for percentile vs adjusted_percentile if needed

