# cd4episcore Integration Assessment

## Overview
cd4episcore is an immunogenicity prediction method for CD4+ T cell epitopes. It uses a neural network model trained on tetramer data and outputs a normalized score (0-100) where lower scores indicate higher immunogenicity.

## Key Requirements

1. **Epitope Size**: Only works with 15-mer peptides (hardcoded in the code)
2. **Input Type**: Uses `type: "immunogenicity"` (not `type: "binding"`)
3. **Output Format**: Normalized score (0-100), not percentile
4. **Method**: `cd4episcore` (version 1.0)

## Integration Options

### Option A: Run binding methods first, then cd4episcore separately on filtered results
**Pros:**
- Can filter binding predictions before running immunogenicity
- Reduces computational load for cd4episcore
- More control over which peptides get immunogenicity scores

**Cons:**
- Requires two separate runs
- More complex workflow
- Need to manage intermediate files

**Implementation:** Would require running binding methods first, filtering results (e.g., by percentile threshold), then running cd4episcore on the filtered peptide list.

### Option B: Run binding + cd4episcore in same JSON (parallel execution) [RECOMMENDED]
**Pros:**
- Single execution pass
- All predictions available simultaneously
- Standard approach shown in examples
- Simpler workflow

**Cons:**
- cd4episcore runs on all 15-mers (can't filter first)
- May run predictions on peptides that won't be used

**Implementation:** Add cd4episcore to the predictors array in the same JSON, but only when length is 15:
```perl
if ($no == 15) {
    # Add cd4episcore to predictors array
    print $json_fh "    {\n";
    print $json_fh "      \"type\": \"immunogenicity\",\n";
    print $json_fh "      \"method\": \"cd4episcore\"\n";
    print $json_fh "    },\n";
}
```

### Option C: Two-step workflow (binding predictions → filter → cd4episcore on top candidates)
**Pros:**
- Most efficient use of computational resources
- Only run immunogenicity on promising candidates
- Can apply multiple filtering criteria

**Cons:**
- Most complex implementation
- Requires parsing intermediate results
- Multiple JSON files and method calls

**Implementation:** Would require:
1. Run binding methods for all lengths (15-20)
2. Parse and filter results (e.g., percentile < 10 for multiple methods)
3. Extract 15-mer peptides from filtered results
4. Run cd4episcore on filtered 15-mer list

## Current Perl Script Implementation

The current `iedb_alignment_run_v0-2.pl` script:
- Loops through lengths 15-20
- For each length, runs all binding methods
- Creates separate JSON files for each length/method combination

## Recommendation

**Option B (Parallel Execution)** is recommended because:
1. It's the standard approach shown in the example JSON files
2. Simplest to implement (just add cd4episcore to predictors when length == 15)
3. All results available in one execution
4. The workflow can filter results after all predictions are complete

## Implementation Notes

To implement Option B in the Perl script:
1. When `$no == 15`, add cd4episcore to the predictors array
2. Keep it in the same JSON as binding methods
3. The tcell_mhcii.py script will handle both binding and immunogenicity predictions in one call

Example JSON structure for length 15:
```json
{
  "input_sequence_text_file_path": "/path/to/file.fa",
  "peptide_length_range": [15, 15],
  "alleles": "DRB1*01:01",
  "predictors": [
    {"type": "binding", "method": "netmhciipan_el"},
    {"type": "binding", "method": "netmhciipan_ba"},
    {"type": "binding", "method": "nn_align"},
    {"type": "binding", "method": "smm_align"},
    {"type": "binding", "method": "tepitope"},
    {"type": "binding", "method": "comblib"},
    {"type": "immunogenicity", "method": "cd4episcore"}
  ]
}
```

## Testing Recommendations

1. Test cd4episcore standalone with a simple 15-mer peptide
2. Test combined JSON with binding + cd4episcore
3. Verify output format (Imm_score 0-100)
4. Confirm it only processes 15-mers when length range is [15, 15]

