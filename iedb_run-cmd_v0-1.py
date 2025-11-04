import os
import shutil
import subprocess
from pathlib import Path


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
	cmd = [
		"perl",
		parser.as_posix(),
		output_dir,   # OUTPUT_DIR relative
		input_dir     # INPUT_DIR relative
	]
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), text=True, capture_output=True)
	if completed.stdout:
		print(completed.stdout, end="")
	if completed.stderr:
		print(completed.stderr, end="")
	if completed.returncode != 0:
		raise SystemExit(completed.returncode)

def _run_v04_for_query(base_dir: Path) -> None:
	"""Render a temp copy of v0-4 to point at query_output and run it for query_parsed."""
	v04 = base_dir / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-4.pl"
	tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v04.pl"
	text = v04.read_text()
	# Update master_files to query_output and keep absolute here
	text = text.replace("\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		"\t'/query_output/' => 'anticancer_test-ref.csv'")
	# Ensure output dir is CLI arg (already is in v0-4)
	tmp.write_text(text)
	# Prepare output dir and rotate
	query_out = base_dir / "query_parsed"
	query_out.mkdir(parents=True, exist_ok=True)
	_rotate_runs(query_out)
	cmd = ["perl", tmp.as_posix(), "query_parsed"]
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), text=True, capture_output=True)
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


def _run_v05_for_query(base_dir: Path) -> None:
	"""Render a temp copy of v0-5 to point at query_output and run it for query_parsed."""
	v05 = base_dir / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_parse_v0-5.pl"
	tmp = base_dir / "vendor/1_ng_tc1-0.1.2-beta/.tmp_query_v05.pl"
	text = v05.read_text()
	# Update master_files to query_output
	text = text.replace("\t'/dev_test_out-pl/' => 'anticancer_test-ref.csv'",
		"\t'/query_output/' => 'anticancer_test-ref.csv'")
	tmp.write_text(text)
	# Prepare output dir and rotate
	query_out = base_dir / "query_parsed"
	query_out.mkdir(parents=True, exist_ok=True)
	_rotate_runs(query_out)
	cmd = ["perl", tmp.as_posix(), "query_parsed"]
	completed = subprocess.run(cmd, cwd=base_dir.as_posix(), text=True, capture_output=True)
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


def main() -> None:
	base_dir = Path("/Users/michael_gaunt/Desktop/Anastasia")
	parser_ref = base_dir / "vendor/1_ng_tc1-0.1.2-beta/iedb_output_ref-parse_v0-1.pl"

	# Preserve previous outputs so rotation can archive into run_1/run_2/run_3

	# Pass relative dirs from project root: run ref parser first
	_run_parser(base_dir, parser_ref, "ref_output", "ref_parsed")
	# Then run v0-5 for query via temporary adjusted script
	_run_v05_for_query(base_dir)

	# Concatenate Global and Summary across sizes and add size column for Summary
	store = base_dir / "ref_parsed/outfile_store"
	global_targets = [
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.8.csv",
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.9.csv",
		store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.10.csv",
	]
	global_out = store / "Global_IEDB_out_anticancer_test-ref_anticancer_test.csv"
	# Write header from the first file and then append all rows except headers
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
	# Insert Epitope size (X-mer) as a column after Peptide
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
						# header
						cols = line.split(",")
						if not wrote_header:
							# insert Epitope size (X-mer) after Peptide
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
						idx = cols.index("Peptide") + 1  # won't be found in data rows
					except ValueError:
						# Data: columns: Virus strain,HLA genotype,Peptide,... so insert after 3rd col
						idx = 3
					cols.insert(idx, str(size) if size is not None else "")
					so.write(",".join(cols) + "\n")


if __name__ == "__main__":
	main()
