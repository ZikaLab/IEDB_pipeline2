#!/usr/bin/env python3
"""
convert_to_docker3.py

Fixes BASE_DIR environment variable issue in docker-build/iedb_run-cmd_v0-2.py

The problem: BASE_DIR was being set to base_dir (OUTPUT_ROOT=/app/outputs) instead of 
the actual BASE_DIR (/app), which caused Perl scripts to look for data files in the 
wrong location.

Fixes:
1. In _run_parser: Set BASE_DIR to os.getenv("BASE_DIR", "/app") instead of base_dir
2. In _run_v05_for_query: Set BASE_DIR to os.getenv("BASE_DIR", "/app") instead of base_dir
"""

import os
from pathlib import Path


def fix_base_dir_env_vars(file_path: Path) -> bool:
    """
    Fix BASE_DIR environment variable settings in iedb_run-cmd_v0-2.py
    
    Args:
        file_path: Path to the file to fix
        
    Returns:
        True if changes were made, False otherwise
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    text = file_path.read_text()
    original_text = text
    
    # Fix 1: In _run_parser function
    # Replace the problematic BASE_DIR assignment
    # Try multiple patterns in case the file has been partially modified
    
    # Pattern 1a: Original pattern with Path conversion
    old_parser_code1a = """	# Pass BASE_DIR as environment variable for Perl scripts (from environment if set, else use base_dir)
	env = os.environ.copy()
	# Use BASE_DIR from environment if available, otherwise use base_dir
	env_base_dir = Path(env.get('BASE_DIR', base_dir.as_posix()))
	env['BASE_DIR'] = env_base_dir.as_posix()"""
    
    # Pattern 1b: Simplified version (if Path conversion was already removed)
    old_parser_code1b = """	# Pass BASE_DIR as environment variable for Perl scripts
	env = os.environ.copy()
	env['BASE_DIR'] = base_dir.as_posix()"""
    
    new_parser_code = """	# Pass BASE_DIR as environment variable for Perl scripts
	# Use actual BASE_DIR (from env or default to /app), not base_dir which is OUTPUT_ROOT
	env = os.environ.copy()
	env['BASE_DIR'] = os.getenv("BASE_DIR", "/app")"""
    
    fixed_parser = False
    if old_parser_code1a in text:
        text = text.replace(old_parser_code1a, new_parser_code)
        print("✓ Fixed BASE_DIR in _run_parser function (pattern 1a)")
        fixed_parser = True
    elif old_parser_code1b in text:
        text = text.replace(old_parser_code1b, new_parser_code)
        print("✓ Fixed BASE_DIR in _run_parser function (pattern 1b)")
        fixed_parser = True
    
    if not fixed_parser:
        # Check if already fixed
        if 'env[\'BASE_DIR\'] = os.getenv("BASE_DIR", "/app")' in text and '_run_parser' in text:
            print("⚠ _run_parser BASE_DIR already fixed")
        else:
            print("⚠ Pattern 1 not found - code structure may have changed")
    
    # Fix 2: In _run_v05_for_query function - also fix tmp path creation and master_files path
    # Replace the problematic BASE_DIR assignment and fix tmp file path
    
    # Pattern 2a: Original tmp path (before convert_to_docker2.py fix)
    old_v05_tmp_code = """	v05 = parser_v05_path
	tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
	text = v05.read_text()"""
    
    new_v05_tmp_code = """	v05 = parser_v05_path
	# Use BASE_DIR (from env or default to /app) instead of base_dir (which is OUTPUT_ROOT)
	base_dir_for_tmp = Path(os.getenv("BASE_DIR", "/app"))
	tmp = base_dir_for_tmp / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
	# Ensure the directory exists before writing
	tmp.parent.mkdir(parents=True, exist_ok=True)
	text = v05.read_text()"""
    
    fixed_tmp = False
    if old_v05_tmp_code in text:
        text = text.replace(old_v05_tmp_code, new_v05_tmp_code)
        print("✓ Fixed tmp path creation in _run_v05_for_query function")
        fixed_tmp = True
    
    # Pattern 2c: Fix master_files path replacement - must include 'outputs/' prefix
    # In Perl: $here = BASE_DIR (/app/ with trailing slash), but files are in OUTPUT_ROOT (/app/outputs/)
    # Since $here has trailing slash, master_files key should be 'outputs/query_output/' (NO leading slash)
    # This avoids double-slash: '/app/' + 'outputs/query_output/' = '/app/outputs/query_output/'
    # 
    # NOTE: In docker-build, convert_to_docker.py already changed '/dev_test_out-pl/' to '/query_output/'
    # So we need to replace '/query_output/' (or '/dev_test_out-pl/' if present) with 'outputs/query_output/'
    
    # Pattern to match old code - original pattern from source (before convert_to_docker.py)
    old_master_files_code1 = """	# Update master_files to query_input_dir
	text = text.replace("\\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		f"\\t'/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
    
    # Pattern to match docker-build version (convert_to_docker.py sets it to '/query_output/')
    # This is what we actually need to fix - replace '/query_output/' with 'outputs/query_output/'
    old_master_files_code2a = """	# Update master_files to query_input_dir
	text = text.replace("\\t'/query_output/' => 'anticancer_test-ref.csv'",
		f"\\t'/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
    
    # Pattern to match current fix attempt (with '/outputs/' but wrong - has leading slash)
    old_master_files_code2b = """	# Update master_files to query_input_dir
	# Note: $here in Perl is BASE_DIR (/app/), but files are in OUTPUT_ROOT (/app/outputs/)
	# So we need to prepend 'outputs/' to the path
	# base_dir parameter is OUTPUT_ROOT, so query_input_dir is relative to OUTPUT_ROOT
	text = text.replace("\\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		f"\\t'/outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
    
    new_master_files_code = """	# Update master_files to query_input_dir
	# Note: $here in Perl is BASE_DIR (/app/ with trailing slash), files are in OUTPUT_ROOT (/app/outputs/)
	# Since $here has trailing slash, use 'outputs/{query_input_dir}/' (NO leading slash)
	# Result: '/app/' + 'outputs/query_output/' = '/app/outputs/query_output/' (no double-slash)
	# Replace either '/dev_test_out-pl/' (original) or '/query_output/' (from convert_to_docker.py)
	text = text.replace("\\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		f"\\t'outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")
	text = text.replace("\\t'/query_output/' => 'anticancer_test-ref.csv'",
		f"\\t'outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
    
    if old_master_files_code1 in text:
        text = text.replace(old_master_files_code1, new_master_files_code)
        print("✓ Fixed master_files path to include 'outputs/' prefix (no leading slash)")
        fixed_tmp = True
    elif old_master_files_code2a in text:
        # Replace '/query_output/' (from convert_to_docker.py) with 'outputs/query_output/'
        text = text.replace(old_master_files_code2a, new_master_files_code)
        print("✓ Fixed master_files path - replaced '/query_output/' with 'outputs/query_output/'")
        fixed_tmp = True
    elif old_master_files_code2b in text:
        text = text.replace(old_master_files_code2b, new_master_files_code)
        print("✓ Fixed master_files path - removed leading slash to avoid double-slash issue")
        fixed_tmp = True
    elif "'outputs/{query_input_dir}/'" in text and "'/outputs/{query_input_dir}/'" not in text:
        # Check if we need to add the '/query_output/' replacement
        if "text.replace(\"\\t'/query_output/'" not in text and "text.replace('\\t'/query_output/'" not in text:
            # Add the second replacement for '/query_output/'
            # Simply append it after the first replacement line
            old_single_replacement = """\ttext = text.replace("\\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
\t\tf"\\t'outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
            new_double_replacement = """\ttext = text.replace("\\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
\t\tf"\\t'outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")
\ttext = text.replace("\\t'/query_output/' => 'anticancer_test-ref.csv'",
\t\tf"\\t'outputs/{query_input_dir}/' => 'anticancer_test-ref.csv'")"""
            if old_single_replacement in text:
                text = text.replace(old_single_replacement, new_double_replacement)
                print("✓ Added '/query_output/' replacement to handle docker-build version")
                fixed_tmp = True
            else:
                print("⚠ master_files path already correct (no leading slash)")
        else:
            print("⚠ master_files path already correct (includes both replacements)")
    elif "'/outputs/{query_input_dir}/'" in text:
        # Still has leading slash - need to fix
        text = text.replace("f\"\\t'/outputs/{query_input_dir}/'", "f\"\\t'outputs/{query_input_dir}/'")
        text = text.replace("f'\\t'/outputs/{query_input_dir}/'", "f'\\t'outputs/{query_input_dir}/'")
        print("✓ Fixed master_files path - removed leading slash")
        fixed_tmp = True
    
    # Pattern 2b: BASE_DIR environment variable assignment
    old_v05_env_code = """	# Pass BASE_DIR as environment variable for Perl scripts
	env = os.environ.copy()
	env['BASE_DIR'] = base_dir.as_posix()"""
    
    new_v05_env_code = """	# Pass BASE_DIR as environment variable for Perl scripts
	# Use actual BASE_DIR (from env or default to /app), not base_dir which is OUTPUT_ROOT
	env = os.environ.copy()
	env['BASE_DIR'] = os.getenv("BASE_DIR", "/app")"""
    
    fixed_env = False
    if old_v05_env_code in text:
        text = text.replace(old_v05_env_code, new_v05_env_code)
        print("✓ Fixed BASE_DIR env var in _run_v05_for_query function")
        fixed_env = True
    
    if not fixed_tmp and not fixed_env:
        # Check if already fixed
        if 'base_dir_for_tmp = Path(os.getenv("BASE_DIR", "/app"))' in text:
            print("⚠ _run_v05_for_query tmp path already fixed")
        if 'env[\'BASE_DIR\'] = os.getenv("BASE_DIR", "/app")' in text and '_run_v05_for_query' in text:
            print("⚠ _run_v05_for_query BASE_DIR already fixed")
        if not ('base_dir_for_tmp' in text or 'env[\'BASE_DIR\'] = os.getenv("BASE_DIR", "/app")' in text):
            print("⚠ Pattern 2 not found - code structure may have changed")
    
    # Only write if changes were made
    if text != original_text:
        file_path.write_text(text)
        print(f"\n✓ Successfully updated: {file_path}")
        return True
    else:
        print(f"\n⚠ No changes needed in: {file_path}")
        return False


def main():
    """Main function to apply fixes"""
    script_dir = Path(__file__).parent.resolve()
    target_file = script_dir / "docker-build" / "iedb_run-cmd_v0-2.py"
    
    print("=" * 60)
    print("convert_to_docker3.py - BASE_DIR Environment Variable Fix")
    print("=" * 60)
    print(f"Target file: {target_file}")
    print()
    
    if fix_base_dir_env_vars(target_file):
        print("\n✓ Conversion complete!")
    else:
        print("\n⚠ No changes applied.")


if __name__ == "__main__":
    main()
