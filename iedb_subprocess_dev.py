#!/usr/bin/env python3
"""
IEDB Subprocess Development Wrapper
=====================================
This script wraps the IEDB tcell_mhci.py predictions by:
1. Reading FASTA files (full protein sequences)
2. Extracting all 9-mer peptides from each sequence
3. Converting to JSON format
4. Calling IEDB via subprocess
5. Saving separate CSV outputs for each FASTA file
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import tempfile

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Path to IEDB Python script
IEDB_SCRIPT = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py"

# Input FASTA files to process
INPUT_FASTA_FILES = [
    "/Users/michael_gaunt/Desktop/Anastasia/test_output/fa_tmp/Cathelicidin-BF.fa",
    "/Users/michael_gaunt/Desktop/Anastasia/test_output/fa_tmp/Buforin_II.fa"
]

# Output directory for results
OUTPUT_DIR = "/Users/michael_gaunt/Desktop/Anastasia/dev_test_out"

# HLA allele to use for predictions
HLA_ALLELE = "HLA-A*02:01"

# Prediction methods to run
# ALWAYS RUN THESE THREE METHODS (mirrors original Perl script behavior):
#   - "smm" ✅ (Python/cpickle data - works on macOS and Linux)
#   - "ann" ⚠️ (Requires Linux binary - may produce empty results on macOS)
#   - "comblib_sidney2008" ✅ (Python matrices - works on macOS and Linux)
#
# Note: ANN may produce blank/empty results on macOS (Linux binary required)
#       but will still run and produce output files as per original Perl script
METHODS = ["smm", "ann", "comblib_sidney2008"]  # Always run all three

# Peptide length to extract
PEPTIDE_LENGTH = 9

# ============================================================================
# FUNCTIONS
# ============================================================================

def read_fasta_file(fasta_path):
    """
    Read a FASTA file and extract sequence information.
    
    Args:
        fasta_path (str): Path to FASTA file
        
    Returns:
        tuple: (sequence_name, sequence_string)
    """
    with open(fasta_path, 'r') as f:
        lines = f.readlines()    
    # Extract sequence name from first line (remove '>')
    seq_name = lines[0].strip().lstrip('>')    
    # Extract sequence (remove newlines)
    sequence = ''.join(line.strip() for line in lines[1:] if line.strip() and not line.startswith('>'))    
    return seq_name, sequence

def extract_kmers(sequence, k=9):
    """
    Extract all k-mers from a protein sequence.
    
    Args:
        sequence (str): Protein sequence
        k (int): Length of k-mer
        
    Returns:
        list: List of k-mer peptides
    """
    kmers = []
    for i in range(len(sequence) - k + 1):
        kmers.append(sequence[i:i+k])
    return kmers


def create_json_input(peptide_list, allele, methods):
    """
    Create JSON input for IEDB prediction.
    
    Args:
        peptide_list (list): List of peptide sequences
        allele (str): HLA allele
        methods (list): List of prediction methods
        
    Returns:
        dict: JSON input structure
    """
    # Ensure methods is a list
    if isinstance(methods, str):
        methods = [methods]
    
    predictors = []
    for method in methods:
        predictors.append({
            "type": "binding",
            "method": method
        })
    
    json_input = {
        "peptide_list": peptide_list,
        "alleles": allele,
        "predictors": predictors
    }
    return json_input

def run_iedb_prediction(json_data, output_prefix):
    """
    Run IEDB prediction via subprocess call.
    
    Args:
        json_data (dict): JSON input data
        output_prefix (str): Output file prefix
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
        json.dump(json_data, tmp_json, indent=2)
        tmp_json_path = tmp_json.name
    
    try:
        # Construct command
        cmd = [
            'python3',
            IEDB_SCRIPT,
            '-j', tmp_json_path,
            '-o', output_prefix,
            '-f', 'tsv'
        ]
        
        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if output file was created (even if empty)
        output_file = f"{output_prefix}.tsv"
        if os.path.exists(output_file):
            # Check if file has content (more than just header)
            with open(output_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"✓ Successfully generated: {output_prefix}.tsv ({len(lines)-1} predictions)")
                else:
                    print(f"⚠ Generated: {output_prefix}.tsv (empty - no predictions, may be platform limitation)")
        else:
            print(f"⚠ Output file not found: {output_prefix}.tsv")
        
        if result.stdout:
            print(f"  Output: {result.stdout}")
        if result.stderr:
            print(f"  Warnings: {result.stderr}")
        
        # Return True even if results are empty (matches original script behavior)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to process {output_prefix}")
        print(f"  Error: {e}")
        print(f"  stderr: {e.stderr}")
        return False
        
    finally:
        # Clean up temporary JSON file
        if os.path.exists(tmp_json_path):
            os.unlink(tmp_json_path)


def process_fasta_file(fasta_path):
    """
    Process a single FASTA file through the complete pipeline.
    
    Args:
        fasta_path (str): Path to FASTA file
        
    Returns:
        bool: True if successful
    """
    print(f"\n{'='*70}")
    print(f"Processing: {fasta_path}")
    print(f"{'='*70}")
    # 1. Read FASTA file
    try:
        seq_name, sequence = read_fasta_file(fasta_path)
        print(f"\n✓ Read FASTA")
        print(f"  Sequence: {seq_name}")
        print(f"  Length: {len(sequence)} residues")
        print(f"  Sequence: {sequence}")
    except Exception as e:
        print(f"✗ Error reading FASTA: {e}")
        return False
    
    # 2. Create JSON input with FASTA file path - let IEDB handle sliding window
    # This preserves the original sliding window logic where longer sequences
    # automatically produce more peptides
    print(f"\n✓ Sequence length: {len(sequence)} residues")
    print(f"  Will generate all {PEPTIDE_LENGTH}-mer peptides via IEDB sliding window")
    
    # 3. Create JSON input with FASTA file path (not pre-extracted peptides)
    # Create temporary FASTA file first
    import tempfile
    tmp_fasta_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fa', delete=False) as tmp_fasta:
            tmp_fasta.write(f">{seq_name}\n{sequence}\n")
            tmp_fasta_path = tmp_fasta.name
        
        # Create JSON input with FASTA file path
        json_data = {
            "input_sequence_text_file_path": tmp_fasta_path,
            "peptide_length_range": [PEPTIDE_LENGTH, PEPTIDE_LENGTH],
            "alleles": HLA_ALLELE,
            "predictors": []
        }
        for method in METHODS:
            json_data["predictors"].append({
                "type": "binding",
                "method": method
            })
        print(f"\n✓ Created JSON input structure")
        print(f"  Allele: {HLA_ALLELE}")
        print(f"  Methods: {METHODS}")
        print(f"  FASTA file: {tmp_fasta_path}")
        print(f"  Peptide length: {PEPTIDE_LENGTH}")
        print(f"  IEDB will extract all {PEPTIDE_LENGTH}-mers via sliding window")
        
        # 4. Determine output filenames for each method
        seq_filename = os.path.basename(fasta_path)
        base_name = os.path.splitext(seq_filename)[0]
        
        # Run predictions for each method
        results = []
        for method in METHODS:
            output_filename = f"{base_name}_iedb_{method}"
            output_prefix = os.path.join(OUTPUT_DIR, output_filename)
            
            print(f"\n✓ Processing with method: {method}")
            print(f"  Output prefix: {output_prefix}")
            
            # Create single-method JSON input with FASTA file path
            single_method_json = {
                "input_sequence_text_file_path": tmp_fasta_path,
                "peptide_length_range": [PEPTIDE_LENGTH, PEPTIDE_LENGTH],
                "alleles": HLA_ALLELE,
                "predictors": [{
                    "type": "binding",
                    "method": method
                }]
            }
            
            # Run IEDB prediction via subprocess
            success = run_iedb_prediction(single_method_json, output_prefix)
            results.append((method, success))
        
        # Check if all methods succeeded
        all_success = all(result[1] for result in results)
        
        if all_success:
            print(f"\n✓✓✓ Successfully processed {seq_name}")
            print(f"   Output files:")
            for method, success in results:
                if success:
                    output_filename = f"{base_name}_iedb_{method}"
                    output_prefix = os.path.join(OUTPUT_DIR, output_filename)
                    print(f"   - {output_prefix}.tsv ({method})")
                    print(f"   - {output_prefix}.json ({method})")
            return True
        else:
            print(f"\n✗✗✗ Failed to process {seq_name}")
            for method, success in results:
                if not success:
                    print(f"   Failed method: {method}")
            return False
    finally:
        # Clean up temporary FASTA file
        if tmp_fasta_path and os.path.exists(tmp_fasta_path):
            os.unlink(tmp_fasta_path)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    
    print("="*70)
    print("IEDB Subprocess Development Wrapper")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  IEDB Script: {IEDB_SCRIPT}")
    print(f"  Output Dir:  {OUTPUT_DIR}")
    print(f"  HLA Allele:  {HLA_ALLELE}")
    print(f"  Methods:     {METHODS}")
    print(f"  K-mer Length: {PEPTIDE_LENGTH}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n✓ Created output directory: {OUTPUT_DIR}")
    
    # Process each FASTA file
    results = []
    for fasta_path in INPUT_FASTA_FILES:
        if os.path.exists(fasta_path):
            success = process_fasta_file(fasta_path)
            results.append((fasta_path, success))
        else:
            print(f"\n✗ FASTA file not found: {fasta_path}")
            results.append((fasta_path, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for fasta_path, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {os.path.basename(fasta_path)}: {status}")
    
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("="*70)


if __name__ == "__main__":
    main()

