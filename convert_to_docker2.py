#!/usr/bin/env python3
"""
Docker Fix Script for iedb_run-cmd_v0-2.py

Fixes the temp file path issue in _run_v05_for_query function.
The temp file should be created in BASE_DIR, not in base_dir (OUTPUT_ROOT).

author: Michael W. Gaunt, Ph.D
"""
import os
from pathlib import Path

# Configuration
DOCKER_BUILD_DIR = Path(__file__).parent / "docker-build"
TARGET_FILE = DOCKER_BUILD_DIR / "iedb_run-cmd_v0-2.py"


def fix_v05_temp_file_path(file_path: Path) -> bool:
    """
    Fix the temp file path in _run_v05_for_query to use BASE_DIR instead of base_dir.
    Returns True if fix was applied, False if not needed.
    """
    text = file_path.read_text()
    original_text = text
    
    # Find the problematic line in _run_v05_for_query
    # Line 70: tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
    # Should be: tmp = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
    
    # We need to get BASE_DIR from the wrapper script's context
    # Actually, we should import os and use BASE_DIR from environment or calculate it
    # Let's fix it to use the same logic as the wrapper uses
    
    # Look for the pattern: tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
    # Need to replace with BASE_DIR-based path and ensure directory exists
    old_pattern = '\ttmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"'
    new_code = '''\t# Use BASE_DIR (from env or default to /app) instead of base_dir (which is OUTPUT_ROOT)
\tbase_dir_for_tmp = Path(os.getenv("BASE_DIR", "/app"))
\ttmp = base_dir_for_tmp / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
\t# Ensure the directory exists before writing
\ttmp.parent.mkdir(parents=True, exist_ok=True)'''
    
    if old_pattern in text:
        text = text.replace(old_pattern, new_code)
        file_path.write_text(text)
        return True
    
    # Also check if already partially fixed but missing directory creation
    if 'base_dir_for_tmp = Path(os.getenv("BASE_DIR", "/app"))' in text and 'tmp.parent.mkdir' not in text:
        # Add directory creation if missing
        pattern_to_find = 'tmp = base_dir_for_tmp / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"'
        if pattern_to_find in text:
            replacement = 'tmp = base_dir_for_tmp / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"\n\t# Ensure the directory exists before writing\n\ttmp.parent.mkdir(parents=True, exist_ok=True)'
            text = text.replace(pattern_to_find, replacement)
            file_path.write_text(text)
            return True
    
    return False


def main():
    """Main fix function."""
    print("=" * 70)
    print("Docker Fix Script for iedb_run-cmd_v0-2.py")
    print("=" * 70)
    print(f"Target file: {TARGET_FILE}")
    print()
    
    if not TARGET_FILE.exists():
        print(f"✗ ERROR: Target file not found: {TARGET_FILE}")
        print("Make sure docker-build/iedb_run-cmd_v0-2.py exists")
        return
    
    print("Fixing temp file path in _run_v05_for_query()...")
    print("-" * 70)
    
    if fix_v05_temp_file_path(TARGET_FILE):
        print("✓ Fixed: Updated temp file path to use BASE_DIR instead of base_dir")
    else:
        print("→ No changes needed (fix may already be applied)")
    
    print()
    print("=" * 70)
    print("Fix Complete")
    print("=" * 70)
    print(f"✓ Updated file: {TARGET_FILE}")
    print()
    print("Next steps:")
    print("  1. Verify the fix in docker-build/iedb_run-cmd_v0-2.py")
    print("  2. Rebuild Docker image on EC2")
    print()


if __name__ == "__main__":
    main()

