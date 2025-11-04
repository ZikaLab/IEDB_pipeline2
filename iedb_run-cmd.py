import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BASE_DIR = Path("/Users/michael_gaunt/Desktop/Anastasia")
DATA_DIR = BASE_DIR / "data"
PERL_SRC = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_alignment_run_v0-2.pl"
PARSER_SRC = BASE_DIR / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-3.pl"

# Output roots
REF_OUTPUT_ROOT = BASE_DIR / "ref_output"
QUERY_OUTPUT_ROOT = BASE_DIR / "query_output"
REF_TMP_DIR = BASE_DIR / "ref_tmp"
QUERY_PARSED_ROOT = BASE_DIR / "query_parsed"

CD8_ALLELE = "HLA-A*02:01"  # Aligned with existing usage


def find_reference_and_query(data_dir: Path) -> tuple[Path, Path]:
    csvs = [p for p in data_dir.glob("*.csv")]
    if len(csvs) != 2:
        raise RuntimeError(f"Expected exactly 2 CSV files in {data_dir}, found {len(csvs)}")
    ref = next((p for p in csvs if "ref" in p.name.lower()), None)
    if ref is None:
        raise RuntimeError("Could not find reference CSV (filename must contain 'ref')")
    query = next(p for p in csvs if p != ref)
    return ref, query


def _has_real_outputs(output_root: Path) -> bool:
    """Return True if directory contains real outputs (not just fa_tmp or run_*)."""
    patterns = ["*.csv.tsv", "*.tsv", "*.csv", "Total_MBFV_*.log", "*.json"]
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

    tmpdir = Path(tempfile.mkdtemp(prefix="iedb_run_"))
    temp_pl = tmpdir / "iedb_alignment_run_tmp.pl"
    temp_pl.write_text(new_text)
    return temp_pl


def run_perl(perl_path: Path) -> None:
    cmd = ["perl", perl_path.as_posix()]
    completed = subprocess.run(cmd, cwd=BASE_DIR.as_posix(), capture_output=True, text=True)
    if completed.stdout:
        print("[perl stdout]\n" + completed.stdout)
    if completed.stderr:
        print("[perl stderr]\n" + completed.stderr)
    if completed.returncode != 0 and completed.stderr.strip():
        raise RuntimeError("Perl run failed with errors. See stderr above.")


def copy_ref_outputs_to_tmp(output_root: Path, ref_tmp_dir: Path) -> None:
    patterns = ["*.csv.tsv", "*.tsv", "*.csv", "Total_MBFV_*.log"]
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
    logs = list(output_root.glob("Total_MBFV_*.log"))
    print(f"[{label}] fa_tmp exists; Total_MBFV logs found: {len(logs)}")


def render_temp_parser_for_query(parser_src: Path, query_output: Path, output_parsed: Path) -> Path:
    text = parser_src.read_text()
    new_text = text
    new_text = new_text.replace(
        "my $here = '/Users/michael_gaunt/Desktop/Anastasia/';",
        f"my $here = '{BASE_DIR.as_posix()}/';",
    )
    new_text = new_text.replace(
        "my %master_files = ( \n\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'\n\t);",
        f"my %master_files = ( \n\t'/query_output/' => 'anticancer_test-ref.csv'\n\t);",
    )
    new_text = new_text.replace(
        "my $output_dir = $here . 'dev_test_out-pl_parsed/';",
        f"my $output_dir = '{output_parsed.as_posix()}/';",
    )
    # Keep outputs under query_parsed: override file_begin and file_clean parent directory calculations
    new_text = new_text.replace(
        "(my $out_dir = $dir_0) =~ s/(.*\/).+?\/$/$1/;",
        "my $out_dir = $dir_0;",
    )
    new_text = new_text.replace(
        "(my $out_dir_8 = $dir_8) =~ s/(.*\/).+?\/$/$1/;",
        "my $out_dir_8 = $dir_8;",
    )

    tmpdir = Path(tempfile.mkdtemp(prefix="iedb_parse_"))
    temp_pl = tmpdir / "iedb_output_parse_tmp.pl"
    temp_pl.write_text(new_text)
    return temp_pl


def parse_query_outputs() -> None:
    QUERY_PARSED_ROOT.mkdir(parents=True, exist_ok=True)
    temp_parser = render_temp_parser_for_query(PARSER_SRC, QUERY_OUTPUT_ROOT, QUERY_PARSED_ROOT)
    run_perl(temp_parser)
    print(f"[parser] Wrote parsed outputs to {QUERY_PARSED_ROOT}")


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

    # Parse query outputs into query_parsed
    parse_query_outputs()

    print("All runs completed successfully.")


if __name__ == "__main__":
    main()
