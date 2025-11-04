"""
Main wrapper script for IEDB pipeline execution.
Orchestrates alignment runs and parsing pipeline.

author: Michael W. Gaunt, Ph.D
"""
import os
import shutil
import subprocess
import tempfile
import importlib.util
from pathlib import Path

# Import parsing pipeline from v0-2 (using importlib because filename has dashes)
v02_spec = importlib.util.spec_from_file_location(
    "iedb_run_cmd_v0_2",
    Path(__file__).parent / "iedb_run-cmd_v0-2.py"
)
v02 = importlib.util.module_from_spec(v02_spec)
v02_spec.loader.exec_module(v02)

# Get BASE_DIR from environment variable or default to script's parent directory
BASE_DIR = Path(os.getenv("BASE_DIR", str(Path(__file__).parent.resolve())))
DATA_DIR = BASE_DIR / "data"
PERL_SRC = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-3.pl"

# Output roots - allow override via environment variable
OUTPUT_ROOT = Path(os.getenv("OUTPUT_ROOT", str(BASE_DIR)))
REF_OUTPUT_ROOT = OUTPUT_ROOT / "ref_output"
QUERY_OUTPUT_ROOT = OUTPUT_ROOT / "query_output"
REF_TMP_DIR = OUTPUT_ROOT / "ref_tmp"

# Parser paths
PARSER_REF = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl"
PARSER_V05 = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl"

CD8_ALLELE = "HLA-A*02:01"  # Aligned with existing usage


def find_reference_and_query(data_dir: Path) -> tuple[Path, Path]:
    """Find reference and query CSV files.
    
    Detection order:
    1. Environment variables REF_CSV and QUERY_CSV (if set)
    2. Filename pattern: file with 'ref' in name → reference, other → query
    3. Fallback: alphabetical order (first = ref, second = query)
    """
    # Check if explicitly specified via environment variables
    ref_csv_env = os.getenv("REF_CSV")
    query_csv_env = os.getenv("QUERY_CSV")
    
    if ref_csv_env and query_csv_env:
        ref_path = Path(ref_csv_env)
        query_path = Path(query_csv_env)
        if not ref_path.exists():
            raise RuntimeError(f"REF_CSV file not found: {ref_csv_env}")
        if not query_path.exists():
            raise RuntimeError(f"QUERY_CSV file not found: {query_csv_env}")
        return ref_path, query_path
    
    # Otherwise, find CSVs in data directory
    csvs = sorted([p for p in data_dir.glob("*.csv")])
    if len(csvs) < 2:
        raise RuntimeError(
            f"Expected at least 2 CSV files in {data_dir}, found {len(csvs)}. "
            f"Alternatively, set REF_CSV and QUERY_CSV environment variables."
        )
    
    # Try to detect by filename (contains "ref")
    ref = next((p for p in csvs if "ref" in p.name.lower()), None)
    if ref:
        query = next(p for p in csvs if p != ref)
        return ref, query
    
    # Fallback: if exactly 2 files, use first as ref, second as query
    if len(csvs) == 2:
        print(f"[warning] Could not auto-detect reference file by 'ref' pattern.")
        print(f"[warning] Using first file as reference: {csvs[0].name}")
        print(f"[warning] Using second file as query: {csvs[1].name}")
        print(f"[warning] To override, set REF_CSV and QUERY_CSV environment variables.")
        return csvs[0], csvs[1]
    
    # Multiple files without "ref" - require explicit specification
    raise RuntimeError(
        f"Found {len(csvs)} CSV files in {data_dir} but none contain 'ref' in filename.\n"
        f"Files found: {', '.join(c.name for c in csvs)}\n"
        f"Please either:\n"
        f"  1. Rename one file to include 'ref' in the filename, or\n"
        f"  2. Set REF_CSV and QUERY_CSV environment variables to specify files explicitly."
    )


def _has_real_outputs(output_root: Path) -> bool:
    """Return True if directory contains real outputs (not just fa_tmp or run_*)."""
    patterns = ["*.csv.tsv", "*.tsv", "*.csv", "Total_EPAM_*.log", "*.json"]
    for pat in patterns:
        if any(output_root.glob(pat)):
            return True
    for p in output_root.iterdir():
        if p.name in {"fa_tmp", "run_1", "run_2", "run_3"}:
            continue
        return True
    return False


def rotate_runs(output_root: Path) -> None:
    run1 = output_root / "run_1"
    run2 = output_root / "run_2"
    run3 = output_root / "run_3"
    fa_tmp = output_root / "fa_tmp"

    if not output_root.exists():
        return

    if not _has_real_outputs(output_root):
        if fa_tmp.exists():
            shutil.rmtree(fa_tmp)
        return

    if run3.exists():
        shutil.rmtree(run3)
    if run2.exists():
        run2.rename(run3)
    if run1.exists():
        run1.rename(run2)
    run1.mkdir(parents=True, exist_ok=True)

    for item in list(output_root.iterdir()):
        if item.name in {"run_1", "run_2", "run_3"}:
            continue
        target = run1 / item.name
        item.rename(target)


def prepare_output_dirs(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    rotate_runs(output_root)
    (output_root / "fa_tmp").mkdir(parents=True, exist_ok=True)


def write_ref_tmp_note(ref_tmp_dir: Path) -> None:
    ref_tmp_dir.mkdir(parents=True, exist_ok=True)
    note = ref_tmp_dir / "README.txt"
    content = (
        "This directory contains temporary IEDB outputs generated for the reference sequences.\n"
        "They are used for the final calculation that compares reference percentile scores \n"
        "against query scores. Contents are overwritten on each wrapper run.\n"
    )
    note.write_text(content)


def clean_ref_tmp(ref_tmp_dir: Path) -> None:
    if ref_tmp_dir.exists():
        for child in ref_tmp_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        ref_tmp_dir.mkdir(parents=True, exist_ok=True)


def render_temp_perl(perl_src: Path, align_csv: Path, output_root: Path) -> Path:
    text = perl_src.read_text()
    new_text = text
    # Update parent_cwd to use BASE_DIR
    new_text = new_text.replace(
        "my $parent_cwd = '/Users/michael_gaunt/Desktop/Anastasia/';",
        f"my $parent_cwd = '{BASE_DIR.as_posix()}/';",
    )
    new_text = new_text.replace(
        "my $align_loc = $parent_cwd . 'data/';",
        f"my $align_loc = '{align_csv.parent.as_posix()}/';",
    )
    new_text = new_text.replace(
        "my $align = 'anticancer_test.csv';",
        f"my $align = '{align_csv.name}';",
    )
    new_text = new_text.replace(
        "my $iedb_out = $parent_cwd . 'dev_test_out-pl/';",
        f"my $iedb_out = '{output_root.as_posix()}/';",
    )
    # Update Python script path to use BASE_DIR
    python_script_path = BASE_DIR / "1_ng_tc1-0.1.2-beta/src/tcell_mhci.py"
    new_text = new_text.replace(
        'my $iedb_script = "/Users/michael_gaunt/Desktop/Anastasia/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py";',
        f'my $iedb_script = "{python_script_path.as_posix()}";',
    )

    tmpdir = Path(tempfile.mkdtemp(prefix="iedb_run_"))
    temp_pl = tmpdir / "iedb_alignment_run_tmp.pl"
    temp_pl.write_text(new_text)
    return temp_pl


def run_perl(perl_path: Path) -> None:
    cmd = ["perl", perl_path.as_posix()]
    # Pass BASE_DIR as environment variable for Perl scripts
    env = os.environ.copy()
    env['BASE_DIR'] = BASE_DIR.as_posix()
    completed = subprocess.run(cmd, cwd=BASE_DIR.as_posix(), env=env, capture_output=True, text=True)
    if completed.stdout:
        print("[perl stdout]\n" + completed.stdout)
    if completed.stderr:
        print("[perl stderr]\n" + completed.stderr)
    if completed.returncode != 0 and completed.stderr.strip():
        raise RuntimeError("Perl run failed with errors. See stderr above.")


def copy_ref_outputs_to_tmp(output_root: Path, ref_tmp_dir: Path) -> None:
    patterns = ["*.csv.tsv", "*.tsv", "*.csv", "Total_EPAM_*.log"]
    print(f"[reference] scanning for outputs in: {output_root}")
    all_found: list[Path] = []
    for pattern in patterns:
        matches = list(output_root.glob(pattern))
        if matches:
            print(f"[reference] found {len(matches)} files for pattern {pattern}")
            for f in matches:
                print(f"  - {f.name}")
            all_found.extend(matches)
        else:
            print(f"[reference] no files for pattern {pattern}")
    copied = 0
    for f in all_found:
        shutil.copy2(f, ref_tmp_dir / f.name)
        copied += 1
    print(f"[reference] copied {copied} files to {ref_tmp_dir}")


def verify_outputs(output_root: Path, label: str) -> None:
    fa_tmp = output_root / "fa_tmp"
    print(f"[{label}] verifying outputs in {output_root}")
    if not fa_tmp.exists():
        raise RuntimeError(f"[{label}] Expected fa_tmp not found at {fa_tmp}")
    logs = list(output_root.glob("Total_EPAM_*.log"))
    print(f"[{label}] fa_tmp exists; Total_EPAM logs found: {len(logs)}")


def main() -> None:
    ref_csv, query_csv = find_reference_and_query(DATA_DIR)

    # Prepare ref_tmp
    clean_ref_tmp(REF_TMP_DIR)
    write_ref_tmp_note(REF_TMP_DIR)

    # Reference run (smart rotation)
    prepare_output_dirs(REF_OUTPUT_ROOT)
    ref_pl = render_temp_perl(PERL_SRC, ref_csv, REF_OUTPUT_ROOT)
    run_perl(ref_pl)
    verify_outputs(REF_OUTPUT_ROOT, label="reference")
    copy_ref_outputs_to_tmp(REF_OUTPUT_ROOT, REF_TMP_DIR)

    # Query run (smart rotation)
    prepare_output_dirs(QUERY_OUTPUT_ROOT)
    query_pl = render_temp_perl(PERL_SRC, query_csv, QUERY_OUTPUT_ROOT)
    run_perl(query_pl)
    verify_outputs(QUERY_OUTPUT_ROOT, label="query")

    # Run parsing pipeline (imported from v0-2)
    print("\n[parsing] Starting parsing pipeline...")
    # Pass OUTPUT_ROOT as base_dir so input/output dirs resolve correctly
    # Parser paths (PARSER_REF, PARSER_V05) are absolute, so they'll still work
    v02.run_parsing_pipeline(
        base_dir=OUTPUT_ROOT,  # Use OUTPUT_ROOT as base for input/output dirs
        parser_ref_path=PARSER_REF,  # Absolute path from BASE_DIR
        parser_v05_path=PARSER_V05,  # Absolute path from BASE_DIR
        ref_input_dir="ref_output",
        ref_output_dir="ref_parsed",
        query_input_dir="query_output",
        query_output_dir="query_parsed",
        percentile_threshold="2.5"
    )

    print("All runs completed successfully.")


if __name__ == "__main__":
    main()

