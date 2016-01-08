#!/usr/bin/env perl
use strict;
use Getopt::Std;
use Pod::Usage;
use File::Find;
use File::Basename;
use File::Copy;
use Cwd;

use vars qw($opt_s $opt_f $opt_o $opt_a $opt_h $opt_t);
getopts("s:f:o:a:h:t:");

my $usage = "$0 -s sam_path -f filtered_taglen_path -o softclip_taglen_path -a adapter_taglen_path -h chastity_taglen_path -t alignment_stats_path \n";
die "$usage" unless $opt_s && $opt_f && $opt_o && $opt_a && $opt_h && $opt_t;

my $r = get_config();

my $filtered_path = $opt_f;
my $softclip_path = $opt_o;
my $adapter_path = $opt_a;
my $chastity_path = $opt_h;
my $stats_path = $opt_t;

my $sam_path = $opt_s;

my $dir = dirname(__FILE__); #R scripts are in the same directory as this script

my $filename = basename($sam_path);
$filename =~ s/\.[bs]am$//;
my ($lib, $index) = split('_', $filename);
$index = '' unless defined $index;

my $outdir = getcwd;

system "$r $dir/taglengths.R $outdir $filename $filtered_path tags";
system "$r $dir/taglengths.R $outdir $filename $softclip_path softclip";
system "$r $dir/taglengths.R $outdir $filename $chastity_path chastity";
system "$r $dir/adapter.R $outdir $filename $adapter_path" if -e $adapter_path;

system "$r $dir/saturation.R $filename\_saturation.jpg ".uc($filename)." $stats_path";

sub get_config {
	my $dir = dirname(__FILE__);
	my $config_file = "$dir/../../config/pipeline_params.cfg";
	
	open CONFIG, $config_file or die "Could not find config file in default location ($config_file)";
	my @config = <CONFIG>;
	close CONFIG;
	chomp @config;
	
	my ($r) = [grep(/^\s*Rscript/, @config)]->[0] =~ /^\s*Rscript\s*=\s*(.+)/ or die "No entry found for Rscript binary in config file.";
	return $r;
}

perl /home/ubuntu/bin/profiler/v0.2.7/code/library_stats/graph_libs.pl 
-s /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/TCGA-56-7823-01B-11H-2246-13_mirna.sam 
-f /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/TCGA-56-7823-01B-11H-2246-13_mirna_features/filtered_taglengths.csv 
-o /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/TCGA-56-7823-01B-11H-2246-13_mirna_features/softclip_taglengths.csv 
-a /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/TCGA-56-7823-01B-11H-2246-13_mirna_adapter.report 
-h /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/TCGA-56-7823-01B-11H-2246-13_mirna_features/chastity_taglengths.csv 
-t /home/ubuntu/SCRATCH/Mirna/172e576e-ec9c-47d1-a431-6e4ed3be28a5/alignment_stats.csv 
