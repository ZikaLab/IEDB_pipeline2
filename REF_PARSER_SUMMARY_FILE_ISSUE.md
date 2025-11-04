# Ref Parser Summary File Issue Analysis

## Problem
`iedb_output_ref-parse_v0-11.pl` does not produce final concatenated summary files like `Summary_IEDB_anticancer_summary.csv` and `Global_IEDB_out_anticancer_summary.csv` that are produced by `iedb_output_parse_v0-51.pl`.

## Root Cause Analysis

### 1. File Naming Differences

**`iedb_output_parse_v0-51.pl` (Query Parser):**
- Uses **hardcoded** filenames:
  - `Summary_IEDB_anticancer_summary.csv` (line 818)
  - `Global_IEDB_out_anticancer_summary.csv` (line 816)
- Writes directly to these stable filenames (no size suffix)
- Files accumulate all sizes in the same files
- Size-specific files are created later in `file_clean` by filtering

**`iedb_output_ref-parse_v0-11.pl` (Ref Parser):**
- Uses **dynamic** filenames based on `$locus` variable:
  - `Summary_IEDB_{$locus}_{$cd8_type}.---.csv` (line 168)
  - `Global_IEDB_out_{$locus}_{$cd8_type}.---.csv` (line 168)
- Where:
  - `$locus` = alignment file name without extension (e.g., `anticancer_test-combined`)
  - `$cd8_type` = `anticancer_test` (becomes `anticancer_test` after transformation)
- Result: `Summary_IEDB_anticancer_test-combined_anticancer_test.---.csv`
- The `---` placeholder is replaced with size in `file_clean` (line 187)
- Files are moved to `outfile_store/` directory
- **No final concatenated file is created**

### 2. Wrapper Expectations

**`iedb_run-cmd_v0-2.py` expects:**
- `_concatenate_ref_outputs()` function (lines 124-189) looks for:
  - `Summary_IEDB_anticancer_test-ref_anticancer_test.{8,9,10}.csv`
  - `Global_IEDB_out_anticancer_test-ref_anticancer_test.{8,9,10}.csv`
- **Issues:**
  1. Expects `anticancer_test-ref` but ref parser generates `anticancer_test-combined`
  2. Hardcoded for Class I lengths (8, 9, 10) but Class II uses (15, 16)
  3. Expects concatenated files to be created, but ref parser only creates size-specific files

### 3. Current Output Structure

**Ref Parser Output (`ref_test/outfile_store/`):**
```
Summary_IEDB_anticancer_test-combined_anticancer_test.15.csv
Summary_IEDB_anticancer_test-combined_anticancer_test.16.csv
Global_IEDB_out_anticancer_test-combined_anticancer_test.15.csv
Global_IEDB_out_anticancer_test-combined_anticancer_test.16.csv
Sum_totals_IEDB_anticancer_test-combined_anticancer_test.15.csv
Sum_totals_IEDB_anticancer_test-combined_anticancer_test.16.csv
```

**Query Parser Output (`parsed_output/homology_output/`):**
```
Summary_IEDB_anticancer_summary.csv         # ← Final concatenated file
Summary_IEDB_anticancer_summary.15.csv      # ← Size-specific
Summary_IEDB_anticancer_summary.16.csv      # ← Size-specific
Global_IEDB_out_anticancer_summary.csv      # ← Final concatenated file
Global_IEDB_out_anticancer_summary.15.csv  # ← Size-specific
Global_IEDB_out_anticancer_summary.16.csv  # ← Size-specific
```

## Solution Options

### Option 1: Modify Ref Parser to Match Query Parser Pattern
- Change `iedb_output_ref-parse_v0-11.pl` to use hardcoded filenames like query parser
- Write directly to `Summary_IEDB_anticancer_summary.csv` and `Global_IEDB_out_anticancer_summary.csv`
- Create size-specific files in `file_clean` by filtering the main files

### Option 2: Update Wrapper to Handle Ref Parser Output
- Modify `_concatenate_ref_outputs()` in `iedb_run-cmd_v0-2.py` to:
  1. Detect actual file patterns (support `anticancer_test-combined` or `anticancer_test-ref`)
  2. Support Class II lengths (15, 16) in addition to Class I (8, 9, 10)
  3. Concatenate size-specific files into final summary files

### Option 3: Hybrid Approach
- Modify ref parser to create concatenated files similar to query parser
- Update wrapper to support both patterns for backward compatibility

## Recommendation

**Option 1** is recommended because:
1. Consistency: Both parsers would use the same output pattern
2. Simplicity: Single stable filename for all sizes
3. Compatibility: Query parser already works this way
4. Maintainability: Less special-case logic needed

## Implementation Notes

If choosing Option 1, the ref parser needs:
1. Change filename generation in `iedb_printout` (line 168) to use hardcoded names:
   - `Summary_IEDB_anticancer_summary.csv`
   - `Global_IEDB_out_anticancer_summary.csv`
2. Modify `file_clean` (line 187) to:
   - Filter the main files by size to create size-specific versions
   - Similar to how `iedb_output_parse_v0-51.pl` does it (lines 1155-1194)

