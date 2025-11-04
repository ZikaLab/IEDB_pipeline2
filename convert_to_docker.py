#!/usr/bin/env python3
"""
Docker Path Conversion Script for IEDB Pipeline

Converts hardcoded local paths to Docker-compatible paths (/app/) 
by creating modified copies of wrapper and vendor scripts.

Original files remain untouched. Converted files are placed in docker-build/ directory.

author: Michael W. Gaunt, Ph.D
"""
import os
import shutil
from pathlib import Path
import re

# Configuration
LOCAL_BASE_PATH = "/Users/michael_gaunt/Desktop/Anastasia"
DOCKER_BASE_PATH = "/app"
OUTPUT_DIR = Path(__file__).parent / "docker-build"

# Files to convert
PYTHON_SCRIPTS = [
    "iedb_run-cmd_wrapper.py",
    "iedb_run-cmd_v0-2.py",
]

PERL_SCRIPTS = [
    "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl",
    "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl",
    "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl",
]

# Files to copy without modification
FILES_TO_COPY = [
    "docker_run.sh",
    "Dockerfile",
]

# Directories to copy recursively without modification
DIRS_TO_COPY = [
    "1_ng_tc1-0.1.2-beta",
]


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def convert_python_script(src: Path, dst: Path) -> list[str]:
    """
    Convert Python script to Docker paths.
    Returns list of changes made.
    """
    changes = []
    text = src.read_text()
    original_text = text
    
    # Convert iedb_run-cmd_v0-2.py: change default BASE_DIR fallback
    if src.name == "iedb_run-cmd_v0-2.py":
        # Line 259: BASE_DIR default
        old_pattern = 'base_dir = Path(os.getenv("BASE_DIR", "/Users/michael_gaunt/Desktop/Anastasia"))'
        new_pattern = 'base_dir = Path(os.getenv("BASE_DIR", "/app"))'
        if old_pattern in text:
            text = text.replace(old_pattern, new_pattern)
            changes.append(f"Updated BASE_DIR default: {LOCAL_BASE_PATH} → {DOCKER_BASE_PATH}")
    
    # Convert iedb_run-cmd_wrapper.py: update hardcoded paths in render_temp_perl function
    if src.name == "iedb_run-cmd_wrapper.py":
        # Line 168: parent_cwd replacement string
        old_pattern1 = "my $parent_cwd = '/Users/michael_gaunt/Desktop/Anastasia/';"
        new_pattern1 = "my $parent_cwd = '$ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/app/';"
        if old_pattern1 in text:
            text = text.replace(old_pattern1, new_pattern1)
            changes.append("Updated parent_cwd replacement in render_temp_perl()")
        
        # Line 186: iedb_script replacement string
        old_pattern2 = 'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
        new_pattern2 = 'my $iedb_script = ($ENV{"BASE_DIR"} ? $ENV{"BASE_DIR"} : "/app") . "/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
        if old_pattern2 in text:
            text = text.replace(old_pattern2, new_pattern2)
            changes.append("Updated iedb_script replacement in render_temp_perl()")
    
    if text != original_text:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        print(f"✓ Converted: {src.name}")
    else:
        # Copy unchanged file
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"→ Copied (no changes): {src.name}")
    
    return changes


def convert_perl_alignment_script(src: Path, dst: Path) -> list[str]:
    """
    Convert iedb_alignment_run_v0-2.pl to Docker paths.
    Returns list of changes made.
    """
    changes = []
    text = src.read_text()
    original_text = text
    
    # Line 27: Convert hardcoded parent_cwd to use BASE_DIR env var
    old_line1 = "my $parent_cwd = '/Users/michael_gaunt/Desktop/Anastasia/';"
    new_line1 = "my $parent_cwd = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/app/';"
    if old_line1 in text:
        text = text.replace(old_line1, new_line1)
        changes.append("Updated parent_cwd to use BASE_DIR env var with /app/ fallback")
    
    # Line 146: Convert hardcoded Python script path
    old_line2 = 'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
    new_line2 = 'my $iedb_script = ($ENV{"BASE_DIR"} ? $ENV{"BASE_DIR"} : "/app") . "/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";'
    if old_line2 in text:
        text = text.replace(old_line2, new_line2)
        changes.append("Updated iedb_script path to use BASE_DIR env var with /app/ fallback")
    
    if text != original_text:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        print(f"✓ Converted: {src.name}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"→ Copied (no changes): {src.name}")
    
    return changes


def convert_perl_ref_parser(src: Path, dst: Path) -> list[str]:
    """
    Convert iedb_output_ref-parse_v0-1.pl to Docker paths.
    Returns list of changes made.
    """
    changes = []
    text = src.read_text()
    original_text = text
    
    # Line 29: Convert hardcoded fallback path
    old_line = "my $here = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/Users/michael_gaunt/Desktop/Anastasia/';"
    new_line = "my $here = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/app/';"
    if old_line in text:
        text = text.replace(old_line, new_line)
        changes.append("Updated BASE_DIR fallback: /Users/... → /app/")
    
    if text != original_text:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        print(f"✓ Converted: {src.name}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"→ Copied (no changes): {src.name}")
    
    return changes


def convert_perl_v05_parser(src: Path, dst: Path) -> list[str]:
    """
    Convert iedb_output_parse_v0-5.pl to Docker paths.
    Returns list of changes made.
    """
    changes = []
    text = src.read_text()
    original_text = text
    
    # Line 45: Convert hardcoded fallback path
    old_line1 = "my $here = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/Users/michael_gaunt/Desktop/Anastasia/';"
    new_line1 = "my $here = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/app/';"
    if old_line1 in text:
        text = text.replace(old_line1, new_line1)
        changes.append("Updated BASE_DIR fallback: /Users/... → /app/")
    
    # Line 51: Convert master_files hash key for Docker consistency
    # Note: This is still dynamically replaced at runtime, but we set a Docker-friendly default
    old_line2 = "'/dev_test_out-pl/' => 'anticancer_test-ref.csv'"
    new_line2 = "'/query_output/' => 'anticancer_test-ref.csv'"
    if old_line2 in text:
        text = text.replace(old_line2, new_line2)
        changes.append("Updated master_files key: /dev_test_out-pl/ → /query_output/ (for Docker consistency)")
    
    if text != original_text:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        print(f"✓ Converted: {src.name}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"→ Copied (no changes): {src.name}")
    
    return changes


def main():
    """Main conversion function."""
    base_dir = Path(__file__).parent
    
    print("=" * 70)
    print("Docker Path Conversion Script")
    print("=" * 70)
    print(f"Source directory: {base_dir}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Converting: {LOCAL_BASE_PATH} → {DOCKER_BASE_PATH}")
    print()
    
    # Create output directory
    ensure_dir(OUTPUT_DIR)
    
    all_changes = []
    
    # Convert Python scripts
    print("Converting Python scripts...")
    print("-" * 70)
    for script in PYTHON_SCRIPTS:
        src = base_dir / script
        if not src.exists():
            print(f"✗ WARNING: Source file not found: {script}")
            continue
        
        dst = OUTPUT_DIR / script
        changes = convert_python_script(src, dst)
        all_changes.extend(changes)
    
    print()
    print("Converting Perl scripts...")
    print("-" * 70)
    
    # Convert Perl alignment script
    perl_align = "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl"
    src = base_dir / perl_align
    if src.exists():
        dst = OUTPUT_DIR / perl_align
        changes = convert_perl_alignment_script(src, dst)
        all_changes.extend(changes)
    else:
        print(f"✗ WARNING: Source file not found: {perl_align}")
    
    # Convert Perl ref parser
    perl_ref = "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl"
    src = base_dir / perl_ref
    if src.exists():
        dst = OUTPUT_DIR / perl_ref
        changes = convert_perl_ref_parser(src, dst)
        all_changes.extend(changes)
    else:
        print(f"✗ WARNING: Source file not found: {perl_ref}")
    
    # Convert Perl v05 parser
    perl_v05 = "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl"
    src = base_dir / perl_v05
    if src.exists():
        dst = OUTPUT_DIR / perl_v05
        changes = convert_perl_v05_parser(src, dst)
        all_changes.extend(changes)
    else:
        print(f"✗ WARNING: Source file not found: {perl_v05}")
    
    print()
    print("Copying files without modification...")
    print("-" * 70)
    
    # Copy files that don't need modification
    for file_path in FILES_TO_COPY:
        src = base_dir / file_path
        if src.exists():
            dst = OUTPUT_DIR / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"→ Copied: {file_path}")
        else:
            print(f"✗ WARNING: File not found: {file_path}")
    
    print()
    print("Copying directories without modification...")
    print("-" * 70)
    
    # Copy directories recursively without modification
    for dir_path in DIRS_TO_COPY:
        src = base_dir / dir_path
        if src.exists() and src.is_dir():
            dst = OUTPUT_DIR / dir_path
            # Remove destination if it exists to avoid conflicts
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, dirs_exist_ok=False)
            print(f"→ Copied directory: {dir_path}/")
        else:
            print(f"✗ WARNING: Directory not found: {dir_path}")
    
    print()
    print("=" * 70)
    print("Conversion Summary")
    print("=" * 70)
    if all_changes:
        print(f"Total changes made: {len(all_changes)}")
        print("\nChanges:")
        for i, change in enumerate(all_changes, 1):
            print(f"  {i}. {change}")
    else:
        print("No path conversions were needed (files already use environment variables)")
    
    print()
    print(f"✓ Converted files are in: {OUTPUT_DIR}")
    print()
    print("Files copied (unchanged):")
    for file_path in FILES_TO_COPY:
        print(f"  - {file_path}")
    for dir_path in DIRS_TO_COPY:
        print(f"  - {dir_path}/")
    print()
    print("Next steps:")
    print("  1. Review converted files in docker-build/")
    print("  2. Upload docker-build/ to AWS")
    print("  3. Build Docker image on AWS")
    print()


if __name__ == "__main__":
    main()

