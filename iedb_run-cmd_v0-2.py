"""
Parsing pipeline for IEDB outputs.
Handles ref and query parsing with pandas joins.

author: Michael W. Gaunt, Ph.D
"""
import os
import re
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


def _run_v05_for_query(base_dir: Path, parser_v05_path: Path, query_input_dir: str, query_output_dir: str, percentile_threshold: str = "2.5") -> None:
	"""Run v0-52 parser for query output (Class II format).
	
	Args:
		base_dir: Base directory path
		parser_v05_path: Path to iedb_output_parse_v0-52.pl
		query_input_dir: Relative input directory (e.g., "query_output")
		query_output_dir: Relative output directory (e.g., "query_parsed")
		percentile_threshold: Percentile threshold (default: "2.5" for Class II)
	"""
	# v0-52.pl expects: OUTPUT_DIR (ARGV[0]), INPUT_DIR (ARGV[1]), PERCENTILE_THRESHOLD (ARGV[2]), HOMOLOGY_THRESHOLD (ARGV[3])
	# Uses CLI_INPUT_DIR like v0-12.pl - no temp file modification needed
	# Prepare output dir and rotate
	query_out = base_dir / query_output_dir
	query_out.mkdir(parents=True, exist_ok=True)
	_rotate_runs(query_out)
	# Pass BASE_DIR as environment variable for Perl scripts
	env = os.environ.copy()
	env['BASE_DIR'] = base_dir.as_posix()
	# v0-52.pl expects: OUTPUT_DIR, INPUT_DIR, PERCENTILE_THRESHOLD (optional)
	cmd = ["perl", parser_v05_path.as_posix(), query_output_dir, query_input_dir, percentile_threshold]
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), env=env, text=True, capture_output=True)
	if completed.stdout:
		print(completed.stdout, end="")
	if completed.stderr:
		print(completed.stderr, end="")
	if completed.returncode != 0:
		raise SystemExit(completed.returncode)


def run_parsing_pipeline(base_dir: Path, parser_ref_path: Path, parser_v05_path: Path, ref_input_dir: str, ref_output_dir: str, query_input_dir: str, query_output_dir: str, percentile_threshold: str = "2.5") -> None:
	"""Main parsing pipeline function that can be imported and called with parameters.
	
	Args:
		base_dir: Base directory path
		parser_ref_path: Path to iedb_output_ref-parse_v0-12.pl (Class II)
		parser_v05_path: Path to iedb_output_parse_v0-52.pl (Class II)
		ref_input_dir: Relative input directory for ref parser (e.g., "ref_output")
		ref_output_dir: Relative output directory for ref parser (e.g., "ref_parsed")
		query_input_dir: Relative input directory for query parser (e.g., "query_output")
		query_output_dir: Relative output directory for query parser (e.g., "query_parsed")
		percentile_threshold: Percentile threshold for v0-52 parser (default: "2.5" for Class II)
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
	"""Concatenate ref parser outputs across sizes (Class II format: 15-20).
	
	NOTE: CONCATENATION ERROR RESOLUTION (Nov 2024):
	The ref parser (iedb_output_ref-parse_v0-12.pl) creates concatenated files
	by appending to Summary_IEDB_anticancer_summary.csv and Global_IEDB_out_anticancer_summary.csv
	using append mode (>>). However, this was found to only include the last processed size
	(e.g., only 16-mer peptides, missing all 15-mer peptides).
	
	This function now ALWAYS re-concatenates from size-specific files (e.g., *.15.csv, *.16.csv)
	using pandas, ensuring all sizes are properly included. This fix ensures that the join operation
	has complete reference data for matching query peptides across all epitope sizes.
	
	The concatenated files are recreated even if they already exist, to prevent incomplete
	data from being used in downstream joins.
	"""
	store = base_dir / f"{ref_output_dir}/outfile_store"
	# Class II uses sizes 15-20, file names are like:
	# Global_IEDB_out_anticancer_summary.15.csv, Global_IEDB_out_anticancer_summary.16.csv, etc.
	# Summary_IEDB_anticancer_summary.15.csv, Summary_IEDB_anticancer_summary.16.csv, etc.
	global_targets = [
		store / "Global_IEDB_out_anticancer_summary.15.csv",
		store / "Global_IEDB_out_anticancer_summary.16.csv",
		store / "Global_IEDB_out_anticancer_summary.17.csv",
		store / "Global_IEDB_out_anticancer_summary.18.csv",
		store / "Global_IEDB_out_anticancer_summary.19.csv",
		store / "Global_IEDB_out_anticancer_summary.20.csv",
	]
	# Always re-concatenate from size-specific files (v0-12.pl may create incomplete concatenated file)
	global_out = store / "Global_IEDB_out_anticancer_summary.csv"
	# Use pandas to properly concatenate (handles headers and ensures all rows are included)
	gdfs = []
	for f in global_targets:
		if f.exists():
			df = pd.read_csv(f)
			gdfs.append(df)
	if gdfs:
		combined = pd.concat(gdfs, ignore_index=True)
		combined.to_csv(global_out, index=False)
		print(f"[concatenate] Re-created {global_out.name} with {len(combined)} rows from {len(gdfs)} size-specific files")
	else:
		# Fallback to old method if pandas not available or no files found
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
		store / "Summary_IEDB_anticancer_summary.15.csv",
		store / "Summary_IEDB_anticancer_summary.16.csv",
		store / "Summary_IEDB_anticancer_summary.17.csv",
		store / "Summary_IEDB_anticancer_summary.18.csv",
		store / "Summary_IEDB_anticancer_summary.19.csv",
		store / "Summary_IEDB_anticancer_summary.20.csv",
	]
	# Always re-concatenate from size-specific files (v0-12.pl may create incomplete concatenated file)
	# This ensures all sizes are included, not just the last one processed
	summary_out = store / "Summary_IEDB_anticancer_summary.csv"
	# Use pandas to properly concatenate (handles headers and ensures all rows are included)
	dfs = []
	for f in summary_targets:
		if f.exists():
			df = pd.read_csv(f)
			dfs.append(df)
	if dfs:
		combined = pd.concat(dfs, ignore_index=True)
		combined.to_csv(summary_out, index=False)
		print(f"[concatenate] Re-created {summary_out.name} with {len(combined)} rows from {len(dfs)} size-specific files")
	else:
		# Fallback to old method if pandas not available or no files found
		with summary_out.open("w") as so:
			wrote_header = False
			for f in summary_targets:
				size = None
				name = f.name
				# Extract size from filename like "Summary_IEDB_anticancer_summary.15.csv"
				match = re.search(r'\.(\d+)\.csv$', name)
				if match:
					size = int(match.group(1))
				if not f.exists():
					continue
				with f.open() as fh:
					for i, line in enumerate(fh):
						line = line.rstrip("\n")
						if i == 0:
							cols = line.split(",")
							if not wrote_header:
								# Check if "Epitope size (X-mer)" column already exists
								if "Epitope size (X-mer)" not in cols:
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
						# Check if size column already exists
						if "Epitope size (X-mer)" not in line and size is not None:
							try:
								idx = cols.index("Peptide") + 1
							except ValueError:
								idx = 3
							cols.insert(idx, f"{size}-mer")
						so.write(",".join(cols) + "\n")

def _join_query_ref_outputs(base_dir: Path, query_output_dir: str, ref_output_dir: str) -> None:
	"""Join query and ref outputs using pandas (Class II format)."""
	# Join query homology Summary with ref Summary and write to query-ref_parsed
	query_summary = base_dir / f"{query_output_dir}/homology_output/Summary_IEDB_anticancer_summary.csv"
	ref_summary = base_dir / f"{ref_output_dir}/outfile_store/Summary_IEDB_anticancer_summary.csv"
	if query_summary.exists() and ref_summary.exists():
		query_df = pd.read_csv(query_summary)
		ref_df = pd.read_csv(ref_summary)
		# Prepare minimal ref columns for join (add Method) - Class II has Adjusted Percentile
		# Use Adjusted Percentile if available, otherwise Percentile
		ref_cols = ["HLA genotype", "Method", "Peptide"]
		if "Adjusted Percentile" in ref_df.columns:
			ref_cols.append("Adjusted Percentile")
			ref_keep = ref_df[ref_cols].copy()
			ref_keep = ref_keep.rename(columns={"Adjusted Percentile": "Ref Adjusted Percentile"})
		else:
			ref_cols.append("Percentile")
			ref_keep = ref_df[ref_cols].copy()
			ref_keep = ref_keep.rename(columns={"Percentile": "Ref Percentile"})
		# Merge on Peptide directly (not on reference peptide columns)
		result = query_df.merge(ref_keep, how="left",
			left_on=["HLA genotype", "Method", "Peptide"],
			right_on=["HLA genotype", "Method", "Peptide"],
			suffixes=("", "_ref"))
		# Compute Percentile Delta - use Adjusted Percentile if available
		def _delta(row):
			try:
				# Try Adjusted Percentile first (Class II), fallback to Percentile
				if "Ref Adjusted Percentile" in row and not pd.isna(row.get("Ref Adjusted Percentile")):
					rp = row.get("Ref Adjusted Percentile")
					qp = row.get("Adjusted Percentile") if "Adjusted Percentile" in row else row.get("Percentile")
				else:
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

	# Do the same join for the Global files (homology_output vs ref outfile_store)
	query_global = base_dir / f"{query_output_dir}/homology_output/Global_IEDB_out_anticancer_summary.csv"
	ref_global = base_dir / f"{ref_output_dir}/outfile_store/Global_IEDB_out_anticancer_summary.csv"
	if query_global.exists() and ref_global.exists():
		qg = pd.read_csv(query_global)
		rg = pd.read_csv(ref_global)
		# Keep ref Percentile/Adjusted Percentile with keys (add Method) - Class II
		rg_cols = ["HLA genotype", "Method", "Peptide"]
		if "Adjusted Percentile" in rg.columns:
			rg_cols.append("Adjusted Percentile")
			rg_keep = rg[rg_cols].copy()
			rg_keep = rg_keep.rename(columns={"Adjusted Percentile": "Ref Adjusted Percentile"})
		else:
			rg_cols.append("Percentile")
			rg_keep = rg[rg_cols].copy()
			rg_keep = rg_keep.rename(columns={"Percentile": "Ref Percentile"})
		# Merge on Peptide directly (not on reference peptide columns)
		g_join = qg.merge(rg_keep, how="left",
			left_on=["HLA genotype", "Method", "Peptide"],
			right_on=["HLA genotype", "Method", "Peptide"],
			suffixes=("", "_ref"))
		# Compute Percentile Delta - use Adjusted Percentile if available (Class II)
		def _gdelta(row):
			try:
				# Try Adjusted Percentile first (Class II), fallback to Percentile
				if "Ref Adjusted Percentile" in row and not pd.isna(row.get("Ref Adjusted Percentile")):
					rp = row.get("Ref Adjusted Percentile")
					qp = row.get("Adjusted Percentile") if "Adjusted Percentile" in row else row.get("Percentile")
				else:
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


