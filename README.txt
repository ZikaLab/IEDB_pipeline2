IEDB Next-Generation Tools T Cell Class II - version 0.2.2 beta
============================================================

Introduction
------------
This package contains a collection of prediction tools for MHC class II peptide:MHC
binding, elution, immunogenicity, and antigen processing prediction.  It is a mixture
of Python scripts and AMD64 Linux-specific binaries and Docker containers.  This
standalone tool handles most of the data processing for the T Cell Class II
tool at https://nextgen-tools.iedb.org/pipeline?tool=tc2.

Basic functionality for running individual binding/elution, immunogenicity, and
antigen processing predictions is supported through the command line interface.
More advanced functionality for splitting and aggregating jobs is supported, but
not recommended for non-IEDB staff with this early release.  Future releases
may include code to streamline this functionality for end users.


Release Notes
-------------
v0.1 beta   - Initial public beta release
v0.1.1 beta - fix an issue regarding duplicate peptides in different input sequences/positions
v0.2 beta - add support for MHCII-NP
v0.2.1 beta - update allele validation for NetMHCIIpan version 4.2 and 4.3
v0.2.2 beta - update column order for immunogenicity output

Prerequisites
-------------

The following prerequisites must be met before installing the tools:

+ Linux 64-bit environment
  * http://www.ubuntu.com/
    - This distribution has been tested on Linux/Ubuntu 64 bit system.

+ Python 3.8 or higher
  * http://www.python.org/

+ tcsh
  * http://www.tcsh.org/Welcome
    - Under ubuntu: sudo apt-get install tcsh

+ gawk
  * http://www.gnu.org/software/gawk/
    - Under ubuntu: sudo apt-get install gawk

Optional:

+ Docker
  Docker Engine is required for running MHC-NP and MHCflurry
  * https://docs.docker.com/engine/install/


Installation
------------

Below, we will use the example of installing to ~/iedb_tools.

1. Extract the code and change directory: 
  $ mkdir ~/iedb_tools
  $ tar -xvzf IEDB_NG_TC2-VERSION.tar.gz -C ~/iedb_tools
  $ cd ~/iedb_tools/ng_tc2-VERSION


2. Optionally, create and activate a Python 3.8+ virtual environment using your favorite virtual environment manager.  Here, we will assume the virtualenv is at ~/virtualenvs/tc1:
  $ python3 -m venv ~/venvs/tc2
  $ source ~/venvs/tc2/bin/activate

3. Install python requirements:
  $ pip install -r requirements.txt

3a. On some versions of python, it may be necessary to constrain the version of cython that is used. If you have difficulty installing, try the following alternative command:
  $ PIP_CONSTRAINTS=pip_constraints.txt pip install -r requirements.txt


Usage
-----

python3 src/tcell_mhcii.py [-j] <input_json_file> [-o] <output_prefix> [-f] <output_format>

  * output_format: tsv (default), json

Example: python3 src/tcell_mhcii.py  -j examples/netmhciipan.json -o output -f json

Run the following command, or see the 'example_commands.txt' file in the 'src'
directory for typical usage examples:

python3 src/tcell_mhcii.py -h

All of the methods support input parameters via a JSON file.  Several of the
binding methods also support passing parameters in the command line
and we aim to improve support for this in the future.  See the 'caveats' section
below.


Input formats
-------------
Inputs may be specified in JSON format.  See the JSON files in the 'examples'
directory.  When multiple methods are selected, jobs will be run serially and
the output will be concatenated.  This can be avoided with the '--split' and 
'--aggregate' workflow which is described below, but currently only supported
for internal IEDB usage.

Here is an example JSON that illustrates the basic format:

{
"peptide_list": ["MGQIVTMFEALPHII", "ALPHIIDEVINIVII", "VINIVIIVLIVITGI"],
"peptide_length_range": [],
"alleles": "DRB1*01:01,DRB1*01:02,DRB1*01:03",
  "predictors": [
    {
      "type": "binding",
      "method": "netmhciipan_el"
    }
  ]
}

* peptide_list: A list of peptides for which to predict
* alleles: A comma-separated string of alleles
* predictors: A list of individual predictors to run.  See the file 
    examples/input_sequence_text.json for a list of all possible
    predictors and options.  Multiple predictors may be specified.

As an alternative to providing a peptide list, sequences can be provided
as a fasta string with the 'input_sequence_text' parameter and will be
broken down into peptides based on the peptide_length_range parameter, e.g.:

{
"input_sequence_text": ">LCMV Armstrong, Protein GP\nMGQIVTMFEALPHIIDEVINIVIIVLIVITGI",
"peptide_length_range": [
  15,
  15
],
"alleles": "DRB1*01:01,DRB1*01:02,DRB1*01:03",
  "predictors": [
    {
      "type": "binding",
      "method": "netmhciipan_el"
    }
  ]
}


Job splitting and aggregation
-----------------------------
*NOTE that this is an experimental workflow and this package does not contain
the code to automate job submission and aggregation.  Currently this is for
IEDB internal usage only*

Prediction jobs with multiple methods, alleles, lengths are good candidates for
splitting into smaller units for parallelization.  Using the '--split' option,
a job will be decomposed into units that are efficient for processing.

A 'job_description.json' file will be created that will describe the commands
needed to run each individual job, its dependencies, and the expected outputs. 
Each job can be executed as job dependencies are satisfied.  The job description
file will also contain an aggregation job, that will combine all of the
individual outputs into one JSON file.


Run tests
---------
This project includes a testing script and a directory for test data to verify the code is working as expected.

Files and Directories
cmd_test.py: This Python script is used to test the command-line commands of the project. It runs various tests to ensure the code is working correctly.
test_data/: This directory contains all the input and expected output files used by cmd_test.py for testing purposes.

How to Run Tests
To run the tests, execute the cmd_test.py script. It will read the input files from the test_data directory, execute the corresponding commands, and compare the actual outputs with the expected outputs:

python3 cmd_test.py


Caveats
-------
All IEDB next-generation standalones have been developed with the primary
focus of supporting the website.  Some user-facing features may be lacking,
but will be improved as these tools mature.


Contact
-------
Please contact us with any issues encountered or questions about the software
through any of the channels listed below.

IEDB Help Desk: https://help.iedb.org/
Email: help@iedb.org
