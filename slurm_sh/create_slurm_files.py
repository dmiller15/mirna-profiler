#!/usr/bin/env python

#psql command
#\o mirna_tcga_case.txt
#select case_id,location,barcode from mirnaseq where study='TCGA' order by case_id;
#\q

import argparse
import logging
import os
import sys

def write_case_file(template_file, caseid, bamurl, barcode, thread_count, git_hash):
    template_dir = os.path.dirname(template_file)
    out_dir = os.path.join(template_dir, 'case_slurm_sh')
    os.makedirs(out_dir, exist_ok=True)
    out_file = 'profiling_'+barcode+'.sh'
    out_path = os.path.join(out_dir, out_file)
    print('out_path=%s' % out_path)
    out_path_open = open(out_path, 'w')
    with open(template_file, 'r') as template_file_open:
        for line in template_file_open:
            if 'XX_BAM_URL_XX' in line:
                newline = line.replace('XX_BAM_URL_XX', bamurl)
                out_path_open.write(newline)
            elif 'XX_CASE_ID_XX' in line:
                newline = line.replace('XX_CASE_ID_XX', caseid)
                out_path_open.write(newline)
            elif 'XX_TCGA_BARCODE_XX' in line:
                newline = line.replace('XX_TCGA_BARCODE_XX', barcode)
                out_path_open.write(newline)
            elif 'XX_THREAD_COUNT_XX' in line:
                newline = line.replace('XX_THREAD_COUNT_XX', thread_count)
                out_path_open.write(newline)
            elif 'XX_GIT_CWL_HASH_XX' in line:
                newline = line.replace('XX_GIT_CWL_HASH_XX', git_hash)
                out_path_open.write(newline)
            else:
                out_path_open.write(line)
    out_path_open.close()
    return

def parse_sql_file(sql_file):
    sql_values=[]
    with open(sql_file, 'r') as sql_file_open:
        for line in sql_file_open:
            if line.startswith('-') or line.startswith('    ') or line.startswith('(') or line.startswith('\n'):
                continue
            else:
                line_split = line.split('|')
                caseid = line_split[0].strip()
                bamurl = line_split[1].strip()
                bamurl = bamurl.replace('cleversafe.service.consul/', '')
                barcode = line_split[2].strip()
                sql_values.append((caseid, bamurl, barcode))
    return sql_values

def main():
    parser = argparse.ArgumentParser('make slurm')
    # Logging flags.
    parser.add_argument('-d', '--debug',
        action = 'store_const',
        const = logging.DEBUG,
        dest = 'level',
        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    parser.add_argument('--sql_file',
                        required = True,
                        help = 'pulled from harmonized_files'
    )
    parser.add_argument('--template_file',
                        required = True,
                        help = 'slurm template file',
    )
    parser.add_argument('--thread_count',
                        required = True,
                        help = 'slurm template file',
    )
    parser.add_argument('--git_hash',
                        required = True,
                        help = 'slurm template file',
    )

    args = parser.parse_args()
    sql_file = args.sql_file
    template_file = args.template_file
    thread_count = args.thread_count
    git_hash = args.git_hash

    parsed_sql = parse_sql_file(sql_file)
    
    for caseid, bamurl, barcode in parsed_sql:
        print('\nmiRNA_entry=%s\t%s\t%s' % (caseid bamurl, barcode))
        write_case_file(template_file, caseid, bamurl, barcode, thread_count, git_hash)
        
if __name__=='__main__':
    main()
