#!/usr/local/bin/perl
use strict;
use warnings;
our VERSION = "2.3";
########################################################################################################
########################################################################################################
## The code is a two part program, which drives an amino acid alignment through IEDB, under a large	        ##
## variety of different parameters, including HLA genotypes and T-cell epitope size. Both CD8+ and 	            ##
## CD4+ epitopes could be analysed if required. The second script parses and analyses the IEDB		            ##
## output to derive a robust epitope prediction and secondly to carefully assess the potential of a                  ##
## ZIKV epitope to be a trans-species epitope. 														                                            ##
## Notes: 																							                                                               ##
## 1. The "load_align" subroutine generates a hash (database structure) of which many of the "keys"	           ##
##    (database tags) are only used for the parsing and analysis script (see point 5). 				                       ##
## 2. The alignment MUST BE EXACTLY of format ">virus_name(tab)sequence". Any variation from this     ##
##    format will be identified by incongruence in the "triple verified" array JE_057434_EF623988                  ##
##    and KU365778_Zika_BeH819015																	                                           ##
## 3. The reference sequences used are 'JE_057434_EF623988', 'KU365778_Zika_BeH819015'				  ##
## 4. One computer node will run the script for one ~70 taxon alignment for on HLA genotype within a        ##
##    reasonable time.																				                                                         ##
## 5. The script will likely be rewritten as a module to enable a seamless pipeline from amino acid              ##
##    alignment to trans-species epitope prediction.												                                         ##
########################################################################################################

my $align_loc = '/home/ipmbmgau/MHC-I/alignments/';
my $align = 'NS2a_2b_NS3S7-DEDX_HELICc5prime-.phy';
my @CD8_list = ('HLA-B*40:01');
my $iedb_out = '/home/ipmbmgau/MHC-I/mhc_i/iedb_output/';

main ();

sub main {    
	foreach my $cd8 (@CD8_list){
	my ($alignment_, $locus_) = load_align (\$align_loc, \$align, \$cd8);
	my $alignment_list = run_iedb ($alignment_, $locus_, $align_loc, $iedb_out, $cd8);
	printout($alignment_list, $locus_, $iedb_out, $cd8);
	exit 1;
	}
}
# This subroutine loads the alignment and creates a hash (database) 
# into which all relevant information will be stored. 
# The position of each gap is also stored. This is quite important 
# for later analysis in confirming the position of the epitope

sub load_align {
 	my ($align_location, $align_, $cd8_) = @_;	
 	my %alignment;
 	(my $locus = $$align_) =~ s/\.phy//; 
	open (my $fh, '<', "$$align_location$$align_") or die "The original alignment file will not open\n", "$!";
	<$fh>;
	while (my $line = <$fh>){
		my ($virus, $data) = split ("\t", $line);
		chomp $virus;
 		my $gap_positions = gaps ($data);
		(my $dealign = $data) =~ s/-//g;
# Note the variable $virus here is taken from the alignment name
		$alignment{$virus}->{'aligned_locus'} = $locus;
		$alignment{$virus}->{'gaps'} = $gap_positions;
		$alignment{$virus}->{'protein'} = $data;
		$alignment{$virus}->{'dealign_protein'} = $dealign;
# "Tags" (keys and values) hereon are not used in this script
		$alignment{$virus}->{$$cd8_}->{'ANN'} = ();
		$alignment{$virus}->{$$cd8_}->{'SMM'} = ();
		$alignment{$virus}->{$$cd8_}->{'Epitopes'} = ();
		$alignment{$virus}->{$$cd8_}->{'Epitope_loc'} = ();
		$alignment{$virus}->{$$cd8_}->{'Index_epi_location'} = ();
		$alignment{$virus}->{$$cd8_}->{'Size'} = ();
		$alignment{$virus}->{$$cd8_}->{'Consensus'} = (); 
		$alignment{$virus}->{$$cd8_}->{'Error'} = (); 
		$alignment{$virus}->{$$cd8_}->{'Gold_location'} = ();
		$alignment{$virus}->{$$cd8_}->{'Epitope_homologue_penultimate'} = ();
		$alignment{$virus}->{$$cd8_}->{'Epitope_homologue_confirmed'} = ();
		$alignment{$virus}->{$$cd8_}->{'Indel_epitope_reference'}->{'KU365778_Zika_BeH819015'} = ();
		$alignment{$virus}->{$$cd8_}->{'Indel_epitope_reference'}->{'JE_057434_EF623988'} = ();
		$alignment{$virus}->{$$cd8_}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'} = (); 
		$alignment{$virus}->{$$cd8_}->{'amino_acid_identity'}->{'JE_057434_EF623988'} = ();
		$alignment{$virus}->{$$cd8_}->{'amino_acid_differences'}->{'KU365778_Zika_BeH819015'} = ();
		$alignment{$virus}->{$$cd8_}->{'amino_acid_differences'}->{'JE_057434_EF623988'} = ();
		}
	close $fh;
	return (\%alignment, $locus);
}

sub gaps {
	my $data_1 = @_;
	my $s = 0;
	my @c;
	my $i;
	for ( $i = 0; $i < length($data_1); $i++ ) {
	    my $d = substr( $data_1, $i, 1 );
	    if ( $d eq "-" ) {
	        $s++;
	        push( @c, $i + 1 );
		}
	}
	return \@c;
}

# Variable area 0
sub run_iedb {
	my ($alignment_0, $locus_0, $align_loc_0, $iedb_out_0, $cd8_0) = @_;
	my @iedb_raw = ();
	my $dir_tmp = 'fa_tmp/';
	unless (-d "$iedb_out_0"){
		system("mkdir $iedb_out_0");
		system("mkdir $iedb_out_0$dir_tmp");
		 }
	foreach my $no (8..10){
	my $tag = "__" . "$cd8_0" . "\.$no" . "\.csv";
			foreach my $virus (keys %{$alignment_0}){
				(my $output = $virus) =~ s/(.+)/$1$tag/;
				$output =~ s/\*/\+/; # using globs (\*) within filenames causes mayhem, so it is substituted with "+" (and converted back again later)
				my $tmpf = $iedb_out_0 . $dir_tmp . "$virus\.fa";
				open(my $fhout, '>', "$tmpf") or die "Can not open the temporary outfile\.\n" . "$!";
				print $fhout "\>$virus\n", "$alignment_0->{$virus}->{'dealign_protein'}"; # it must be fasta format
				close $fhout;
################
## An exammple run command is: 
## "./src/predict_binding.py consensus HLA-A*02:01 9 ./examples/input_sequence.fasta"
## Note, File over-ride used because its one output per length per sequence per HLA type
################
			system ("/home/ipmbmgau/MHC-I/mhc_i/src/predict_binding.py consensus $cd8_0 $no $tmpf > $iedb_out_0$output"); 
#			system("rm $tmpf"); # Keep for now as it provides a log of activity
			push (@iedb_raw, "$iedb_out_0$output");
		}
	}	
	return \@iedb_raw;
}

sub printout {
	my ($in, $locus_00, $iedb_out_00, $cd8_00) = @_;
	my $outfile = "Total_MBFV_" . $locus_00 . $cd8_00 . "\.log";
	my $outlog = $iedb_out_00 . $outfile;
	system ("rm $outlog") if -e $outlog;
	open (my $fhout, '>>', "$outlog") or die "Can not open the temporary outfile\.\n" . "$!";
	print $fhout 'These proteins have been processed by IEDB for' . "$cd8_00" . ' and ' . "$locus_00\:\n";
	foreach my $f (@$in){
		print $fhout $f, "\n"; 
	}
	close $fhout;
}

__END__
