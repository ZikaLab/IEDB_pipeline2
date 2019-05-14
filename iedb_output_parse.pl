#!/usr/local/bin/perl
use strict;
use warnings;

#####################################################################################################
#####################################################################################################
#### The alignment MUST EXACTLY of format Virus_name(tab)sequence any variation will be identified ##
#### by incongruence in the "triple verified" array JE_057434_EF623988, KU365778_Zika_BeH819015	   ##
#### The reference sequences used are 'JE_057434_EF623988', 'KU365778_Zika_BeH819015'			   ##
#####################################################################################################
#####################################################################################################

=begin genotype_list
SE Asian 
my @cd8_library = ('HLA-B*40:01', 'HLA-A*24:02', 'HLA-A*11:01');
my $cd8_type = 'SEAsia_';
my $cd8_old = '';

non-SE Asian
my @cd8_library = ('HLA-A*26:01', 'HLA-B*35:01', 'HLA-B*07:02', 'HLA-A*01:01', 'HLA-A*02:01', 'HLA-B*15:01', 'HLA-B*08:01', 'HLA-B*38:01', 'HLA-A*30:01');
my @cd8_library = ('HLA-A*26:01', 'HLA-B*35:01', 'HLA-B*07:02', 'HLA-A*01:01', 'HLA-A*02:01', 'HLA-B*15:01', 'HLA-B*08:01', 'HLA-B*38:01', 'HLA-A*30:01');

Total
my @cd8_library = ('HLA-B*40:01', 'HLA-A*26:01', 'HLA-A*11:01', 'HLA-A*24:02', 'HLA-B*35:01', 'HLA-B*07:02', 'HLA-A*01:01', 'HLA-A*02:01', 'HLA-B*15:01', 'HLA-B*08:01', 'HLA-B*38:01', 'HLA-A*30:01');
=cut

my @cd8_library = ('HLA-A*26:01', 'HLA-B*35:01', 'HLA-B*07:02', 'HLA-A*01:01', 'HLA-A*02:01', 'HLA-B*15:01', 'HLA-B*08:01', 'HLA-B*38:01', 'HLA-A*30:01');
my $cd8_type = 'worldwide44otrovez2-5_';
# my $cd8_type = 'SEAsia55-4_';

my %master_files = ( 
#	'/iedb_NS2a-DEAD/' => 'NS2a_2b_NS3S7-DEDX_HELICc5prime2.phy',
#	'/iedb_NS4b/' => 'FLAVI_gen100_NS4b-CUT.phy',
#	'/iedb_NS1-HELICc2/' => 'ZIKV_gen100_NS1-HELICc.phy',
#	'/iedb_E/' => 'FLAVI_gen100_E-CUT.phy',
#	'/iedb_NS4a/' => 'NS4a-ridge-162-3pri-.phy',
#	'/iedb_PrM2/' => 'ZIKV_gen100_PrM.phy',
	'/iedb_NS5-C/' => 'ZIKV_gen100-C_NS5.phy'
	);

	
main ();

sub main { 
	for my $directory (sort keys %master_files){
			my $align = $master_files{$directory};
		for my $store_no (8..10){
			my $iedb_out = $here . $directory . "store_" . $store_no . '/';
			my %hash_counts; 
			my $flag = 0;   
			my ($loci, $size, $outfile, $summary);		
			file_begin ($align, $iedb_out, $flag, $cd8_type);
foreach my $cd8 (@cd8_library){
			my ($alignment_, $locus_) = load_align (\$align_loc, \$align, \$cd8);
			my $iedb_parsed = parse_iedb($iedb_out, $alignment_, $cd8);
			my $iedb_true_loc = epitope_locations ($iedb_parsed, $cd8);
			my $iedb_prot_id = amino_acid_diffs ($iedb_true_loc, $cd8);
			my $iedb_final_db = epitope_reference_match ($iedb_prot_id, $cd8);
			my $hash_counter;
			($loci, $size, $outfile, $summary, $hash_counter) = iedb_printout (\%hash_counts, $iedb_final_db, $cd8, $iedb_out, $locus_, $flag, $cd8_type);
			%hash_counts = %{$hash_counter};
			$flag = 1;
			}
my $summary_stuff = file_clean ($loci, $iedb_out, $size, $outfile, $summary, $cd8_type, $store_no);
final_average (\%hash_counts, $summary_stuff);
		}
	}
}

# Variable area 1
sub load_align {
 	my ($align_location, $align_, $cd8_) = @_;	
 	my %alignment;
 	(my $locus = $$align_) =~ s/\.phy//; 
	open (my $fh, '<', "$$align_location$$align_") or die "The original alignment file will not open\n" . "$!";
	my $header = <$fh>;
	while (<$fh>){
		my $line = $_;
		chomp $line;
		my ($virus, $data) = split ("\t", $line);
		chomp $virus;
	 	my $gap_positions = gaps ($data);
		(my $dealign = $data) =~ s/-//g;
# Note the variable $virus here is taken from the alignment name
		$alignment{$virus}->{'aligned_locus'} = $locus;
		$alignment{$virus}->{'gaps'} = $gap_positions;
		$alignment{$virus}->{'protein'} = $data;
		$alignment{$virus}->{'dealign_protein'} = $dealign;
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
		$alignment{$virus}->{$$cd8_}->{'amino_acid_homology'}->{'KU365778_Zika_BeH819015'} = (); 
		$alignment{$virus}->{$$cd8_}->{'amino_acid_homology'}->{'JE_057434_EF623988'} = ();
		$alignment{$virus}->{$$cd8_}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'} = (); 
		$alignment{$virus}->{$$cd8_}->{'amino_acid_identity'}->{'JE_057434_EF623988'} = (); 
		$alignment{$virus}->{$$cd8_}->{'amino_acid_differences'}->{'KU365778_Zika_BeH819015'} = ();
		$alignment{$virus}->{$$cd8_}->{'amino_acid_differences'}->{'JE_057434_EF623988'} = ();
	}
	close $fh;
	return (\%alignment, $locus);
}

sub gaps {
	my ($data_1) = @_;
	my $s = 0;
	my @c;
	my $i;
	for ( $i = 0; $i <= length($data_1); $i++ ) {
	    my $d = substr($data_1, $i, 1);
	    if ( $d eq "-" ) {
	        push( @c, $i + 1 );
		}
	}
	return \@c;
}


sub load_iedb {
	my ($input) = @_;
	opendir (my $fh1, "$input") or die "I can not find the infiles" . "$!";
#	my @rf = grep{/HLA/ && /\.csv/} readdir($fh1);
	my @rf = grep{/HLA/ && /\.csv/} readdir($fh1);
	closedir $fh1;
	return \@rf;
}


# Variable area 2
sub parse_iedb {
	my ($in, $alignment_2, $cd8_2) = @_;
#	my @iedb_files = @$in;
	my $iedb_files = load_iedb($in);
	foreach my $file (@$iedb_files){
		my @epitopes = (); my @epitope_loc = (); my @consensus = (); my @ANN = (); my @SMM = (); my @length = ();
		chomp $file;
		my $flag_virus = checker ($alignment_2, $file); 		
		next unless $flag_virus == 1;
		open (my $fh2, '<', "$in$file") or die "I can not find the IEDB output file" . "\t" . "$!";
 		
# Note the variable $virus_2 here is taken from the file name. The file and alignment name must match
# At line 141 there is a "next unless" statement, this could be re-written to "die" if the files do not match
 		(my $cd8_check = $file) =~ s/.*(HLA.*?)\+(\d+\:\d+)\..*/$1\*$2/;
 		(my $virus_2 = $file) =~ s/^(.+?)__.*/$1/;  # Critical for file / sequence matching
		my $header2 = <$fh2>;
#		eval {$cd8_check eq $cd8_2} or die "There is a bug Bud because the HLA types don\'t match \n" . "$!";
		next unless $cd8_check eq $cd8_2; 
		while (<$fh2>){
			my $results = $_;
			chomp $results;
#			next unless $results =~ m/^HLA/;
			(my $percentile = $results) =~ s/^HLA\-.+?(\t\d+){4}\t[\w|\?]*\t(\d+\.?\d*?)\t.*/$2/; # checked
			next unless $percentile <= "2.5001";
			(my $peptide = $results) =~ s/^HLA\-.+?(\t\d+){4}\t([\w|\?]*).*/$2/; # checked
			my $ann_;
			if ($results =~ m/^HLA\-.+?(\t\d+){4}(\t[\w|\?]*)\t\d+\.?\d*\t(\d+\.?\d*)\t.*/){
			($ann_ = $results) =~ s/^HLA\-.+?(\t\d+){4}(\t[\w|\?]*)\t\d+\.?\d*\t(\d+\.?\d*)\t.*/$3/; # checked
				} else {
				$ann_ = "0.0000";
				} 
			my $smm_;
			if ($results =~ m/^HLA\-.+?(\t\d+){4}(\t[\w|\?]*)(\t\d+.?\d*){3}\t(\d+\.?\d*)\t.*/){
			($smm_ = $results) =~ s/^HLA\-.+?(\t\d+){4}(\t[\w|\?]*)(\t\d+.?\d*){3}\t(\d+\.?\d*)\t.*/$4/; # checked
				} else {
			$smm_ = "0.0000";
			}
			(my $epi_size = $results) =~ s/^HLA\-.+?(\t\d+){3}\t(\d+)\t.*/$2/; # checked
			(my $epi_loc_begin = $results) =~ s/^HLA\-.+?(\t\d+){1}\t(\d+)\t.*/$2/; # checked
			(my $epi_loc_end = $results) =~ s/^HLA\-.+?(\t\d+){2}\t(\d+)\t.*/$2/; # checked
			push (@epitopes, $peptide);
			push (@length, $epi_size);
			push (@consensus, $percentile);
			push (@ANN, $ann_);
			push (@SMM, $smm_);
			my @tmp_array = ($epi_loc_begin, $epi_loc_end);
			push (@epitope_loc, \@tmp_array); 
			$alignment_2->{$virus_2}->{$cd8_2}->{'Epitopes'} = \@epitopes;
			$alignment_2->{$virus_2}->{$cd8_2}->{'Size'} = \@length;
			$alignment_2->{$virus_2}->{$cd8_2}->{'Consensus'} = \@consensus;
			$alignment_2->{$virus_2}->{$cd8_2}->{'ANN'} = \@ANN;
			$alignment_2->{$virus_2}->{$cd8_2}->{'SMM'} = \@SMM;
			$alignment_2->{$virus_2}->{$cd8_2}->{'Epitope_loc'} = \@epitope_loc;
		}
	}
	return $alignment_2;
}

sub checker {
		my ($alignment_2, $file_) = @_;
		my $flag_virus = 0;
		$file_ =~ s/(.*)__.*/$1/;
		foreach my $virus_check (keys %{$alignment_2}){
			next unless $file_ =~ m/$virus_check/;
			$flag_virus = 1;
		}
		return $flag_virus;
}

# Variable area 3
sub epitope_locations {
	my ($alignment_3, $cd8_3) = @_;
	for my $virus_3 (keys %$alignment_3){
	my @mrcool; my @triple_verified; my @error; my $i = 0; my $flag_3;
		next unless defined $alignment_3->{$virus_3}->{$cd8_3}->{'Epitopes'};
		foreach my $epitope_peptide (@{$alignment_3->{$virus_3}->{$cd8_3}->{'Epitopes'}}){
			my $epitope_value1 = index($alignment_3->{$virus_3}->{'protein'}, $epitope_peptide) + 1;
# Breakpoint here
			my $epitope_value2 = rindex($alignment_3->{$virus_3}->{'protein'}, $epitope_peptide) + 1;
			my $cool = $epitope_value1 if $epitope_value1 eq $epitope_value2;			
			$cool = $epitope_value1 . "-" . $epitope_value2 if $epitope_value1 != $epitope_value2;
			push (@mrcool, $cool);			
# Ident just to signify the use of a subroutine and the variables dependent on it afterwards
				my ($check_locus, $check_locus2, $flag_3) = check_epitope($virus_3, $alignment_3, $cd8_3, $i);
				if ($cool =~ m/-/){
				push (@triple_verified, $check_locus); # note this is a temporary fix to duplicated epitopes
				print "$virus_3 for allele $cd8_3 has a duplicate epitopes\.", "\n";
				} else {
				push (@triple_verified, $check_locus) if $check_locus == $cool;
				}
				my $tmp_val = "$epitope_value1" . "-" . "$epitope_value2" . "-" . "$check_locus" . "-" . "$check_locus2";
				push (@triple_verified, $tmp_val) if $epitope_value1 != $check_locus; 
				($triple_verified[$i] =~ m/-/ ? $flag_3 : $flag_3) = ($triple_verified[$i] =~ m/-/ ? 1 : 0);
				push (@error, $flag_3);
				$i++; $flag_3 = 0;
		}
			$alignment_3->{$virus_3}->{$cd8_3}->{'Index_epi_location'} = \@mrcool;
			$alignment_3->{$virus_3}->{$cd8_3}->{'Gold_location'} = \@triple_verified;
			$alignment_3->{$virus_3}->{$cd8_3}->{'Error'} = \@error;
	}
		return $alignment_3;
}

# Variable area 4
	sub check_epitope {
		my ($virus_4, $alignment_4, $cd8_4, $i_) = @_;
		my $counter = 0; my $flag_4;
		my $epi_loc = $alignment_4->{$virus_4}->{$cd8_4}->{'Epitope_loc'}->[$i_]->[0];
		my $epi_loc2 = $alignment_4->{$virus_4}->{$cd8_4}->{'Epitope_loc'}->[$i_]->[1];
		my $epi_loc2_store = $epi_loc2;
		foreach my $gap_loc (@{$alignment_4->{$virus_4}->{'gaps'}}){
			 if ($epi_loc <= $gap_loc) {last;} else {
				$epi_loc = $epi_loc + 1; $counter++;
			}
		}		
		foreach my $gap_loc (@{$alignment_4->{$virus_4}->{'gaps'}}){
			 if ($epi_loc2 <= $gap_loc) {last;} else {
				$epi_loc2 = $epi_loc2 + 1;
			}
		}
		return ($epi_loc, $epi_loc2, $flag_4);
	}

# I am duplicating the unfurling of the hash, rather than referencing it from within sub 
# Epitope_locations because I think it keeps the code cleaner. If I get chance I will write 
# a single subroutine to avoid this duplication.

# Variable area 5
sub amino_acid_diffs {
=pod rationale1
Here I convert between absolute amino acid position (without indels) and alignment position (with indels)
If alignment indels are present within the predicted epitope this will result in index and rindex = 0, the "check_epitope" 
subroutine will identify the correct epitope along with its indels. This leads to 3 scenarios:
1. Predicted epitope and target both contain indels (this subroutine identifies if their at identical sites). 
Conclusion, potential T-cell homologue.
2. Predicted epitope contains indels but the reference sequence does not. 
Conclusion invalid T-cell homologue.
3. Reference sequence contains indels but the predicted epitope does not.
Conclusion, invalid T-cell homogue.
=cut
    my ($alignment_5, $cd8_5) = @_;
    my @ZIKV_JEV = ('JE_057434_EF623988', 'KU365778_Zika_BeH819015');
	for my $virus_5 (keys %$alignment_5){	
		next unless defined $alignment_5->{$virus_5}->{$cd8_5}->{'Epitopes'};
		foreach my $reference (@ZIKV_JEV){
			my @homology = (); my @all_amino_acids_epitopes = (); my @final_homologue = (); my @aa_identity = (); my @differences; my @gap_epitope_reference = (); my $a = 0;
			my $ref_peptide = $alignment_5->{$reference}->{'protein'};
			my $target_peptide = $alignment_5->{$virus_5}->{'protein'};
			foreach my $epitope_peptide (@{$alignment_5->{$virus_5}->{$cd8_5}->{'Epitopes'}}){
				my $gap_ref_start; my $gap_ref_end; my $homologue_gap; my $target_gap; my $homologue;
				my $flag_5 = 0; 
				my $death_flag = 0; 

				my $multiply = $alignment_5->{$virus_5}->{$cd8_5}->{'Size'}->[0]; # Variable called $size_7 in variable area 7
				$epitope_peptide = 'X' x  $multiply if $epitope_peptide =~ /\d+/;
				my $ref_position = $alignment_5->{$virus_5}->{$cd8_5}->{'Gold_location'}->[$a];
=pod rationale2
If index and rindex = 0, then there must be indels within predicted epitope and thus the gap adjusted 
position is needed. $flag = 1 means there are gaps in the target peptide. Note, assessing whether the 
indels between the target and reference align is done manually post-print out. This allows verification 
of the positioning of indels within the putative epitope.
=cut
				chomp $ref_position;
				if ($ref_position =~ m/\d+\-\d+\-\d+\-\d+/){
					$flag_5 = 1;
					my ($a, $b, $gap_ref_start, $gap_ref_end) = split ("-", $ref_position);
					my $gap_length = ($gap_ref_end - $gap_ref_start) + 1;
					$homologue_gap = substr ($ref_peptide, $gap_ref_start - 1, $gap_length);
					$target_gap = substr ($target_peptide, $gap_ref_start - 1, $gap_length);
# Here the reference epitope has gaps otherwise an 'undef' blocks further calculations
					if ($homologue_gap =~ m/-/) {
							$homologue = $homologue_gap;
						} else {
						$death_flag = 1;
						$homologue = "undef";}
					($target_gap =~ m/-/ ? $epitope_peptide : $death_flag) = ($homologue_gap =~ m/-/ ? $target_gap : 1); ## Death flag
					push @gap_epitope_reference, $homologue_gap;
						} elsif ($flag_5 == 0) {
					$homologue = substr ($ref_peptide, $ref_position - 1, length($epitope_peptide));
					if (defined $homologue){
						push @gap_epitope_reference, "$homologue";} else {
						push @gap_epitope_reference, $epitope_peptide;}
						} else {
					$death_flag = 1;
					push @gap_epitope_reference, "-1";
					}
# If the reference sequence has gaps but the target sequences doesn't this is not considered a homologous epitope
					if ($homologue =~ m/-/ and $flag_5 == "0"){
						$death_flag = 1;
						}; ## Death flag
					my @target_peptide = split(//, $epitope_peptide);
			    	my @ref_peptide = split(//, $homologue) if defined ($homologue);
			    	my $counter = 0; 
			    	my $matches = 0;
					for (my $i = 0; $i <= $#target_peptide; $i++) {
						last unless $death_flag == 0; ## Death flag
						$target_peptide[$i] = 'X' unless defined $target_peptide[$i];
#						if($target_peptide[$i] eq "-" and $ref_peptide[$i] eq "-"){
#							next;}
						next if $target_peptide[$i] =~ m/-/;
						$counter++;
						if($target_peptide[$i] eq $ref_peptide[$i]){
							$matches++;
						}
					}
					if ($death_flag == 0){

						push @aa_identity, $matches;
						push @all_amino_acids_epitopes, $counter;
						push @homology, ($matches/$counter);
						push @differences, ($counter - $matches);
						push @final_homologue, $alignment_5->{$virus_5}->{$cd8_5}->{'Gold_location'}->[$a];
							} else {
						push @aa_identity, "0";
						push @homology, "0";
						push @differences, "0";
						push @final_homologue, "0";
						} 	 # Keep in mind numbers still carry "-"
					$a++; # check flag reset
        		}
				$alignment_5->{$virus_5}->{$cd8_5}->{'Epitope_homologue_penultimate'} = \@final_homologue;
				$alignment_5->{$virus_5}->{$cd8_5}->{'all_amino_acids_epitopes'}->{$reference}  = \@all_amino_acids_epitopes;
				$alignment_5->{$virus_5}->{$cd8_5}->{'amino_acid_homology'}->{$reference} = \@homology;
				$alignment_5->{$virus_5}->{$cd8_5}->{'amino_acid_identity'}->{$reference} = \@aa_identity;
				$alignment_5->{$virus_5}->{$cd8_5}->{'amino_acid_differences'}->{$reference} = \@differences;
				$alignment_5->{$virus_5}->{$cd8_5}->{'Indel_epitope_reference'}->{$reference} = \@gap_epitope_reference;
			}
		}
	return $alignment_5;
	}

# Variable area 6
sub epitope_reference_match {
	my ($alignment_6, $cd8_6) = @_;
	my @ZIKV_JEV = ('JE_057434_EF623988', 'KU365778_Zika_BeH819015');
####	my @ZIKV_JEV = ('KU365778_Zika_BeH819015');
	for my $virus_6 (keys %$alignment_6){
		foreach my $reference_ (@ZIKV_JEV){
			my @homologue_ = ();
			next unless defined $alignment_6->{$virus_6}->{$cd8_6}->{'Epitope_homologue_penultimate'};	
################### This is the first loop of a nested loop using the target #########################			
			foreach my $homologue_test (@{$alignment_6->{$virus_6}->{$cd8_6}->{'Epitope_homologue_penultimate'}}){
				my $flag_6 = 0; my $flag3_6 = 0; my $homologue_gap_end;

				if ($homologue_test =~ m /\d+\-\d+\-\d+\-\d+/){
				($homologue_gap_end = $homologue_test) =~ s/\d+\-\d+\-\d+\-(\d+)/$1/;
				$homologue_test =~ s/\d+\-\d+\-(\d+)\-\d+/$1/;
				$flag_6 = "1";
					} else {$flag_6 = 0;}
################## This is the second loop of a nested loop using the reference ##########################
				foreach my $homologue_ref (@{$alignment_6->{$reference_}->{$cd8_6}->{'Epitope_homologue_penultimate'}}){
					my $homologue_ref_gap_end; my $flag2_6 = 0;
						if ($homologue_ref =~ m /\d+\-\d+\-\d+\-\d+/){
							($homologue_ref_gap_end = $homologue_ref) =~ s/\d+\-\d+\-\d+\-(\d+)/$1/;
							$homologue_ref =~ s/\d+\-\d+\-(\d+)\-\d+/$1/;
							$flag2_6 = "1";
							} else {
						$homologue_ref_gap_end = $alignment_6->{$virus_6}->{$cd8_6}->{'Size'}->[0] + $homologue_ref - 1;}
						next unless $homologue_test == $homologue_ref;
						$flag3_6 = 1;
					 		if ($flag_6 == 1 and $flag2_6 == 1){				 			
								if ($homologue_ref_gap_end == $homologue_gap_end){
									push @homologue_, $homologue_test;
									} else {
									push @homologue_, 0;}
								} else {
								push @homologue_, $homologue_test;
							}
						}
######################## This is the end of the inner nest loop ########################					
							push (@homologue_, "0") if $flag3_6 == 0;
	}
########################### This is the end of the nested loop #########################					

			$alignment_6->{$virus_6}->{$cd8_6}->{'Epitope_homologue_confirmed'}->{$reference_} = \@homologue_;
			}
		}
	return $alignment_6;
	}

# Variable area 7
sub iedb_printout {
	my ($hash_counts_7, $alignment_7, $cd8_7, $dir_7, $locus, $flag_7, $cd8_type_7) = @_;
# Assigning the output file name
	(my $out_dir = $dir_7) =~ s/(.*\/).+?\/$/$1/;  
	(my $cd8_type_8 = $cd8_type_7) =~ s/(\w+)_/_$1/;
	my $outfile_fin = "$out_dir" . "Global_IEDB_out_" . "$locus" . "$cd8_type_8" . "\." . "---" . "\.csv";
	my $outfile_summary = "$out_dir" . "Summary_IEDB_" . "$locus" . "$cd8_type_8" . "\." . "---" . "\.csv";
	my $size_7;
# Deleting any possible pre-existing outfile

if ($flag_7==0){
	open (my $fhout2, '>>', $outfile_summary) or die "The data summary will not open\." . "$!", "\n";
	print $fhout2 'Virus strain', ",", 'HLA genotype', ",", 'Zika-like epitopes',",", 'ZIKV amino acid identity', ",", 'ZIKV amino acid diff', ",", 'Total amino acids', ",",  'Average', ",", 'JEV amino acid identify', 'JEV amino acid diffs', ",", 'Average JEV-like', "\n";
	close $fhout2;
}
	open (my $fhout, '>>', "$outfile_fin");
	print $fhout 'HLA genotype', ",", "Virus", ",", "Peptide", ",", "ZIKV ref", ",", "JEV ref", ",", 'Epitope loc.', ",", "Consensus", ",", "ANN", ",", "SMM", ",", '%age id ZIKV', ",", '%age ID JEV', ",",
	'No. ID aa with ZIKV', ",", 'No. diff vs ZIKV', ",", 
	'No. diff vs JEV', ",", 'No. ID aa with JEV',",", 
	"Homologue Zika", ",", "Homologue JEV", ",", "Check indels", "\n"  if $flag_7 == 0;
	
	foreach my $virus_7 (sort {$b cmp $a} keys %$alignment_7){
		my $no_amino_acid_diff = 0; my $identical_amino_acids = 0; my $JEV_identical_amino_acids = 0;  my $zika_no_epitopes = 0; my $virus_strain = 0; my $JEV_amino_acid_diff = 0; my $total_amino_acids = 0; my $total_JEV_amino_acids = 0;

		my $i_7 = 0;

		foreach my $peptide (@{$alignment_7->{$virus_7}->{$cd8_7}->{'Epitopes'}}){
			if ($alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_homology'}->{'KU365778_Zika_BeH819015'}->[$i_7] <= "0.440"){
				$i_7++;
				next;
				}
			if ($alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_confirmed'}->{'KU365778_Zika_BeH819015'}->[$i_7] <= 0){
			$i_7++;
			next;
			}
			unless	(defined $alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_confirmed'}->{'KU365778_Zika_BeH819015'}->[$i_7]){
			$i_7++;
			next;
			}						
			
printf $fhout <<"__EOFOO__", $cd8_7, $virus_7, $peptide, $alignment_7->{$virus_7}->{$cd8_7}->{'Indel_epitope_reference'}->{'KU365778_Zika_BeH819015'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Indel_epitope_reference'}->{'JE_057434_EF623988'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_penultimate'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Consensus'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'ANN'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'SMM'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_homology'}->{'KU365778_Zika_BeH819015'}->[$i_7]*100, $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_homology'}->{'JE_057434_EF623988'}->[$i_7]*100, $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_differences'}->{'KU365778_Zika_BeH819015'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'JE_057434_EF623988'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_differences'}->{'JE_057434_EF623988'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_confirmed'}->{'KU365778_Zika_BeH819015'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_confirmed'}->{'JE_057434_EF623988'}->[$i_7], $alignment_7->{$virus_7}->{$cd8_7}->{'Error'}->[$i_7];
%s,%s,%s,%s,%s,%d,%.3f,%.1f,%.1f,%.1f,%.1f,%d,%d,%d,%d,%d,%d,%d
__EOFOO__

		$size_7 = $alignment_7->{$virus_7}->{$cd8_7}->{'Size'}->[0];
			$zika_no_epitopes++ if $alignment_7->{$virus_7}->{$cd8_7}->{'Epitope_homologue_confirmed'}->{'KU365778_Zika_BeH819015'}->[$i_7] > 0;
			$no_amino_acid_diff += $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_differences'}->{'KU365778_Zika_BeH819015'}->[$i_7];
			$identical_amino_acids += $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'}->[$i_7] if defined $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'}->[$i_7];
#			$total_amino_acids += $size_7;
			$total_amino_acids += $alignment_7->{$virus_7}->{$cd8_7}->{'all_amino_acids_epitopes'}->{'KU365778_Zika_BeH819015'}->[$i_7] if defined $alignment_7->{$virus_7}->{$cd8_7}->{'all_amino_acids_epitopes'}->{'KU365778_Zika_BeH819015'}->[$i_7];
			$JEV_amino_acid_diff += $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_differences'}->{'JE_057434_EF623988'}->[$i_7];
			$JEV_identical_amino_acids += $alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'JE_057434_EF623988'}->[$i_7] if defined ($alignment_7->{$virus_7}->{$cd8_7}->{'amino_acid_identity'}->{'JE_057434_EF623988'}->[$i_7]);
			$total_JEV_amino_acids += $alignment_7->{$virus_7}->{$cd8_7}->{'all_amino_acids_epitopes'}->{'JE_057434_EF623988'}->[$i_7] if defined $alignment_7->{$virus_7}->{$cd8_7}->{'all_amino_acids_epitopes'}->{'JE_057434_EF623988'}->[$i_7];
			$i_7++;
		}
		
		print $virus_7, "\t", $cd8_7, "\t", $alignment_7->{$virus_7}->{'aligned_locus'}, "\t", $dir_7, "\n";
		
##########################################
## Cross check data for summary output	##
##########################################
		my ($identity_ref, $JEV_identity_ref, $average_aa, $JEV_average);
		######

		if (defined $JEV_identical_amino_acids){
			if (defined $total_JEV_amino_acids){
				$JEV_identical_amino_acids == "0" ? ($JEV_identity_ref = 0) : ($JEV_identity_ref = $JEV_identical_amino_acids);
				$JEV_identity_ref == 0 or $total_JEV_amino_acids == 0 ? ($JEV_average = 0) : ($JEV_average = $JEV_identity_ref / $total_JEV_amino_acids);
				$JEV_average = 0 unless defined $average_aa; 
				} else {
				$JEV_identical_amino_acids = 0;
				$JEV_average = 0;
				$JEV_identity_ref = $JEV_identical_amino_acids;
				}
		} else {
			$JEV_identity_ref = 0;
			$JEV_average = 0;		
			$JEV_amino_acid_diff = "undef";
			}

		$identity_ref = $identical_amino_acids;
		if (defined $identical_amino_acids){	
			if (defined $total_amino_acids) {
				$identity_ref == 0  or $total_amino_acids == 0 ? ($average_aa = 0) : ($average_aa = $identity_ref / $total_amino_acids);
				$average_aa = 0 unless defined $average_aa; 
				} else {
				$average_aa = 0;
				$total_amino_acids = "0";
				}
		} else {
			$identity_ref = 0;
			$average_aa = 0;
			$total_amino_acids = 0;
			$no_amino_acid_diff = "0";
		}
		
##############################
		
		open (my $fh_out2, '>>', $outfile_summary);
		print $fh_out2 $virus_7, ",", $cd8_7, ",", $zika_no_epitopes, ",", $identity_ref, ",", $no_amino_acid_diff, ",", $total_amino_acids, ",", $average_aa, ",", $JEV_identity_ref, ",", $JEV_amino_acid_diff, ",", $JEV_average, "\n";
		$hash_counts_7->{$virus_7}->{'ZIKV_aa_identity'} += $identity_ref if $zika_no_epitopes > 0;
		$hash_counts_7->{$virus_7}->{'ZIKV_aa_diff'} += $no_amino_acid_diff if $zika_no_epitopes > 0;
		$hash_counts_7->{$virus_7}->{'Total_aa'} += $total_amino_acids if $zika_no_epitopes > 0;
		$hash_counts_7->{$virus_7}->{'No_epitopes'} += $zika_no_epitopes if $zika_no_epitopes > 0;
		$hash_counts_7->{$virus_7}->{'JEV_aa_identity'} += $JEV_identity_ref if $zika_no_epitopes > 0;
		$hash_counts_7->{$virus_7}->{'JEV_aa_diff'} += $JEV_amino_acid_diff if $zika_no_epitopes > 0;
		close $fh_out2;
	}
	close $fhout;
	return ($locus, $size_7, $outfile_fin, $outfile_summary, $hash_counts_7);
}

sub file_begin {
	my ($locus_0, $dir_0, $flag_0, $cd8_type_) = @_;
	$locus_0 =~ s/\.phy//;
	(my $out_dir = $dir_0) =~ s/(.*\/).+?\/$/$1/; 
	my $store = $out_dir . $cd8_type_ . "outfile_store";
	system ("mkdir $store") unless -d $store;
}

# Variable zone 8
sub file_clean {
	my ($locus_8, $dir_8, $size_8, $outfile_8, $summary_8, $cd8_type_8, $store_no_8) = @_;
	$size_8 = $store_no_8 unless defined $size_8;
	print $size_8, "\n";
	(my $out_dir_8 = $dir_8) =~ s/(.*\/).+?\/$/$1/; 
	(my $cd8_type_9 = $cd8_type_8) =~ s/(\w+)_/_$1/;
	my $out_dir_9 = $out_dir_8 . $cd8_type_8 . 'outfile_store/';
	(my $summary_9 = $summary_8) =~ s/(.*Summary_IEDB_.*$locus_8$cd8_type_9\.)---(\.csv)/$1$size_8$2/;
	system ("mv $summary_8 $summary_9");
	system ("mv $summary_9 $out_dir_9");
	(my $outfile_9 = $outfile_8) =~ s/(.*Global_IEDB_out_.*$locus_8$cd8_type_9\.)---(\.csv)/$1$size_8$2/;
	system ("mv $outfile_8 $outfile_9");
	system ("mv $outfile_9 $out_dir_9");
	return $summary_9;
}

sub final_average {
	my ($hash_counts_, $summary_10) = @_;
	$summary_10 =~ s/Summary/Sum_totals/;
	my %hash_brown = %{$hash_counts_};
	open (my $fh_out3, '>', "$summary_10");
	print $fh_out3 'Virus', ",", 'Trans-ZIKV epitopes', ",", 'ZIKV aa identity', ",",'ZIK aa diffs', ",", 'Total aa', ",", 'JEV aa identity', ",", 'JEV aa diffs', "\n";
	foreach my $virus_key (sort {$b cmp $a} keys %hash_brown){
	print $fh_out3 $virus_key, ",", $hash_brown{$virus_key}->{'No_epitopes'}, ",", 	
	$hash_brown{$virus_key}->{'ZIKV_aa_identity'}, ",", 
	$hash_brown{$virus_key}->{'ZIKV_aa_diff'}, ",", 
	$hash_brown{$virus_key}->{'Total_aa'}, ",", 
	$hash_brown{$virus_key}->{'JEV_aa_identity'}, ",", 	
	$hash_brown{$virus_key}->{'JEV_aa_diff'}, "\n";
	}
	close $fh_out3;
	print "Calculation is completed" . "\n";
}

__END__
