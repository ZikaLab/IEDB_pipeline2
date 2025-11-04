# Anastasia2 - MHC Class II Epitope Prediction Workflow

## Overview

Anastasia2 is an adaptation of the Anastasia Class I MHC workflow for **MHC Class II** epitope prediction. This workflow integrates the IEDB Next-Generation Tools T Cell Class II package (`ng_tc2-0.2.2-beta`) to predict CD4+ T cell epitopes.

## Key Features

- **Class II MHC prediction** using multiple binding methods (NetMHCIIpan EL/BA, NN_align, SMM_align, TEPITOPE, Comblib)
- **Immunogenicity scoring** using CD4episcore
- **Antigen processing prediction** using MHCII-NP
- **Homology filtering** against reference sequences
- **Comprehensive output parsing** with percentile-based filtering

## Workflow Components

### Main Scripts

- **`iedb_run-cmd_wrapper.py`** - Main Python wrapper that orchestrates the workflow
- **`vendor/ng_tc2-0.2.2-beta/iedb_alignment_run_v0-2.pl`** - Perl script for running IEDB predictions
- **`vendor/ng_tc2-0.2.2-beta/iedb_output_parse_v0-51.pl`** - Query output parser
- **`vendor/ng_tc2-0.2.2-beta/iedb_output_ref-parse_v0-12.pl`** - Reference output parser (homology filtering)

### Configuration

- **`params/CD_type.dat`** - HLA allele list (e.g., `HLA-DRB1*01:01`)
- **`params/length.dat`** - Peptide length range (e.g., `15, 20`)

### Output Structure

- **`dev_test_out-pl/`** - Raw IEDB prediction outputs
- **`parsed_output/`** - Parsed query outputs
- **`ref_test/outfile_store/`** - Parsed reference outputs with homology filtering

## Key Differences from Class I

| Aspect | Class I | Class II |
|--------|---------|----------|
| **Allele format** | `HLA-A*01:01` | `HLA-DRB1*01:01` |
| **Peptide lengths** | 8-10 mers | 15-30 mers (default: 15-20) |
| **Core region** | N/A | 9-mer core within longer peptides |
| **Threshold** | Percentile ≤ 2.5 | Adjusted Percentile ≤ 90.0 |

## Usage

### Basic Workflow

1. Place input sequences in `data/` directory (CSV format: `sequence_name,sequence`)
2. Configure alleles in `params/CD_type.dat`
3. Configure length range in `params/length.dat`
4. Run the workflow:
   ```bash
   python3 iedb_run-cmd_wrapper.py
   ```

### Reference Parser (Homology Filtering)

The reference parser filters epitopes based on homology to reference sequences:

```bash
perl vendor/ng_tc2-0.2.2-beta/iedb_output_ref-parse_v0-12.pl \
    ref_test dev_test_out-pl
```

**Key parameters:**
- Adjusted percentile threshold: **90.0** (configured in script)
- Filters epitopes with adjusted_percentile ≤ 90.0
- Outputs concatenated and size-specific summary files

## Output Files

### Summary Files
- `Summary_IEDB_anticancer_summary.csv` - Concatenated summary (all sizes)
- `Summary_IEDB_anticancer_summary.15.csv` - 15-mer specific
- `Summary_IEDB_anticancer_summary.16.csv` - 16-mer specific

### Global Files
- `Global_IEDB_out_anticancer_summary.csv` - Detailed epitope data

### Statistics Files
- `Sum_totals_IEDB_anticancer_summary.15.csv` - Summary statistics by size

## Method Outputs

### Binding Methods
- **Comblib Score** - Binding score from combinatorial library method
- **TEPITOPE Score** - Binding score from TEPITOPE method
- **Percentile** - Binding percentile rank
- **Adjusted Percentile** - Adjusted percentile rank (used for filtering)

### Supported Methods (macOS compatible)
- ✅ **TEPITOPE** - Pure Python implementation
- ✅ **Comblib** - Pure Python implementation
- ❌ **cd4episcore** - Linux binary only (not compatible with macOS ARM64)
- ❌ **NetMHCIIpan EL/BA** - Linux binary only
- ❌ **NN_align, SMM_align** - Linux binary only

## Requirements

- Python 3.8+
- Perl 5.x
- macOS (current testing) or Linux (for full binary support)
- IEDB ng_tc2-0.2.2-beta package

## Version History

- **v0-12** - Reference parser with adjusted percentile threshold (90.0), concatenated output support
- **v0-51** - Query parser with Class II TSV format support
- **v0-2** - Initial Class II adaptation from Class I workflow

## Notes

- The workflow is tested on macOS but some methods require Linux binaries
- Reference parser uses `adjusted_percentile ≤ 90.0` for filtering
- All output files are organized in `outfile_store/` subdirectories
- Concatenated files contain all peptide sizes, size-specific files are filtered

## Author

Michael W. Gaunt, Ph.D

## License

See original IEDB package license for `ng_tc2-0.2.2-beta` components.

