# Ref Parser Concatenation Changes Required

## Summary
The ref parser needs to be updated to generate concatenated summary files like the query parser does.

## Required Changes

### 1. Filename Generation (line 168)
**Change from:**
```perl
my $outfile_fin = "$out_dir" . "Global_IEDB_out_" . "$locus" . "$cd8_type_8" . "\.---\.csv";
my $outfile_summary = "$out_dir" . "Summary_IEDB_" . "$locus" . "$cd8_type_8" . "\.---\.csv";
```

**Change to:**
```perl
my $outfile_fin = "$out_dir" . "Global_IEDB_out_anticancer_summary.csv";
my $outfile_summary = "$out_dir" . "Summary_IEDB_anticancer_summary.csv";
```

### 2. Header Writing Logic
**Change from:**
```perl
if ($flag_7==0){
```

**Change to:**
```perl
if (! -e $outfile_summary || -z $outfile_summary){
```

And for Global:
**Change from:**
```perl
print $fhout 'HLA genotype' ... if $flag_7 == 0;
```

**Change to:**
```perl
if (! -e $outfile_fin || -z $outfile_fin) {
    print $fhout 'HLA genotype' ...;
}
```

### 3. Add X-mer Column to Summary Header
**Change from:**
```perl
print $fhout2 'Peptide query', ",", 'HLA genotype', ",", 'Peptide', ",", "$ref1_name ref", ...
```

**Change to:**
```perl
print $fhout2 'Peptide query', ",", 'HLA genotype', ",", 'Peptide', ",", 'Epitope size (X-mer)', ",", "$ref1_name ref", ...
```

### 4. Add X-mer Tracking in peptide_stats
**Need to:**
- Set `$size_7 = $alignment_7->{$virus_7}->{$cd8_7}->{'Size'}->[0];` early in the loop
- Create `my $current_xmer = $size_7 . "-mer";`
- Add `'x_mer' => $current_xmer` to peptide_stats initialization
- Update `$peptide_stats{$peptide_method_key}->{'x_mer'} = $current_xmer;` after initialization

### 5. Add X-mer to Summary Output
**Change from:**
```perl
print $fh_out2 $virus_7, ",", $cd8_7, ",", $pep_data->{'peptide'}, ",", $pep_data->{'ref1_peptide'}, ...
```

**Change to:**
```perl
print $fh_out2 $virus_7, ",", $cd8_7, ",", $pep_data->{'peptide'}, ",", $pep_data->{'x_mer'}, ",", $pep_data->{'ref1_peptide'}, ...
```

### 6. Update file_clean to Filter Instead of Move
Replace the entire file_clean function to filter main files by size instead of moving them.

## Status
- [x] BASE_DIR updated
- [x] master_files updated
- [x] PERCENTILE_THRESHOLD updated
- [ ] Filename generation updated
- [ ] Header writing logic updated
- [ ] X-mer column added
- [ ] file_clean updated

