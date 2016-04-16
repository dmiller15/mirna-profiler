#!/usr/bin/env perl
use strict; 
use Getopt::Std; 
use vars qw ($opt_m $opt_o $opt_h $opt_s $opt_r);
getopts('m:o:h:s:r:');
use DBI;
use Cwd;
use File::Find;
use File::Basename;

#Author: Erin Pleasance, epleasance@bcgsc.ca
#Modified by Andy Chu, achu@bcgsc.ca
#Modified by Daniel Miller, dmiller15@uchiago.edu

my $help_text = "
############## $0 ########################

Using a list of genes and a set of expression files, creates an expression matrix.
Uses mirna_species.txt files created by alignment_stats.pl.

3 versions of the expression matrix are created.
expn_matrix.txt: matrix with raw read counts
expn_matrix_norm.txt: matrix with normalized counts (counts per million miRNA aligned tags)
expn_matrix_norm_log.txt: as above, but values are taken to log2

Usage: $0 -m mirbase_db -o species_code -s sam_path -r mirna_path

########################################################
";

if ($opt_h || !($opt_m && $opt_o && $opt_s && $opt_r)) { print $help_text; exit 1; }

#Data structure
my %genes; #hash gene->sample->value
my @genes; #full list of gene names
my %samples; #hash of samples->total tags
my @sample_names; #sample names as ordered in @mirnafiles

my $norm_factor = 1000000; #Normalize to this number of tags

my $mirna_path = $opt_r;
my $sam_path = $opt_s;
my $sample = basename($sam_path);
$sample =~ s/\.sam//;

#Read in gene list
@genes = get_mirna_genes($opt_m, $opt_o);

push (@sample_names, $sample);

my $sample_total = 0; #Total tag count for sample based on expr file
open(FH, $mirna_path) || die "Cannot open expression file $mirna_path: $!";
while(<FH>) {
    chomp;
    my ($mirna, $value) = split(' ');
    $genes{$mirna}{$sample} = $value;
    $sample_total += $value;
}
close(FH);
$samples{$sample} = $sample_total;

@sample_names = sort @sample_names;

#Header
my $header = "Gene";
$header .= "\t$sample";
$header .= "\n";

#Data
open RAW, ">expn_matrix.txt" or die "Can't write out expression matrix expn_matrix.txt: $!\n";
open NORM, ">expn_matrix_norm.txt" or die "Can't write out expression matrix expn_matrix_norm.txt: $!\n";
open LOG, ">expn_matrix_norm_log.txt" or die "Can't write out expression matrix expn_matrix_norm_log.txt: $!\n";
print RAW $header;
print NORM $header;
print LOG $header;

foreach my $gene (@genes) {
    print RAW "$gene";
    print NORM "$gene";
    print LOG "$gene";
    
    foreach my $sample (@sample_names) {
	my $count = $genes{$gene}{$sample} || 0;
	warn "No reads mapped to miRNAs found in sample $sample. Perhaps the mirna_species.txt file is empty?\n" if $samples{$sample} == 0;
	my $norm_count;
	my $log_count;
	if ($samples{$sample} == 0) {
	    $norm_count = 0;
	    $log_count = 0;
	}
	else {
	    $norm_count = sprintf("%.6f", $count*$norm_factor/$samples{$sample});
	    $log_count = sprintf("%.6f", $norm_count == 0 ? 0 : log($norm_count) / log(2));
	}
	
	print RAW "\t$count";
	print NORM "\t$norm_count";
	print LOG "\t$log_count";
    }
    print RAW "\n";
    print NORM "\n";
    print LOG "\n";
}

close RAW;
close NORM;
close LOG;
	
sub get_mirna_genes {
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
    my $dir = getcwd; 
    my $db_connections = "$dir/db_connections.cfg";
    open DB, $db_connections or die "Could not find database connections file $db_connections";
    my @connections = <DB>;
    close DB;
    chomp @connections;
    return split(/\s+/, [grep(/^$dbname/, @connections)]->[0]) or die "Database $dbname not found in $db_connections";
}

