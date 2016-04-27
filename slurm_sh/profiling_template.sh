#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --workdir=/mnt/SCRATCH
#SBATCH --cpus-per-task=XX_THREAD_COUNT_XX
#SBATCH --mem=18000
##deb reqs: python-dev libssl-dev s3cmd
#environment variables
SCRATCH_DIR="/mnt/SCRATCH"
THREAD_COUNT="XX_THREAD_COUNT_XX"

#job variables
BAM_URL="XX_BAM_URL_XX"
CASE_ID="XX_CASE_ID_XX"
TCGA_BARCODE="XX_BARCODE_XX"

#server environment
S3_CFG_PULL_PATH="/home/ubuntu/.s3cfg.cleversafe"
S3_CFG_PUSH_PATH="/home/ubuntu/.s3cfg.ceph"
EXPORT_PROXY_STR="export http_proxy=http://cloud-proxy:3128; export https_proxy=http://cloud-proxy:3128;"
DB_CONNECT_URL="s3://bioinformatics_scratch/mir_tools/db_connections.cfg"
DB_CRED_URL="s3://bioinformatics_scratch/mir_tools/connect_dmiller.ini"
QUAY_PULL_KEY_URL="s3://bioinformatics_scratch/mir_tools/.dockercfg"

#private cwl
GIT_CWL_SERVER="github.com"
GIT_CWL_SERVER_FINGERPRINT="2048 16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48"
GIT_CWL_DEPLOY_KEY_S3_URL="s3://bioinformatics_scratch/mir_tools/mirna_profiling_rsa"
GIT_CWL_REPO="git@github.com:NCI-GDC/mirna-profiler.git"
GIT_CWL_HASH="XX_GIT_CWL_HASH_XX"
PROFILING_WORKFLOW="workflows/mir_profiling_workflow.cwl.yaml"
SAMTOOLS_TOOL="tools/samtools.cwl.yaml"
ADAPTER_REPORT_TOOL="tools/mir_adapter_report.cwl.yaml"
SAM_ANNOTATOR_TOOL="tools/mir_sam_annotator.cwl.yaml"
ALIGNMENT_STATS_TOOL="tools/mir_alignment_stats.cwl.yaml"
TCGA_TOOL="tools/mir_tcga.cwl.yaml"
EXPN_MATRIX_TOOL="tools/mir_expn_matrix/cwl.yaml"
EXPN_MIMAT_TOOL="tools/mir_expn_mimmat/cwl.yaml"
GRAPH_TOOL="tools/mir_graph.cwl.yaml"
QUEUE_STATUS_TOOL="tools/queue_status.cwl.yaml"


#cwl runner
CWLTOOL_REQUIREMENTS_PATH="slurm_sh/requirements.txt"
CWLTOOL_URL="https://github.com/chapmanb/cwltool.git"
CWLTOOL_HASH="221cf2395b2745ae1c3899c691d94edf3152327d"

#input bucket
S3_MIRASEQ_BUCKET="s3://tcga_mirnaseq_alignment_3"
#output buckets
S3_OUT_BUCKET="s3://tcga_mirna_profiling"
S3_LOG_BUCKET="s3://tcga_mirna_profiling_log"

function remove_data()
{
    echo ""
    echo "remove_data()"
    
    local data_dir="$1"
    local case_id="$2"
    
    echo "rm -rf ${data_dir}"
    rm -rf ${data_dir}
    local this_virtenv_dir=${HOME}/.virtualenvs/p2_${case_id}
    echo "rm -rf ${this_virtenv_dir}"
    rm -rf ${this_virtenv_dir}
}

function queue_status_update()
{
    echo ""
    echo "queue_status_update()"

    local data_dir="${1}"
    local cwl_tool="${2}"
    local git_cwl_repo="${3}"
    local git_cwl_hash="${4}"
    local case_id="${5}"
    local bam_url="${6}"
    local status="${7}"
    local table_name="${8}"
    local s3cfg_path="${9}"
    local db_cred_s3url="${10}"
    local s3_out_bucket="${11}"

    echo "status=${status}"
    echo "table_name=${table_name}"
    
    get_git_name "${git_cwl_repo}"
    echo "git_name=${git_name}"
    local cwl_dir=${data_dir}/${git_name}
    local cwl_tool_path=${cwl_dir}/${cwl_tool}


    local this_virtenv_dir=${HOME}/.virtualenvs/p2_${case_id}
    local cwlrunner_path=${this_virtenv_dir}/bin/cwltool
    local gdc_id=$(basename $(dirname ${bam_url}))

    if [ ${db_cred_s3url} == "XX_DB_CRED_S3URL_XX" ]
    then
        local cwl_command="--debug --outdir ${data_dir} ${cwl_tool_path} --case_id ${case_id} --gdc_id ${gdc_id} --repo ${git_cwl_repo} --repo_hash ${git_cwl_hash} --table_name ${table_name} --status ${status}"
    elif [[ "${status}" == "COMPLETE" ]]
    then
        local bam_file=$(basename ${bam_url})
        local s3_url=${s3_out_bucket}/${gdc_id}/${bam_file}
        local cwl_command="--debug --outdir ${data_dir} ${cwl_tool_path} --case_id ${case_id} --db_cred_s3url ${db_cred_s3url} --gdc_id ${gdc_id} --repo ${git_cwl_repo} --repo_hash ${git_cwl_hash} --s3cfg_path ${s3cfg_path} --table_name ${table_name} --status ${status} --s3_url ${s3_url}"
    else
        local cwl_command="--debug --outdir ${data_dir} ${cwl_tool_path} --case_id ${case_id} --db_cred_s3url ${db_cred_s3url} --gdc_id ${gdc_id} --repo ${git_cwl_repo} --repo_hash ${git_cwl_hash} --s3cfg_path ${s3cfg_path} --table_name ${table_name} --status ${status}"
    fi
    echo "${cwlrunner_path} ${cwl_command}"
    ${cwlrunner_path} ${cwl_command}
}


function get_git_name()
{
    echo ""
    echo "get_git_name()"
    
    local repo_str="$1"

    local git_array=(${repo_str})
    local git_url=${git_array[-1]}
    echo "repo_str=${repo_str}"
    echo "git_url=${git_url}"
    IFS=':' read -r -a array <<< "${git_url}"
    local owner_repo=${array[-1]}
    echo "owner_repo=${owner_repo}"
    local git_repo=$(basename ${owner_repo})
    echo "git_repo=${git_repo}"
    git_name="${git_repo%.*}" # need global var for return
    echo "${git_name}"
}

function install_unique_virtenv()
{
    echo ""
    echo "install_unique_virtenv()"
    
    local uuid="$1"
    local export_proxy_str="$2"
    local data_dir="$3"

    local build_dir=${data_dir}/pip_build
    eval ${export_proxy_str}
    echo "deactivate"
    deactivate
    echo "pip install virtualenvwrapper --build ${build_dir} --user --ignore-installed"
    pip install virtualenvwrapper --build ${build_dir} --user --ignore-installed
    source ${HOME}/.local/bin/virtualenvwrapper.sh
    mkvirtualenv --python /usr/bin/python2 p2_${uuid}
    local this_virtenv_dir=${HOME}/.virtualenvs/p2_${uuid}
    source ${this_virtenv_dir}/bin/activate
    pip install --upgrade pip --build ${build_dir}
    if [ $? -ne 0 ]
    then
        echo "FAILED: pip install --upgrade pip --build ${build_dir}"
        remove_data ${data_dir} ${uuid}
        exit 1
    fi
}

function pip_install_requirements()
{
    echo ""
    echo "pip_install_requirements()"

    local git_cwl_repo="$1"
    local requirements_path="$2"
    local export_proxy_str="$3"
    local data_dir="$4"
    local uuid="$5"

    local build_dir=${data_dir}/pip_build
    local this_virtenv_dir=${HOME}/.virtualenvs/p2_${uuid}
    source ${this_virtenv_dir}/bin/activate
    
    get_git_name "${git_cwl_repo}"
    echo ${git_name}
    requirments_dir="${data_dir}/${git_name}/"
    requirements_path="${requirments_dir}/${requirements_path}"
    
    eval ${export_proxy_str}
    pip install -r ${requirements_path} --build ${build_dir}
    if [ $? -ne 0 ]
    then 
        echo "FAILED: pip install -r ${requirements_path} --build ${build_dir}"
        remove_data ${data_dir} ${uuid}
        exit 1       
    fi
}

function setup_deploy_key()
{
    echo ""
    echo "setup_deploy_key()"
    
    local s3_cfg_path="$1"
    local s3_deploy_key_url="$2"
    local data_dir="$3"
    
    local prev_wd=`pwd`
    local key_name=$(basename ${s3_deploy_key_url})
    echo "cd ${data_dir}"
    cd ${data_dir}
    eval `ssh-agent`
    echo "s3cmd -c ${s3_cfg_path} get --force ${s3_deploy_key_url}"
    s3cmd -c ${s3_cfg_path} get --force ${s3_deploy_key_url}
    echo "chmod 400 ${key_name}"
    chmod 400 ${key_name}
    echo "ssh-add ${key_name}"
    ssh-add ${key_name}
    ssh-add -L
    echo "cd ${prev_wd}"
    cd ${prev_wd}
}

function clone_git_repo()
{
    echo ""
    echo "clone_git_repo()"
    
    local git_server="$1"
    local git_server_fingerprint="$2"
    local git_repo="$3"
    local export_proxy_str="$4"
    local data_dir="$5"
    local git_cwl_hash="$6"

    get_git_name "${git_repo}"
    echo "git_name=${git_name}"

    local prev_wd=`pwd`
    echo "eval ${export_proxy_str}"
    eval ${export_proxy_str}
    echo "cd ${data_dir}"
    cd ${data_dir}
    #check if key is in known hosts
    echo 'ssh-keygen -H -F ${git_server} | grep "Host ${git_server} found: line 1 type RSA" -'
    ssh-keygen -H -F ${git_server} | grep "Host ${git_server} found: line 1 type RSA" -
    if [ $? -eq 0 ]
    then
        echo "git_server ${git_server} is known"
        echo "git clone ${git_repo}"
        git clone ${git_repo}
        cd ${git_name}
        echo "git checkout ${git_cwl_hash}"
        git checkout ${git_cwl_hash}
    else # if not known, get key, check it, then add it
        echo "git_server ${git_server} is NOT known"
        echo "ssh-keyscan ${git_server} > ${git_server}_gitkey"
        ssh-keyscan ${git_server} > ${git_server}_gitkey
        echo `ssh-keygen -lf ${git_server}_gitkey` | grep "${git_server_fingerprint} ${git_server} (RSA)"
        if [ $? -eq 0 ]
        then
            echo "cat ${git_server}_gitkey >> ${HOME}/.ssh/known_hosts"
            cat ${git_server}_gitkey >> ${HOME}/.ssh/known_hosts
            echo "git clone ${git_repo}"
            git clone ${git_repo}
            cd ${git_name}
            echo "git checkout ${git_cwl_hash}"
            git checkout ${git_cwl_hash}
        else
            echo "git server fingerprint is not '${git_server_fingerprint} ${git_server} (RSA)', but instead:  `ssh-keygen -lf ${git_server}_gitkey`"
            cd ${prev_wd}
            exit 1
        fi
    fi
    cd ${prev_wd}
}

function get_bam_file()
{
    echo ""
    echo "get_bam_files()"
    
    local s3_cfg_path="$1"
    local bam_url="$2"
    local data_dir="$3"

    echo "s3_cfg_path=${s3_cfg_path}"
    echo "bam_url=${bam_url}"
    echo "data_dir=${data_dir}"
    
    local prev_wd=`pwd`
    echo "cd ${data_dir}"
    cd ${data_dir}
    echo "s3cmd -c ${s3_cfg_path} --force get ${bam_url}"
    s3cmd -c ${s3_cfg_path} --force get ${bam_url}
    echo "cd ${prev_wd}"
    cd ${prev_wd}
}

function run_profiling()
{
    echo ""
    echo "run_profiling()"
    
    local data_dir="$1"
    local bam_url="$2"
    local case_id="$3"
    local profiling_workflow="$4"
    local connect_url="$5"
    local barcode="$6"
    local git_cwl_repo="$7"
    local db_cred_s3url="$8"
    local s3_cfg_path="$9"

    local genome_version="hg38"
    local species_code="hsa"

    local gdc_id=$(basename $(dirname ${bam_url}))
    local bam_name=$(basename ${bam_url})
    local bam_path=${data_dir}/${bam_name}
    local connect_name=$(basename ${connect_url})
    local connect_path=${data_dir}/${connect_name}

    local sam_name=${barcode}".sam"
    get_git_name "${git_cwl_repo}"
    local cwl_dir=${data_dir}/${git_name}
    local workflow_path=${cwl_dir}/${profiling_workflow}
    
    local profiling_dir=${data_dir}/profiling
    local tmp_dir=${data_dir}/tmp/tmp
    local tmpout_dir=${data_dir}/tmp_out/tmp
    local prev_wd=`pwd`
    mkdir -p ${profiling_dir}
    mkdir -p ${tmp_dir}
    mkdir -p ${tmpout_dir}
    cd ${profiling_dir}
    
    # setup cwl command removed  --leave-tmpdir
    local cwl_command="--debug --outdir ${profiling_dir} --tmpdir-prefix ${tmp_dir} --tmp-outdir-prefix ${tmpout_dir} ${workflow_path} --bam_path ${bam_path} --sam_name ${sam_name}  --genome_version ${genome_version} --species_code ${species_code} --connect_path ${connect_path} --uuid ${gdc_id} --barcode ${barcode} --db_cred_s3url ${db_cred_s3url} --s3cfg_path ${s3_cfg_path}"

    # run cwl
    local this_virtenv_dir=${HOME}/.virtualenvs/p2_${case_id}
    local cwlrunner_path=${this_virtenv_dir}/bin/cwltool
    echo "calling:
         ${cwlrunner_path} ${cwl_command}"
    ${cwlrunner_path} ${cwl_command}
    if [ $? -eq 0 ]
    then
        echo "completed profiling"
    else
        echo "failed profiling"
        queue_status_update "${data_dir}" "${QUEUE_STATUS_TOOL}" "${GIT_CWL_REPO}" "${GIT_CWL_HASH}" "${CASE_ID}" "${BAM_URL}" "FAIL" "profiling_caseid_queue" "${S3_CFG_PULL_PATH}" "${DB_CRED_URL}"
        remove_data ${data_dir} ${case_id}
        exit 1
    fi
    cd ${prev_wd}
}

function upload_profiling_results()
{
    echo ""
    echo "upload_profiling_results()"
    
    local case_id="$1"
    local bam_url="$2"
    local s3_out_bucket="$3"
    local s3_log_bucket="$4"
    local s3_cfg_path="$5"
    local data_dir="$6"
    
    local profiling_dir=${data_dir}/profiling
    local prev_wd=`pwd`
    cd ${profiling_dir}
    local gdc_id=$(basename $(dirname ${bam_url}))
    local tar_name=${gdc_id}"_auxiliary.tar"
    local tar_path=${profiling_dir}/${tar_name}
    local mirnas_path=${profiling_dir}/"tcga/mirnas.quantification.txt"
    local isoforms_path=${profiling_dir}/"tcga/isoforms.quantification.txt"
    tar cf ${tar_name} *.jpg alignment_stats.csv *.report expn* features/
    echo "uploading: s3cmd -c ${s3_cfg_path} put ${tar_path} ${mirnas_path} ${isoforms_path} ${S3_OUT_BUCKET}/${gdc_id}/"
    s3cmd -c ${s3_cfg_path} put ${tar_path} ${mirnas_path} ${isoforms_path} ${s3_out_bucket}/${gdc_id}/
    echo "s3cmd -c ${s3_cfg_path} put ${profiling_dir}/*.log ${s3_log_bucket}/"
    s3cmd -c ${s3_cfg_path} put ${profiling_dir}/*.log ${s3_log_bucket}/
}

function clone_pip_git_hash()
{
    echo ""
    echo "clone_pip_cwltool()"

    local uuid="$1"
    local git_url="$2"
    local git_hash="$3"
    local data_dir="$4"
    local export_proxy_str="$5"

    local build_dir=${data_dir}/pip_build
    echo uuid=${uuid}
    echo git_url=${git_url}
    echo git_hash=${git_hash}
    echo data_dir=${data_dir}
    echo export_proxy_str=${export_proxy_str}
    
    eval ${export_proxy_str}
    
    this_virtenv_dir=${HOME}/.virtualenvs/p2_${uuid}
    source ${this_virtenv_dir}/bin/activate

    prev_wd=`pwd`
    echo "cd ${data_dir}"
    cd ${data_dir}

    git clone ${git_url}
    get_git_name "${git_url}"
    echo "${git_name}"
    echo "cd ${data_dir}/${git_name}"
    cd ${data_dir}/${git_name}
    echo "git reset --hard ${git_hash}"
    git reset --hard ${git_hash}

    echo "pip install -e ."
    pip install --build ${build_dir} -e .
    echo "cd ${prev_wd}"
}

function get_dockercfg()
{
    echo ""
    echo "get_dockercfg()"
    
    local s3_cfg_path="$1"
    local quay_pull_key_url="$2"

    local prev_wd=`pwd`
    cd ${HOME}
    echo 's3cmd -c ${s3_cfg_path} --force get "${quay_pull_key_url}"'
    s3cmd -c ${s3_cfg_path} --force get "${quay_pull_key_url}"
    cd "${prev_wd}"
}

function get_connect_db()
{
    echo ""
    echo "get_connect_db()"
    
    local s3_cfg_path="$1"
    local db_connect_url="$2"
    local data_dir="$3"

    echo "s3_cfg_path=${s3_cfg_path}"
    echo "db_connect_url=${db_connect_url}"
    echo "data_dir=${data_dir}"

    local prev_wd=`pwd`
    echo "cd ${data_dir}"
    cd ${data_dir}
    echo "s3cmd -c ${s3_cfg_path} --force get ${db_connect_url}"
    s3cmd -c ${s3_cfg_path} --force get ${db_connect_url}
    echo "cd ${prev_wd}"
    cd "${prev_wd}"
}


function main()
{

    local data_dir="${SCRATCH_DIR}/data_"${CASE_ID}
    remove_data ${data_dir} ${CASE_ID} ## removes all data from previous run of script
    mkdir -p ${data_dir}
    
   
    setup_deploy_key "${S3_CFG_PULL_PATH}" "${GIT_CWL_DEPLOY_KEY_S3_URL}" "${data_dir}"
    clone_git_repo "${GIT_CWL_SERVER}" "${GIT_CWL_SERVER_FINGERPRINT}" "${GIT_CWL_REPO}" "${EXPORT_PROXY_STR}" "${data_dir}" "${GIT_CWL_HASH}"
    install_unique_virtenv "${CASE_ID}" "${EXPORT_PROXY_STR}" "${data_dir}"
    pip_install_requirements "${GIT_CWL_REPO}" "${CWLTOOL_REQUIREMENTS_PATH}" "${EXPORT_PROXY_STR}" "${data_dir}" "${CASE_ID}"
    clone_pip_git_hash "${CASE_ID}" "${CWLTOOL_URL}" "${CWLTOOL_HASH}" "${data_dir}" "${EXPORT_PROXY_STR}"
    get_dockercfg "${S3_CFG_PULL_PATH}" "${QUAY_PULL_KEY_URL}"
    get_connect_db "${S3_CFG_PULL_PATH}" "${DB_CONNECT_URL}" "${data_dir}"
    queue_status_update "${data_dir}" "${QUEUE_STATUS_TOOL}" "${GIT_CWL_REPO}" "${GIT_CWL_HASH}" "${CASE_ID}" "${BAM_URL}" "RUNNING" "profiling_caseid_queue" "${S3_CFG_PULL_PATH}" "${DB_CRED_URL}" "${S3_OUT_BUCKET}"
    get_bam_file "${S3_CFG_PULL_PATH}" "${BAM_URL}" "${data_dir}"
    run_profiling "${data_dir}" "${BAM_URL}" "${CASE_ID}" "${PROFILING_WORKFLOW}" "${DB_CONNECT_URL}" "${TCGA_BARCODE}" "${GIT_CWL_REPO}" "${DB_CRED_URL}" "${S3_CFG_PULL_PATH}"
    upload_profiling_results "${CASE_ID}" "${BAM_URL}" "${S3_OUT_BUCKET}" "${S3_LOG_BUCKET}" "${S3_CFG_PUSH_PATH}" "${data_dir}"
    queue_status_update "${data_dir}" "${QUEUE_STATUS_TOOL}" "${GIT_CWL_REPO}" "${GIT_CWL_HASH}" "${CASE_ID}" "${BAM_URL}" "COMPLETE" "profiling_caseid_queue" "${S3_CFG_PULL_PATH}" "${DB_CRED_URL}" "${S3_OUT_BUCKET}"
    remove_data "${data_dir}" "${CASE_ID}"
}

main "$@"
