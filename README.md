# IEDB_pipeline
A two part data pipeline held under the Gnu license for flavivirus genome screening of putative shared CD8 epitopes between ZIKV and other mosquito-borne flaviviruses. The pipeline automates the IEDB MHC-I binding prediction tools which is available here, http://tools.iedb.org/static/main/binding_data_2013.zip. 

The code is written in 'modern Perl5', requiring 5.14 or above (command "perl -v to check) and the first stage of data pipeline iedb_alignment_run.pl passes all viruses in any pre-specified number of alignments into the MHC-I binding prediction tools API


