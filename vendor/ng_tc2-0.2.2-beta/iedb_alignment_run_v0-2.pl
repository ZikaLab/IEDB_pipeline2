#!/usr/local/bin/perl
# author: Michael W. Gaunt, Ph.D
# Main IEDB alignment runner - processes peptide sequences through IEDB predictors
use strict;
use warnings;
our $VERSION = "2.3";
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

my $parent_cwd = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} . '/' : '/Users/michael_gaunt/Desktop/Anastasia2/';
my $align_loc = $parent_cwd . 'data/';  # Point to data directory
my $align = 'anticancer_test.csv';  # Use CSV file from data directory

# Load CD8_list from params/CD_type.dat
my @CD8_list = load_cd8_list($parent_cwd);

# Load length range from params/length.dat (default: 15..20)
my ($length_min, $length_max) = load_length_range($parent_cwd);

#,'HLA-A*43:01','HLA-A*66:01','HLA-A*68:01','HLA-A*68:02','HLA-A*69:01','HLA-A*74:01','
#HLA-A*80:01','HLA-A*36:01','HLA-A*28:01','HLA-A*12:01','HLA-B*07:02','HLA-B*08:01','HLA-B*13:02','HLA-B*15:01','HLA-B*15:02','HLA-B*18:01','HLA-B*27:05','HLA-B*35:01','HLA-B*37:01','HLA-B*38:01','HLA-B*39:01','HLA-B*40:01','HLA-B*44:02','HLA-B*44:03','HLA-B*51:01','HLA-B*52:01','HLA-B*53:01','HLA-B*57:01','HLA-B*58:01');
my $iedb_out = $parent_cwd . 'dev_test_out-pl/';  # New output directory
# my @CD8_list = ('HLA-A*02:01', 'HLA-B*07:02');
main ();

sub load_cd8_list {
	my ($base_dir) = @_;
	my @cd8_default = ('HLA-A*01:01','HLA-A*02:01');
	
	my $params_file = $base_dir . 'params/CD_type.dat';
	unless (-f $params_file) {
		warn "Warning: $params_file not found, using default CD8_list\n";
		return @cd8_default;
	}
	
	my @cd8_list = ();
	open(my $fh, '<', $params_file) or do {
		warn "Warning: Cannot open $params_file: $!, using default CD8_list\n";
		return @cd8_default;
	};
	
	while (my $line = <$fh>) {
		chomp $line;
		$line =~ s/^\s+|\s+$//g;  # Trim whitespace
		next if $line =~ /^\s*$/;  # Skip empty lines
		next if $line =~ /^#/;     # Skip comments
		
		# Validate that value is in quotes
		unless ($line =~ /^'([^']+)'[,]?$/) {
			die "Error in $params_file: Values must be in single quotes. Found: $line\n";
		}
		
		my $allele = $1;
		push @cd8_list, $allele;
	}
	close $fh;
	
	if (scalar(@cd8_list) == 0) {
		warn "Warning: No valid CD8 entries found in $params_file, using default\n";
		return @cd8_default;
	}
	
	return @cd8_list;
}

sub load_length_range {
	my ($base_dir) = @_;
	my $length_min_default = 15;
	my $length_max_default = 20;
	
	my $params_file = $base_dir . 'params/length.dat';
	unless (-f $params_file) {
		warn "Warning: $params_file not found, using default range ($length_min_default..$length_max_default)\n";
		return ($length_min_default, $length_max_default);
	}
	
	open(my $fh, '<', $params_file) or do {
		warn "Warning: Cannot open $params_file: $!, using default range ($length_min_default..$length_max_default)\n";
		return ($length_min_default, $length_max_default);
	};
	
	my $line = <$fh>;
	close $fh;
	
	if (!$line) {
		warn "Warning: Empty $params_file, using default range ($length_min_default..$length_max_default)\n";
		return ($length_min_default, $length_max_default);
	}
	
	chomp $line;
	$line =~ s/^\s+|\s+$//g;
	
	# Parse format: "8, 11" or "8,11"
	if ($line =~ /^(\d+)\s*,\s*(\d+)$/) {
		my $min = $1;
		my $max = $2;
		unless ($min > 0 && $max >= $min) {
			die "Error in $params_file: Invalid range. min=$min, max=$max. min must be > 0 and max >= min\n";
		}
		return ($min, $max);
	} else {
		die "Error in $params_file: Invalid format. Expected 'min, max' (e.g., '8, 11'). Found: $line\n";
	}
}

sub main {    
	foreach my $cd4 (@CD8_list){
		my ($alignment_, $locus_) = load_align (\$align_loc, \$align, \$cd4);
		my $alignment_list = run_iedb ($alignment_, $locus_, $align_loc, $iedb_out, $cd4);
		printout($alignment_list, $locus_, $iedb_out, $cd4);
	}
}
# This subroutine loads the alignment and creates a hash (database) 
# into which all relevant information will be stored. 
# The position of each gap is also stored. This is quite important 
# for later analysis in confirming the position of the epitope

sub load_align {
 	my ($align_location, $align_, $cd4_) = @_;	
 	my %alignment;
 	(my $locus = $$align_) =~ s/\.csv//; # Changed from .phy to .csv
	open (my $fh, '<', "$$align_location$$align_") or die "The original alignment file will not open\n", "$!";
	<$fh>; # Skip header line ("Peptide	Amino acid sequence")
	while (my $line = <$fh>){
		chomp $line;
		next if $line =~ /^\s*$/;  # Skip empty lines
		# Try tab first, then split on whitespace
		my ($virus, $data);
		if ($line =~ /\t/) {
			($virus, $data) = split ("\t", $line);
		} else {
			($virus, $data) = split (/\s+/, $line, 2);
		}
		next unless defined $data && length($data) > 0;  # Skip if no sequence
		chomp $virus if defined $virus;
		chomp $data if defined $data;
 		my $gap_positions = gaps ($data);
		(my $dealign = $data) =~ s/-//g;
# Note the variable $virus here is taken from the alignment name
		$alignment{$virus}->{'aligned_locus'} = $locus;
		$alignment{$virus}->{'gaps'} = $gap_positions;
		$alignment{$virus}->{'protein'} = $data;
		$alignment{$virus}->{'dealign_protein'} = $dealign;
# "Tags" (keys and values) hereon are not used in this script
		$alignment{$virus}->{$$cd4_}->{'ANN'} = ();
		$alignment{$virus}->{$$cd4_}->{'SMM'} = ();
		$alignment{$virus}->{$$cd4_}->{'Epitopes'} = ();
		$alignment{$virus}->{$$cd4_}->{'Epitope_loc'} = ();
		$alignment{$virus}->{$$cd4_}->{'Index_epi_location'} = ();
		$alignment{$virus}->{$$cd4_}->{'Size'} = ();
		$alignment{$virus}->{$$cd4_}->{'Consensus'} = (); 
		$alignment{$virus}->{$$cd4_}->{'Error'} = (); 
		$alignment{$virus}->{$$cd4_}->{'Gold_location'} = ();
		$alignment{$virus}->{$$cd4_}->{'Epitope_homologue_penultimate'} = ();
		$alignment{$virus}->{$$cd4_}->{'Epitope_homologue_confirmed'} = ();
		$alignment{$virus}->{$$cd4_}->{'Indel_epitope_reference'}->{'KU365778_Zika_BeH819015'} = ();
		$alignment{$virus}->{$$cd4_}->{'Indel_epitope_reference'}->{'JE_057434_EF623988'} = ();
		$alignment{$virus}->{$$cd4_}->{'amino_acid_identity'}->{'KU365778_Zika_BeH819015'} = (); 
		$alignment{$virus}->{$$cd4_}->{'amino_acid_identity'}->{'JE_057434_EF623988'} = ();
		$alignment{$virus}->{$$cd4_}->{'amino_acid_differences'}->{'KU365778_Zika_BeH819015'} = ();
		$alignment{$virus}->{$$cd4_}->{'amino_acid_differences'}->{'JE_057434_EF623988'} = ();
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
	my ($alignment_0, $locus_0, $align_loc_0, $iedb_out_0, $cd4_0) = @_;
	my @iedb_raw = ();
	my $dir_tmp = 'fa_tmp/';
	unless (-d "$iedb_out_0"){
		system("mkdir $iedb_out_0");
		system("mkdir $iedb_out_0$dir_tmp");
		 }
	foreach my $no ($length_min..$length_max){
		# Method selection for Class II binding methods:
		# - All methods work across the 15-20 range
		# - No length-based conditionals needed
		# macOS compatible methods only (fully compatible):
		# - TEPITOPE: Pure Python, works on macOS (supports many alleles)
		# - Comblib: Pure Python, works on macOS (only supports DRB1*01:01, DRB1*07:01, DRB1*09:01)
		# Other methods (commented out - require Linux):
		# - netmhciipan_el, netmhciipan_ba: Linux-only binaries
		# - nn_align: Requires platform detection fix for ARM64
		# - smm_align: Linux-only binaries
		# - cd4episcore: Requires R and Linux binaries (immunogenicity method)
		
		# Comblib only supports: DRB1*01:01, DRB1*07:01, DRB1*09:01
		# Skip Comblib for unsupported alleles to avoid hanging/failures
		my @comblib_supported = ('DRB1*01:01', 'DRB1*07:01', 'DRB1*09:01');
		my $cd4_normalized = $cd4_0;
		$cd4_normalized =~ s/HLA-//;  # Remove HLA- prefix for comparison
		
		my @methods = ('tepitope');  # Always run TEPITOPE
		# Only add Comblib if allele is supported
		my $comblib_supported = 0;
		foreach my $supported (@comblib_supported) {
			if ($cd4_normalized eq $supported) {
				$comblib_supported = 1;
				last;
			}
		}
		if ($comblib_supported) {
			push @methods, 'comblib';
		}
		
		foreach my $method (@methods) {
			my $tag = "__" . "$cd4_0" . "\.$no" . "\_$method\.csv";
			foreach my $virus (keys %{$alignment_0}){
				(my $output = $virus) =~ s/(.+)/$1$tag/;
				$output =~ s/\*/\+/; # using globs (\*) within filenames causes mayhem, so it is substituted with "+" (and converted back again later)
				my $tmpf = $iedb_out_0 . $dir_tmp . "$virus\.fa";
				open(my $fhout, '>', "$tmpf") or die "Can not open the temporary outfile\.\n" . "$!";
				print $fhout "\>$virus\n", "$alignment_0->{$virus}->{'dealign_protein'}"; # it must be fasta format
				close $fhout;
################
## Updated subprocess call - using JSON with FASTA file path
## This lets IEDB handle the sliding window internally (preserves original logic)
## Key: Use input_sequence_text_file_path with peptide_length_range
################
				# Updated to use Class II IEDB path - tcell_mhcii.py
				my $base_dir = $ENV{'BASE_DIR'} ? $ENV{'BASE_DIR'} : '/Users/michael_gaunt/Desktop/Anastasia2';
				my $iedb_script = "$base_dir/ng_tc2-0.2.2-beta/src/tcell_mhcii.py";
				# Use venv python3 if PYTHON3_PATH is set (from wrapper), otherwise use system python3
				my $python_cmd = $ENV{'PYTHON3_PATH'} ? $ENV{'PYTHON3_PATH'} : 'python3';
				# Create JSON input for binding methods (TEPITOPE and Comblib use file_path)
				my $tmp_json = $tmpf;
				$tmp_json =~ s/\.fa$/\.json/;
				
				open(my $json_fh, '>', "$tmp_json") or die "Can not open JSON file\.\n" . "$!";
				print $json_fh "{\n";
				print $json_fh "  \"input_sequence_text_file_path\": \"$tmpf\",\n";
				print $json_fh "  \"peptide_length_range\": [$no, $no],\n";
				print $json_fh "  \"alleles\": \"$cd4_0\",\n";
				print $json_fh "  \"predictors\": [\n";
				print $json_fh "    {\n";
				print $json_fh "      \"type\": \"binding\",\n";
				print $json_fh "      \"method\": \"$method\"\n";
				print $json_fh "    }\n";
				print $json_fh "  ]\n";
				print $json_fh "}\n";
				close $json_fh;
				# Run IEDB with JSON input - IEDB handles sliding window automatically
				# Use venv python3 if available (set by wrapper)
				my $iedb_cmd = "$python_cmd $iedb_script -j \"$tmp_json\" -o \"$iedb_out_0$output\" -f tsv 2>&1";
				system ($iedb_cmd); 
#				system("rm $tmpf") if -e $tmpf; # Keep for now as it provides a log of activity
#				system("rm $tmp_json") if -e $tmp_json; # Clean up JSON temp file
				push (@iedb_raw, "$iedb_out_0$output");
			}
		}
	}	
	return \@iedb_raw;
}

sub printout {
	my ($in, $locus_00, $iedb_out_00, $cd4_00) = @_;
	my $outfile = "Total_EPAM_" . $locus_00 . $cd4_00 . "\.log";
	my $outlog = $iedb_out_00 . $outfile;
	system ("rm $outlog") if -e $outlog;
	open (my $fhout, '>>', "$outlog") or die "Can not open the temporary outfile\.\n" . "$!";
	print $fhout 'These proteins have been processed by IEDB for' . "$cd4_00" . ' and ' . "$locus_00\:\n";
	foreach my $f (@$in){
		print $fhout $f, "\n"; 
	}
	close $fhout;
}

__END__
