# CD4+ Epitope Scoring Thresholds and Criteria

## Method Outputs and CD4+ Epitope Criteria

### 1. Binding Methods Outputs

**NetMHCIIpan (EL/BA), NN_align, SMM_align, TEPITOPE, Comblib:**

| Output Column | Description | Methods Using This Output |
|---------------|-------------|---------------------------|
| `binding.score` | Raw elution likelihood score | **NetMHCIIpan_EL** (all versions), **TEPITOPE**, **Comblib** |
| `binding.ic50` | Predicted IC50 (nM)<br>Lower = stronger binding | **NetMHCIIpan_BA** (all versions), **NN_align**, **SMM_align** |
| `binding.percentile` | Percentile rank (0-100)<br>Calculated by comparing the peptide's IC50/score against those of a set of random peptides from SWISSPROT database<br>Lower = better binding | **ALL methods** (NetMHCIIpan_EL, NetMHCIIpan_BA, NN_align, SMM_align, TEPITOPE, Comblib) |
| `binding.adjusted_percentile` | Length-adjusted percentile<br>The percentile rank adjusted based on the frequency of peptide lengths | **NN_align, SMM_align, TEPITOPE, Comblib**<br>(NOT NetMHCIIpan_EL/BA) |
| `binding.core` | 9-mer core sequence | All methods |
| `binding.median_percentile` | Median across methods/alleles | Consensus methods |
| `binding.global_median_percentile` | Global median across all | Aggregated results |

**Method Output Summary:**
- **NetMHCIIpan_EL**: `score` + `percentile` (no adjusted_percentile)
- **NetMHCIIpan_BA**: `ic50` + `percentile` (no adjusted_percentile)
- **NN_align**: `ic50` + `percentile` + `adjusted_percentile`
- **SMM_align**: `ic50` + `percentile` + `adjusted_percentile`
- **TEPITOPE**: `score` + `percentile` + `adjusted_percentile`
- **Comblib**: `score` + `percentile` + `adjusted_percentile`

**Note:** Based on code implementation, prediction methods return scores/IC50 values directly, and percentiles are calculated from those scores using percentile lookup tables. The output format shows score/IC50 followed by percentile_rank.

**Key Binding Criteria:**
- **Percentile rank < 10**: Strong binder
- **Percentile rank 10-20**: Moderate binder  
- **Percentile rank > 20**: Weak/non-binder

### 2. Immunogenicity Method (cd4episcore) Outputs

| Output Column | Description | Interpretation |
|---------------|-------------|----------------|
| `immunogenicity.cd4episcore.score` | Immunogenicity score (0-100) | **Lower = more immunogenic**<br>0 = most immunogenic, 100 = least |
| `immunogenicity.cd4episcore.core` | 9-mer core used by NN model | Core peptide sequence |
| `immunogenicity.cd4episcore.combined_score` | Combined binding + immunogenicity | **Lower = better CD4+ epitope**<br>Formula: `(0.4 × immunogenicity_score) + (0.6 × binding_percentile)` |

**Key Immunogenicity Criteria:**
- **Score < 20**: Highly immunogenic
- **Score 20-50**: Moderately immunogenic
- **Score > 50**: Low immunogenicity

### 3. Processing Method (MHCII-NP) Outputs

| Output Column | Description | Interpretation |
|---------------|-------------|----------------|
| `processing.mhciinp.cleavage_probability_score` | Cleavage probability score | **Higher = better processing** |
| `processing.mhciinp.cleavage_probability_percentile_rank` | Percentile rank (0-100) | **Lower = better processing** |
| `processing.mhciinp.n_motif` | N-terminus cleavage motif | Cleavage site information |
| `processing.mhciinp.c_motif` | C-terminus cleavage motif | Cleavage site information |

### 4. Criteria for a Robust CD4+ Epitope

A robust CD4+ epitope should meet the following criteria:

#### Primary Criteria:
1. **Strong MHC Binding:**
   - `binding.global_median_percentile` < 10 (ideally < 5)
   - `binding.ic50` < 1000 nM (ideally < 500 nM)

2. **High Immunogenicity:**
   - `immunogenicity.cd4episcore.score` < 30 (ideally < 20)
   - Lower score indicates better TCR recognition

3. **Combined Score:**
   - `immunogenicity.cd4episcore.combined_score` < 15 (ideally < 10)
   - Combines binding (60% weight) + immunogenicity (40% weight)
   - Lower = higher capacity for TCR recognition

#### Secondary Criteria (optional but recommended):
4. **Good Antigen Processing:**
   - `processing.mhciinp.cleavage_probability_percentile_rank` < 20
   - Higher cleavage probability increases likelihood of being presented

5. **Consensus Across Methods:**
   - `binding.median_percentile` < 10 across multiple binding methods
   - Consistent predictions increase confidence

### 5. Recommended Workflow for Identifying Robust CD4+ Epitopes

1. **Run binding predictions** (NetMHCIIpan_EL, NetMHCIIpan_BA, NN_align, SMM_align)
2. **Filter**: `binding.global_median_percentile` < 10
3. **Run cd4episcore** on filtered peptides
4. **Filter**: `immunogenicity.cd4episcore.score` < 30
5. **Calculate combined score** (if both binding and immunogenicity are available)
6. **Final ranking**: Sort by `immunogenicity.cd4episcore.combined_score` (ascending)

**Top-tier Epitopes:**
- `binding.global_median_percentile` < 5
- `immunogenicity.cd4episcore.score` < 20
- `immunogenicity.cd4episcore.combined_score` < 10

### Example Output Structure

```tsv
sequence_number  peptide              allele      start  end  binding.global_median_percentile  immunogenicity.cd4episcore.score  immunogenicity.cd4episcore.combined_score  core
1                MGQIVTMFEALPHII      DRB1*01:01   1      15   3.5                            15.2                               8.7                                    TMFEALPHI
```

---

## Summary

The **combined score** (`immunogenicity.cd4episcore.combined_score`) is the most informative single metric for CD4+ epitope prediction, as it integrates both MHC binding strength and TCR recognition capacity. Lower values indicate better CD4+ epitope candidates.

**Quick Reference Thresholds:**
- **Strong binding**: Percentile < 10
- **High immunogenicity**: Score < 20
- **Robust epitope**: Combined score < 10
- **Top-tier**: Combined score < 5

