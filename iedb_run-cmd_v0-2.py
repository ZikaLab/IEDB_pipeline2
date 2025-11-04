"""
Parsing pipeline for IEDB outputs.
Handles ref and query parsing with pandas joins.

author: Michael W. Gaunt, Ph.D
"""
import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd


def _rotate_runs(output_root: Path) -> None:
	# basic rotation like run_1/run_2/run_3
	run1 = output_root / "run_1"
	run2 = output_root / "run_2"
	run3 = output_root / "run_3"
	if output_root.exists():
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
			if item.is_dir():
				shutil.copytree(item, target, dirs_exist_ok=True)
				shutil.rmtree(item)
			else:
				shutil.copy2(item, target)
				item.unlink()
	else:
		output_root.mkdir(parents=True, exist_ok=True)


def _run_parser(base_dir: Path, parser: Path, input_dir: str, output_dir: str) -> None:
	# ensure output dir exists and rotate
	out = base_dir / output_dir
	out.mkdir(parents=True, exist_ok=True)
	_rotate_runs(out)
	# Pass BASE_DIR as environment variable for Perl scripts (from environment if set, else use base_dir)
	env = os.environ.copy()
	# Use BASE_DIR from environment if available, otherwise use base_dir
	env_base_dir = Path(env.get('BASE_DIR', base_dir.as_posix()))
	env['BASE_DIR'] = env_base_dir.as_posix()
	# Input/output dirs are relative to base_dir (which should be OUTPUT_ROOT)
	cmd = [
		"perl",
		parser.as_posix(),
		output_dir,   # OUTPUT_DIR relative to base_dir
		input_dir     # INPUT_DIR relative to base_dir
	]
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), env=env, text=True, capture_output=True)
	if completed.stdout:
		print(completed.stdout, end="")
	if completed.stderr:
		print(completed.stderr, end="")
	if completed.returncode != 0:
		raise SystemExit(completed.returncode)


def _run_v05_for_query(base_dir: Path, parser_v05_path: Path, query_input_dir: str, query_output_dir: str, percentile_threshold: str = "9") -> None:
	"""Render a temp copy of v0-5 to point at query_input_dir and run it for query_output_dir."""
	v05 = parser_v05_path
	tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
	text = v05.read_text()
	# Update master_files to query_input_dir
	text = text.replace("\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		f"\t'/{query_input_dir}/' => 'anticancer_test-ref.csv'")
	tmp.write_text(text)
	# Prepare output dir and rotate
	query_out = base_dir / query_output_dir
	query_out.mkdir(parents=True, exist_ok=True)
	_rotate_runs(query_out)
	# Pass BASE_DIR as environment variable for Perl scripts
	env = os.environ.copy()
	env['BASE_DIR'] = base_dir.as_posix()
	cmd = ["perl", tmp.as_posix(), query_output_dir, percentile_threshold]  # Pass percentile threshold as 2nd arg
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), env=env, text=True, capture_output=True)
	if completed.stdout:
		print(completed.stdout, end="")
	if completed.stderr:
		print(completed.stderr, end="")
	if completed.returncode != 0:
		raise SystemExit(completed.returncode)
	try:
		tmp.unlink()
	except Exception:
		pass


def run_parsing_pipeline(base_dir: Path, parser_ref_path: Path, parser_v05_path: Path, ref_input_dir: str, ref_output_dir: str, query_input_dir: str, query_output_dir: str, percentile_threshold: str = "9") -> None:
	"""Main parsing pipeline function that can be imported and called with parameters.
	
	Args:
		base_dir: Base directory path
		parser_ref_path: Path to iedb_output_ref-parse_v0-1.pl
		parser_v05_path: Path to iedb_output_parse_v0-5.pl
		ref_input_dir: Relative input directory for ref parser (e.g., "ref_output")
		ref_output_dir: Relative output directory for ref parser (e.g., "ref_parsed")
		query_input_dir: Relative input directory for query parser (e.g., "query_output")
		query_output_dir: Relative output directory for query parser (e.g., "query_parsed")
		percentile_threshold: Percentile threshold for v0-5 parser (default: "9")
	"""
	# Preserve previous outputs so rotation can archive into run_1/run_2/run_3
	
	# Pass relative dirs from project root: run ref parser first
	_run_parser(base_dir, parser_ref_path, ref_input_dir, ref_output_dir)
	# Then run v0-5 for query via temporary adjusted script
	_run_v05_for_query(base_dir, parser_v05_path, query_input_dir, query_output_dir, percentile_threshold)

	# Concatenate Global and Summary across sizes and add size column for Summary (ref)
	_concatenate_ref_outputs(base_dir, ref_output_dir)
	
	# Join query and ref outputs
	_join_query_ref_outputs(base_dir, query_output_dir, ref_output_dir)


def _concatenate_ref_outputs(base_dir: Path, ref_output_dir: str) -> None:
	"""Concatenate ref parser outputs across sizes."""
	store = base_dir / f"{ref_output_dir}/outfile_store"
	global_targets = [
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.8.csv",
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.9.csv",
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.10.csv",
	]
	global_out = store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.csv"
	with global_out.open("w") as go:
		wrote_header = False
		for f in global_targets:
			if not f.exists():
				continue
			with f.open() as fh:
				for i, line in enumerate(fh):
					if i == 0:
						if not wrote_header:
							go.write(line.rstrip() + "\n")
							wrote_header = True
						continue
					if line.strip():
						go.write(line.rstrip() + "\n")

	summary_targets = [
		store / "Summary_IEDB_anticancer_test-ref_anticancer_test.8.csv",
		store / "Summary_IEDB_anticancer_test-ref_anticancer_test.9.csv",
		store / "Summary_IEDB_anticancer_test-ref_anticancer_test.10.csv",
	]
	summary_out = store / "Summary_IEDB_anticancer_test-ref_anticancer_test.csv"
	with summary_out.open("w") as so:
		wrote_header = False
		for f in summary_targets:
			size = None
			name = f.name
			if name.endswith(".8.csv"):
				size = 8
			elif name.endswith(".9.csv"):
				size = 9
			elif name.endswith(".10.csv"):
				size = 10
			if not f.exists():
				continue
			with f.open() as fh:
				for i, line in enumerate(fh):
					line = line.rstrip("\n")
					if i == 0:
						cols = line.split(",")
						if not wrote_header:
							try:
								idx = cols.index("Peptide") + 1
							except ValueError:
								idx = 3
							cols.insert(idx, "Epitope size (X-mer)")
							so.write(",".join(cols) + "\n")
							wrote_header = True
						continue
					if not line.strip():
						continue
					cols = line.split(",")
					try:
						idx = cols.index("Peptide") + 1
					except ValueError:
						idx = 3
					cols.insert(idx, str(size) if size is not None else "")
					so.write(",".join(cols) + "\n")

def _join_query_ref_outputs(base_dir: Path, query_output_dir: str, ref_output_dir: str) -> None:
	"""Join query and ref outputs using pandas."""
	# NEW: Join query homology Summary with ref Summary and write to query-ref_parsed
	query_summary = base_dir / f"{query_output_dir}/homology_output/Summary_IEDB_anticancer_summary.csv"
	ref_summary = base_dir / f"{ref_output_dir}/outfile_store/Summary_IEDB_anticancer_test-ref_anticancer_test.csv"
	if query_summary.exists() and ref_summary.exists():
		query_df = pd.read_csv(query_summary)
		ref_df = pd.read_csv(ref_summary)
		# Prepare minimal ref columns for join (add Method)
		ref_keep = ref_df[["HLA genotype", "Method", "Peptide", "Percentile"]].copy()
		ref_keep = ref_keep.rename(columns={"Percentile": "Ref Percentile"})
		# Merge on Peptide directly (not on reference peptide columns)
		result = query_df.merge(ref_keep, how="left",
			left_on=["HLA genotype", "Method", "Peptide"],
			right_on=["HLA genotype", "Method", "Peptide"],
			suffixes=("", "_ref"))
		# Compute Percentile Delta = Percentile - Ref Percentile (keep negatives)
		def _delta(row):
			try:
				rp = row.get("Ref Percentile")
				qp = row.get("Percentile")
				if pd.isna(rp) or pd.isna(qp):
					return ""
				return float(qp) - float(rp)
			except Exception:
				return ""
		result["Percentile Delta"] = result.apply(_delta, axis=1)
		out_dir = base_dir / "query-ref_parsed"
		out_dir.mkdir(parents=True, exist_ok=True)
		out_path = out_dir / "Summary_IEDB_anticancer_query_ref.csv"
		result.to_csv(out_path.as_posix(), index=False)
		print(f"Wrote joined query-ref summary → {out_path}")

	# NEW: Do the same join for the Global files (homology_output vs ref outfile_store)
	query_global = base_dir / f"{query_output_dir}/homology_output/Global_IEDB_out_anticancer_summary.csv"
	ref_global = base_dir / f"{ref_output_dir}/outfile_store/Global_IEDB_out_anticancer_test-ref_anticancer_test.csv"
	if query_global.exists() and ref_global.exists():
		qg = pd.read_csv(query_global)
		rg = pd.read_csv(ref_global)
		# Keep ref Percentile with keys (add Method)
		rg_keep = rg[["HLA genotype", "Method", "Peptide", "Percentile"]].copy()
		rg_keep = rg_keep.rename(columns={"Percentile": "Ref Percentile"})
		# Merge on Peptide directly (not on reference peptide columns)
		g_join = qg.merge(rg_keep, how="left",
			left_on=["HLA genotype", "Method", "Peptide"],
			right_on=["HLA genotype", "Method", "Peptide"],
			suffixes=("", "_ref"))
		# Compute Percentile Delta = Percentile - Ref Percentile
		def _gdelta(row):
			try:
				rp = row.get("Ref Percentile")
				qp = row.get("Percentile")
				if pd.isna(rp) or pd.isna(qp):
					return ""
				return float(qp) - float(rp)
			except Exception:
				return ""
		g_join["Percentile Delta"] = g_join.apply(_gdelta, axis=1)
		out_dir = base_dir / "query-ref_parsed"
		out_dir.mkdir(parents=True, exist_ok=True)
		g_out = out_dir / "Global_IEDB_out_anticancer_query_ref.csv"
		g_join.to_csv(g_out.as_posix(), index=False)
		print(f"Wrote joined query-ref global → {g_out}")


def main() -> None:
	"""Standalone main function for running v0-2 directly."""
	import os
	base_dir = Path(os.getenv("BASE_DIR", "/Users/michael_gaunt/Desktop/Anastasia"))
	parser_ref = base_dir / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl"
	parser_v05 = base_dir / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl"
	run_parsing_pipeline(
		base_dir=base_dir,
		parser_ref_path=parser_ref,
		parser_v05_path=parser_v05,
		ref_input_dir="ref_output",
		ref_output_dir="ref_parsed",
		query_input_dir="query_output",
		query_output_dir="query_parsed",
		percentile_threshold="9"
	)


if __name__ == "__main__":
	main()


