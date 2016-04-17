#!/usr/bin/env perl
use strict;
use Getopt::Std;
use Pod::Usage;
use File::Find;
use File::Basename;
use File::Copy;
use lib dirname(__FILE__);
use Annotate;

use vars qw($opt_m $opt_o $opt_u $opt_s);
getopts("m:o:u:s:");

#takes same file and annotates it
#if annotations already exists, they're overwritten

# No longer takes a project directory; now takes absolute path for sam
my $usage = "$0 -m mirbase -u ucsc_database -o species_code -s sam_path\n";
die "$usage" unless $opt_m && $opt_o && $opt_u && $opt_s;

my $sam_path = $opt_s;
# No longer seaerching for sam files

# Since we are writing to job/output we only need a name for the output
my $input_sam = basename($sam_path);
my $samname = "$input_sam.annot";

# build coordinate and index hashes out of reference data for overlapcoordinates
build_reference_hashes($opt_m, $opt_u, $opt_o, $sam_path);

# We only have 1 sam file now so no more for loop
print STDERR "Starting overlaps for $sam_path...";
annotate_file($sam_path);
print STDERR "Done\n";
my $ori_lines = `wc -l $sam_path | cut -d ' ' -f 1`;
my $annot_lines = `wc -l $samname | cut -d ' ' -f 1`;
# Annotated sam no longer replaces the original as it is in a readonly directory
if ($ori_lines ne $annot_lines) {
    print STDERR "Warning: annotated file does not match original file, check $samname\n";
}

sub annotate_file {
    my $file = shift;
    open IN, "<$file" or die "Can't open sam file: $file\n";
    # Write of annotated sam no longer happens in same dir as sam; just passing the name so it will write it cwd
    open OUT, ">$samname" or die "Can't write to annotation file: $samname\n";
    my $annotated_flag = 0; #file has not been annotated before
    while (my $line = <IN>) {
	chomp $line;
	if ($line =~ /^@/) {
	    #dump line straight to output file if it's just a comment
	    print OUT "$line\n";
	    next;
	}
	my ($id, $bitflag, $chr, $start, $mapq, $cigar, $mate, $matepos, $isize, $seq, $qual, $tags) = split(/\t/, $line, 12);
	if ($chr eq '*') {
	    #dump line straight to output without annotation if read didn't align
	    print OUT "$line\n";
	    next;
	}
	my $strand = '-';
	$strand = '+' if (($bitflag & 0x0010) == 0);
	
	my @alignments;
	push(@alignments, [$chr, $start, $strand, $cigar]);
	if ($tags =~ /XA:Z:(\S+)/) {
	    #check the XA tag to see if read has multiple alignments
	    my @xa = split(';', $1);
	    foreach my $xa (@xa) {
		my ($xchr, $xstrand_start, $xcigar, $xnm) = split(',', $xa);
		my $xstrand = substr($xstrand_start, 0, 1);
		my $xstart = substr($xstrand_start, 1);
		push(@alignments, [$xchr, $xstart, $xstrand, $xcigar]);
	    }
	}
	my @coords = parse_cigar(@alignments);
	
	$annotated_flag = 1 if $annotated_flag == 0 && $tags =~ /XC:Z:/; #only have to run the regex engine once to see if there are previous annotations that need to be stripped off
	$tags =~ s/\tXC:Z:[^\t]+\tXI:Z:[^\t]+\tXD:Z:[^\t]+//g if $annotated_flag;
	
	my ($xc, $xi, $xd);
	foreach my $coord (@coords) {
	    my ($sub_xc, $sub_xi, $sub_xd) = annotate_coord($coord->[0], $coord->[1], $coord->[2], $coord->[3]); #chr, start, end, strand
	    $xc .= $sub_xc.";";
	    $xi .= $sub_xi.";";
	    $xd .= $sub_xd.";";
	}
	$tags .= "\tXC:Z:$xc\tXI:Z:$xi\tXD:Z:$xd";
	print OUT join("\t", $id, $bitflag, $chr, $start, $mapq, $cigar, $mate, $matepos, $isize, $seq, $qual, $tags)."\n";
    }
    close IN or warn "Could not close open file $file\n";
    close OUT or warn "Could not close annotation file $samname\n";
}

sub parse_cigar {
    my @alignments = @_; #chr, start, strand, cigar
    my @coords;
    
    foreach my $aln (@alignments) {		
	my $start = $aln->[1];
	my $cigar = $aln->[3];
	#end coordinate is start + number of bases with [MDNP] in cigar string
	my @cigar_ops = split(/([MIDNSHP])/, $cigar); #wrapping the regex in () keeps the delimiter as an array element
	my $end = $start - 1; #after adding the mapped bases the number will be the position immediately after the end, subtract 1
	while (scalar @cigar_ops) {
	    my $numbases = shift @cigar_ops;
	    my $op = shift @cigar_ops;
	    $end += $numbases if $op =~ /[MDNP]/;
	}
	push(@coords, [$aln->[0], $start, $end, $aln->[2]]); #chr, start, end, strand
    }
    
    return @coords;
}
