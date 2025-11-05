# Input Directory Conflict Analysis

## Critical Issue Identified

### Current State

1. **`iedb_output_parse_v0-51.pl` (query parser)**:
   - Hardcoded `master_files`: `/dev_test_out-pl/` → `anticancer_test-combined.csv` (line 50-51)
   - Uses: `$iedb_out = $here . $directory;` where `$directory` comes from `master_files` keys (line 159)
   - **Result**: Reads from `$BASE_DIR/dev_test_out-pl/` (hardcoded path)
   - **Wrapper fix**: Creates temp file replacing `/dev_test_out-pl/` with `query_input_dir` ✓

2. **`iedb_output_ref-parse_v0-12.pl` (ref parser)**:
   - Hardcoded `master_files`: `/dev_test_out-pl/` → `anticancer_test-combined.csv` (line 33-34)
   - Uses: `$iedb_out = $CLI_INPUT_DIR;` (line 134) - **IGNORES master_files!**
   - **Result**: Reads from `CLI_INPUT_DIR` (ARGV[1]) ✓

3. **Wrapper behavior**:
   - `iedb_alignment_run_v0-2.pl` outputs to:
     - Reference run → `ref_output/`
     - Query run → `query_output/`
   - Both parsers should read from their respective directories

### The Problem

**CONFIRMED**: Both parsers have hardcoded `/dev_test_out-pl/` in `master_files`, but:
- **v0-51.pl**: Uses `master_files` keys → reads from hardcoded `/dev_test_out-pl/` (unless temp file modifies it)
- **v0-12.pl**: **IGNORES** `master_files` and uses `CLI_INPUT_DIR` ✓ (correct)

However, **v0-51.pl** still has `master_files` hardcoded, and the temp file modification might not be reliable.

### Actual Flow

1. **Reference run**: 
   - `iedb_alignment_run_v0-2.pl` outputs TSV files to `ref_output/`
   - `iedb_output_ref-parse_v0-12.pl` reads from `CLI_INPUT_DIR` = `ref_output` ✓

2. **Query run**:
   - `iedb_alignment_run_v0-2.pl` outputs TSV files to `query_output/`
   - `iedb_output_parse_v0-51.pl` reads from `master_files` key = `/dev_test_out-pl/` ✗ (WRONG!)
   - Wrapper creates temp file to fix this ✓

### Potential Issues

1. **Temp file approach for v0-51.pl**:
   - If temp file cleanup fails, old version might be used
   - If multiple runs happen, temp file might conflict

2. **`dev_test_out-pl/` directory**:
   - Contains old test outputs (12 TSV files found)
   - If v0-51.pl temp file fix fails, it would read from wrong directory
   - Could cause query parser to read ref data or vice versa

### Recommendation

**Option 1**: Make v0-51.pl use CLI_INPUT_DIR like v0-12.pl (most robust)
**Option 2**: Ensure temp file modification is reliable and add cleanup
**Option 3**: Remove `dev_test_out-pl/` directory or ensure it's not used

