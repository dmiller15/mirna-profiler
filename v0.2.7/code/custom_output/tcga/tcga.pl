#!/usr/bin/env perl
use strict;
use Getopt::Std;
use Pod::Usage;
use File::Find;
use File::Basename;
use DBI;

use vars qw($opt_m $opt_o $opt_g $opt_s $opt_r $opt_c $opt_i);
getopts("m:o:g:s:r:c:i:");

#finds .sam or .bam files under project directory and uses files created by library_stats/alignment_stats.pl to generate data files in the format required for TCGA

my $usage = "$0 -m mirbase_db -o species_code -g genome_version -s sam_path -r mirna_species_path -c crossmapped_path -i isoforms_path\n";
die "$usage" unless $opt_m && $opt_o && $opt_g && $opt_s && $opt_r && $opt_c && $opt_i;

my $sam_path = $opt_s;
my $mirna_path = $opt_r;
my $cross_path = $opt_c;
my $isoform_path = $opt_i;

#Read in gene list
my @genes = read_mirbase($opt_m, $opt_o);
my $NORM_FACTOR = 1000000; #normalize to this many miRNA reads in library

# Only dealing with one SAM now; no more for loop
my $total_mirna = 0; #number of miRNA reads in library, sum of reads from mirna_file and cross_file
my %mirnas; #hash storing output for quantitation by miRNA
my %isoforms; #hash storing output for quantitation by isoform
# my $dir = dirname($samplefile);
my $samname = basename($sam_path);
$samname =~ s/\..am$//;

#only print 1 warning if the whole set of files is missing
warn "$mirna_path not found, please run library_stats/alignment_stats.pl to generate the file.\n" unless -e $mirna_path;
warn "$cross_path not found, please run library_stats/alignment_stats.pl to generate the file.\n" if -e $mirna_path && ! -e $cross_path ;
warn "$isoform_path not found, please run library_stats/alignment_stats.pl to generate the file.\n" if -e $mirna_path && -e $cross_path && ! -e $isoform_path;
die "Missing inputs" unless -e $mirna_path && -e $cross_path && -e $isoform_path;

open MIR, "<$mirna_path" or die "Could not open $mirna_path for reading: $!";
while (<MIR>) {
    my ($mirna_annot, $count, $pct) = split ' ';
    my ($mirna, $annot) = split(',', $mirna_annot, 2);
    $mirnas{$mirna}{count} += $count;
    $mirnas{$mirna}{cross} = 'N';
    $total_mirna += $count;
}
close MIR;
open CROSS, "<$cross_path" or die "Could not open $cross_path for reading: $!";
while (<CROSS>) {
    my ($mirna_string, $count, $pct) = split ' ';
    my @cross_mirnas = split(';', $mirna_string);
    foreach my $mirna_annot (@cross_mirnas) {
	my ($mirna, $annot) = split(',', $mirna_annot);
	$mirnas{$mirna}{count} += $count;
	$mirnas{$mirna}{cross} = 'Y';
	$total_mirna += $count; #since miRNAs are being doubled counted in final file, normalize by the double counted sum
    }
}
close CROSS;
open ISO, "<$isoform_path" or die "Could not open $isoform_path for reading: $!";
while (<ISO>) {
    my ($mirna, $chr, $start, $end, $strand, $seq, $count, $cross, $annot) = split ' ';
    my $coord = "$chr:$start-$end:$strand";
    $isoforms{$mirna}{$coord}{count} += $count;
    $isoforms{$mirna}{$coord}{cross} = $cross ? 'Y' : 'N';
    $isoforms{$mirna}{$coord}{annot} = $annot;
}
close ISO;

unless (-d "tcga") {
    mkdir "tcga" or die "Could not make tcga subfolder tcga: $!";
}
open ISO, ">tcga/isoforms.quantification.txt";
open MIR, ">tcga/mirnas.quantification.txt";

#print headers
print ISO "miRNA_ID\tisoform_coords\tread_count\treads_per_million_miRNA_mapped\tcross-mapped\tmiRNA_region\n";
print MIR "miRNA_ID\tread_count\treads_per_million_miRNA_mapped\tcross-mapped\n";

#write out an entry for all miRNAs in miRBase for MIR
foreach my $mirna (@genes) {
    my $mirna_count = $mirnas{$mirna}{count} || 0;
    my $mirna_cross = $mirnas{$mirna}{cross} || "N";
    my $mirna_norm = sprintf("%.6f", $mirna_count * $NORM_FACTOR / $total_mirna);
    print MIR "$mirna\t$mirna_count\t$mirna_norm\t$mirna_cross\n";
}
#write out an entry for only expressed isoforms
foreach my $mirna (@genes) {
    next unless exists $mirnas{$mirna};
    
    foreach my $coord (sort sort_coord_str keys %{$isoforms{$mirna}}) {
	my $hashref = $isoforms{$mirna}{$coord};
	my $iso_norm = sprintf("%.6f", $hashref->{count} * $NORM_FACTOR / $total_mirna);
	print ISO "$mirna\t$opt_g:$coord\t$hashref->{count}\t$iso_norm\t$hashref->{cross}\t$hashref->{annot}\n";
    }
}
	
close ISO;
close MIR;

sub sort_coord_str {
    my ($a_chr, $a_start, $a_end, $a_strand) = $a =~ /(.*):(.*)-(.*):(.*)/;
    my ($b_chr, $b_start, $b_end, $b_strand) = $b =~ /(.*):(.*)-(.*):(.*)/;
    
    if ($a_chr ne $b_chr) {
	return $a_chr <=> $b_chr;
    }
    elsif ($a_start != $b_start) {
	return $a_start <=> $b_start;
    }
    else {
	return $a_end <=> $b_end;
    }
}

sub read_mirbase {
    #returns an array of miRNA gene names
    my $db = shift;
    my $species = shift;
    my ($dbname, $dbhost, $dbuser, $dbpass) = get_db($db);
    my $dbh_mirbase = DBI->connect("DBI:Pg:database=$dbname;host=$dbhost", $dbuser, $dbpass, {AutoCommit => 0, PrintError => 1}) || die "Could not connect to database: $DBI::errstr";
    
    #get mirbase species code from organism code
    my $species_code = $dbh_mirbase->selectrow_array("SELECT auto_id FROM mirna_species WHERE organism = '$species'");
    die "$species_code organism code not found in database" unless defined $species_code;
    
    my (@mirnas, $mirna);
    #only use miRNAs where there is coordinate information and mature strand information
    my $sth = $dbh_mirbase->prepare("SELECT DISTINCT m.mirna_id FROM mirna m JOIN mirna_chromosome_build co ON m.auto_mirna = co.auto_mirna JOIN mirna_pre_mature p ON m.auto_mirna = p.auto_mirna JOIN mirna_mature ma ON p.auto_mature = ma.auto_mature WHERE auto_species = '$species_code' ORDER BY mirna_id");
    $sth->execute();
    $sth->bind_columns(\$mirna);
    while ($sth->fetchrow_arrayref()) {
	push(@mirnas, $mirna);
    }
    $sth->finish;
    $dbh_mirbase->disconnect;
    return @mirnas;
}

sub get_db {
    my $dbname = shift;
    my $dir = dirname(__FILE__);
    my $db_connections = "$dir/../../../config/db_connections.cfg";
    open DB, $db_connections or die "Could not find database connections file $db_connections";
    my @connections = <DB>;
    close DB;
    chomp @connections;
    return split(/\s+/, [grep(/^$dbname/, @connections)]->[0]) or die "Database $dbname not found in $db_connections";
}
