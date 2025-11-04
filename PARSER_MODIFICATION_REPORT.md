# Parser Modification Report: Class I to Class II TSV Format Adaptation

## Executive Summary

The parser `iedb_output_parse_v0-5.pl` has been partially adapted for Class II MHC predictions, but there are critical issues preventing proper parsing of Class II TSV output files. The primary issue is that **Class II TSV files contain explicit `start` and `end` position fields** (columns 3 and 4), but the current parser **ignores these fields and uses `index()` search instead**, which is inefficient and error-prone. Additionally, the parser should use the `peptide_length` field (column 5) instead of calculating it from the peptide string length.

### Key Differences

| Aspect | Class I | Class II |
|--------|--------|----------|
| **Column Count** | 4 columns | 10 columns |
| **Peptide Location** | Derived via `index()` search | Provided explicitly (start/end fields) |
| **Score Field** | Column 3 (ic50 or score) | Column 8 (score) |
| **Percentile Field** | Column 4 | Column 9 |
| **Additional Fields** | None | seq_num, start, end, peptide_length, core, adjusted_percentile |
| **Methods** | smm, ann, comblib | tepitope, comblib |

### Critical Modifications Required

1. **Use explicit start/end fields** from Class II TSV instead of `index()` search
2. **Use peptide_length field** instead of calculating from peptide string
3. **Verify method detection** works correctly for tepitope
4. **Ensure TEPITOPE array initialization** occurs before use

---

## Format Comparison Table

### Class I TSV Format

**Columns (4 total):**
1. `allele` - HLA allele (e.g., `HLA-A*02:01`)
2. `peptide` - Peptide sequence (8-10 amino acids)
3. `ic50` or `score` - Binding score (ANN/SMM use ic50, Comblib uses score)
4. `percentile` - Percentile rank

**Example (ANN method):**
```
allele	peptide	ic50	percentile
HLA-A*02:01	SSRAGLQFPV	411.6043917835677	4
```

**Example (Comblib method):**
```
allele	peptide	score	percentile
HLA-A*02:01	SRAGLQFPV	2.5026493257310773e-05	1.5
```

### Class II TSV Format

**Columns (10 total):**
1. `allele` - HLA allele (e.g., `HLA-DRB1*01:01`)
2. `seq_num` - Sequence number (typically 1)
3. `start` - Starting position in sequence (1-based)
4. `end` - Ending position in sequence (1-based)
5. `peptide_length` - Length of peptide (typically 15 for Class II)
6. `core` - 9-mer core binding region
7. `peptide` - Full peptide sequence (15-30 amino acids)
8. `score` - Binding score (always uses "score", not "ic50")
9. `percentile` - Percentile rank
10. `adjusted_percentile` - Adjusted percentile rank

**Example (TEPITOPE method):**
```
allele	seq_num	start	end	peptide_length	core	peptide	score	percentile	adjusted_percentile
HLA-DRB1*01:01	1	1	15	15	FVFLVLLPL	MFVFLVLLPLVSSQC	2.6	0.97	0.97
```

**Example (Comblib method):**
```
allele	seq_num	start	end	peptide_length	core	peptide	score	percentile	adjusted_percentile
HLA-DRB1*01:01	1	1	15	15	FLVLLPLVS	MFVFLVLLPLVSSQC	0.01	0.01	0.01
```

### Field Mapping

| Class I Column | Class II Column | Notes |
|----------------|-----------------|-------|
| 1: allele | 1: allele | Same |
| 2: peptide | 7: peptide | Different position |
| 3: ic50/score | 8: score | Different position, always "score" in Class II |
| 4: percentile | 9: percentile | Different position |
| N/A | 2: seq_num | New in Class II |
| N/A | 3: start | **NEW - Use this instead of index() search** |
| N/A | 4: end | **NEW - Use this instead of index() search** |
| N/A | 5: peptide_length | **NEW - Use this instead of length($peptide)** |
| N/A | 6: core | New in Class II (9-mer core) |
| N/A | 10: adjusted_percentile | New in Class II (currently unused) |

---

## Parser Code Analysis

### Current Implementation Status

The Class II parser at `/Users/michael_gaunt/Desktop/Anastasia2/vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-5.pl` has been partially updated:

#### ✅ Correctly Implemented

1. **Format Detection** (lines 354-356):
   ```perl
   my $is_class_ii = ($header2 =~ /\tseq_num\t/ || $header2 =~ /\tpeptide_length\t/ || $header2 =~ /\tcore\t/);
   ```
   - Correctly detects Class II format by checking for unique columns

2. **Column Parsing** (lines 365-376):
   ```perl
   if ($is_class_ii) {
       my @fields = split("\t", $results);
       next unless scalar(@fields) >= 9;
       $allele_check = $fields[0];
       $peptide = $fields[6];      # Correct
       $score_or_ic50 = $fields[7]; # Correct
       $percentile = $fields[8];    # Correct
   }
   ```
   - Correctly extracts peptide, score, and percentile from Class II columns

3. **Method Detection** (lines 380-391):
   ```perl
   if ($file =~ /_tepitope\.csv\.tsv$/) {
       $method = 'tepitope';
   } elsif ($file =~ /_comblib.*\.csv\.tsv$/) {
       $method = 'comblib';
   }
   ```
   - Correctly detects tepitope and comblib methods

4. **TEPITOPE Array Initialization** (lines 445-453):
   ```perl
   unless (exists $alignment_2->{$virus_2}->{$cd8_2}->{'TEPITOPE'}) {
       $alignment_2->{$virus_2}->{$cd8_2}->{'TEPITOPE'} = [];
   }
   push (@{$alignment_2->{$virus_2}->{$cd8_2}->{'TEPITOPE'}}, $tepitope_val);
   ```
   - Correctly initializes and stores TEPITOPE scores

#### ❌ Critical Issues

1. **Peptide Location Extraction** (lines 419-429):
   ```perl
   # CURRENT CODE (WRONG for Class II):
   my $epi_size = length($peptide);
   my $target_protein = $alignment_2->{$virus_2}->{'protein'};
   my $epi_loc_begin = index($target_protein, $peptide) + 1;  # Uses index() search
   $epi_loc_begin = 1 if $epi_loc_begin == 0;  # Fallback
   my $epi_loc_end = $epi_loc_begin + $epi_size - 1;
   ```
   
   **Problem**: Class II TSV files already contain explicit `start` and `end` positions in columns 3 and 4, but the parser ignores them and uses inefficient `index()` string search instead.
   
   **Impact**: 
   - Inefficient (unnecessary string search)
   - Potentially incorrect if peptide appears multiple times in sequence
   - Ignores the explicit location data provided by the prediction tool

2. **Peptide Length Extraction** (line 420):
   ```perl
   # CURRENT CODE:
   my $epi_size = length($peptide);
   ```
   
   **Problem**: Class II TSV files contain a `peptide_length` field in column 5, but the parser calculates it from the peptide string instead.
   
   **Impact**: 
   - Minor inefficiency
   - Should use explicit field for consistency

### Comparison with Class I Parser

**Class I Parser** (`/Users/michael_gaunt/Desktop/Anastasia/vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl`):

- Lines 403-413: Uses `index()` search because Class I TSV doesn't provide location fields
- This is correct for Class I, but should be replaced for Class II

**Class II Parser** (current implementation):

- Lines 419-429: Uses `index()` search even though Class II TSV provides explicit location
- This is incorrect and should use the `start` and `end` fields from columns 3 and 4

---

## Required Modifications

### Modification 1: Use Explicit Start/End Fields for Class II

**Location**: Lines 419-429 in `/Users/michael_gaunt/Desktop/Anastasia2/vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-5.pl`

**Current Code:**
```perl
# Extract peptide length and location (find position in target protein sequence)
my $epi_size = length($peptide);
# Check if virus exists in alignment and has protein sequence
unless (exists $alignment_2->{$virus_2} && exists $alignment_2->{$virus_2}->{'protein'}) {
    warn "Warning: Virus $virus_2 not found in alignment for peptide $peptide - skipping\n";
    next;
}
my $target_protein = $alignment_2->{$virus_2}->{'protein'};
my $epi_loc_begin = index($target_protein, $peptide) + 1;  # 1-based position
$epi_loc_begin = 1 if $epi_loc_begin == 0;  # Fallback if not found
my $epi_loc_end = $epi_loc_begin + $epi_size - 1;
```

**Required Change:**
```perl
# Extract peptide length and location
# For Class II, use explicit start/end fields from TSV
# For Class I, use index() search (backward compatibility)
my $epi_size;
my $epi_loc_begin;
my $epi_loc_end;

if ($is_class_ii) {
    # Class II: Use explicit fields from TSV (columns 3, 4, 5)
    $epi_loc_begin = $fields[2];      # start (column 3, 0-based index 2)
    $epi_loc_end = $fields[3];        # end (column 4, 0-based index 3)
    $epi_size = $fields[4];           # peptide_length (column 5, 0-based index 4)
    
    # Validate that fields are numeric
    unless ($epi_loc_begin =~ /^\d+$/ && $epi_loc_end =~ /^\d+$/ && $epi_size =~ /^\d+$/) {
        warn "Warning: Invalid start/end/length fields for peptide $peptide - skipping\n";
        next;
    }
} else {
    # Class I: Use index() search (original behavior)
    $epi_size = length($peptide);
    unless (exists $alignment_2->{$virus_2} && exists $alignment_2->{$virus_2}->{'protein'}) {
        warn "Warning: Virus $virus_2 not found in alignment for peptide $peptide - skipping\n";
        next;
    }
    my $target_protein = $alignment_2->{$virus_2}->{'protein'};
    $epi_loc_begin = index($target_protein, $peptide) + 1;  # 1-based position
    $epi_loc_begin = 1 if $epi_loc_begin == 0;  # Fallback if not found
    $epi_loc_end = $epi_loc_begin + $epi_size - 1;
}
```

**Rationale:**
- Class II TSV files explicitly provide location information that should be used
- Avoids potential errors from string matching
- More efficient (no string search needed)
- Maintains backward compatibility with Class I format

### Modification 2: Ensure Fields Array is Available

**Location**: The `@fields` array is only created in the Class II parsing block (line 367), so it needs to be accessible in the location extraction section.

**Current Structure:**
The `@fields` array is scoped within the `if ($is_class_ii)` block (lines 365-376), but needs to be accessible later for location extraction.

**Required Change:**
Move the `@fields` array declaration outside the conditional, or ensure it's available when needed:

```perl
# Parse TSV format based on Class I vs Class II
my ($allele_check, $peptide, $score_or_ic50, $percentile);
my @fields = ();  # Initialize outside conditional
if ($is_class_ii) {
    # Class II format: allele, seq_num, start, end, peptide_length, core, peptide, score, percentile, adjusted_percentile
    @fields = split("\t", $results);
    next unless scalar(@fields) >= 9;  # Need at least 9 columns
    $allele_check = $fields[0];
    $peptide = $fields[6];  # peptide is 7th column (index 6)
    $score_or_ic50 = $fields[7];  # score is 8th column (index 7)
    $percentile = $fields[8];  # percentile is 9th column (index 8)
} else {
    # Class I format: allele, peptide, score/ic50, percentile
    ($allele_check, $peptide, $score_or_ic50, $percentile) = split("\t", $results);
}
```

This ensures `@fields` is available for the location extraction code later.

---

## Testing Approach

### Test Cases

1. **Class II TSV Parsing Test**:
   - Input: `YAI81105_de__HLA-DRB1+01:01.15_tepitope.csv.tsv`
   - Verify: `epi_loc_begin` matches `start` field (column 3)
   - Verify: `epi_loc_end` matches `end` field (column 4)
   - Verify: `epi_size` matches `peptide_length` field (column 5)

2. **Class II Comblib Test**:
   - Input: `YAI81105_de__HLA-DRB1+01:01.15_comblib.csv.tsv`
   - Verify: Same location extraction works for Comblib method

3. **Backward Compatibility Test**:
   - Input: Class I TSV file (e.g., `Buforin_II__HLA-A+02:01.10_ann.csv.tsv`)
   - Verify: `index()` search still works for Class I format

4. **Edge Cases**:
   - Test with peptides that appear multiple times in sequence
   - Test with peptides at sequence boundaries (start=1, end=15)
   - Test with invalid start/end values (should skip with warning)

### Validation Steps

1. **Run parser on Class II TSV files**:
   ```bash
   cd /Users/michael_gaunt/Desktop/Anastasia2
   export BASE_DIR=/Users/michael_gaunt/Desktop/Anastasia2
   perl vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-5.pl parsed_output 10.0 0.0
   ```

2. **Verify output files contain data**:
   - Check `parsed_output/homology_output/Global_IEDB_out_anticancer_summary.15.csv`
   - Check `parsed_output/percentile_output/Global_IEDB_out_anticancer_summary.15.csv`
   - Verify rows are present (not just headers)

3. **Verify location accuracy**:
   - Compare `Epitope loc.` column in output with `start` field from input TSV
   - Should match exactly for Class II predictions

4. **Verify peptide length**:
   - Compare `Epitope size` column with `peptide_length` field from input TSV
   - Should match exactly for Class II predictions

---

## Recommendations

### Priority 1 (Critical)

1. **Implement Modification 1**: Use explicit start/end fields for Class II
   - This is the primary issue preventing correct parsing
   - Will improve accuracy and efficiency

2. **Implement Modification 2**: Ensure `@fields` array is accessible
   - Required for Modification 1 to work

### Priority 2 (Important)

3. **Add validation** for start/end/length fields
   - Ensure fields are numeric
   - Ensure end >= start
   - Ensure length matches end - start + 1

4. **Add logging** for debugging
   - Log when using explicit fields vs index() search
   - Log when fields are invalid and peptide is skipped

### Priority 3 (Nice to Have)

5. **Consider using adjusted_percentile** field (column 10)
   - Currently unused, but may be useful for filtering

6. **Consider storing core field** (column 6)
   - 9-mer core binding region may be useful for analysis

---

## Summary

The Class II parser has been partially adapted but has a **critical bug**: it ignores the explicit `start` and `end` position fields provided in Class II TSV files and uses inefficient `index()` string search instead. This should be fixed by:

1. Using `$fields[2]` (start) and `$fields[3]` (end) for location
2. Using `$fields[4]` (peptide_length) for size
3. Maintaining backward compatibility with Class I format

Once these modifications are implemented, the parser should correctly process Class II TSV files and generate output with accurate epitope locations.

