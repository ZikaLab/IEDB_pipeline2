# IEDB pipeline
The scripts form a two part data pipeline held under the GNU General Public License v3.0. Together the code automates screening the flavivirus genome for putative shared CD8 epitopes between ZIKV and other mosquito-borne flaviviruses (MBFV). The pipeline uses the IEDB MHC-I binding prediction tools, and requires a download version of this API which is available here http://tools.iedb.org/static/main/binding_data_2013.zip. 

The code is written in 'modern Perl5', requiring v5.14 or above (command "perl -v to check) and the first stage of data pipeline iedb_alignment_run.pl passes all viruses in any pre-specified number of alignments into the MHC-I binding prediction tools API. 

The second stage of the code iedb_output_parse.pl, parses and analyses the output of IEDB to assess the percentage amino acid identity between a shared CD8 epitope between ZIKV and a given MBFV, and the total number of shared epitopes above a percentage threshold. 

Full methodological details are found in Gaunt et al (submitted) "Zika and related viruses are hybrids of B-cell and T-cell loci from Aedes- and Culex-borne viruses respectively" 
