cd configs && ls -1 *.yaml > ../yaml_list.txt
cd ..
sed -i '/base_config.yaml/d' yaml_list.txt
sed -i 's/.yaml//' yaml_list.txt
echo "COMMIT_SHA: ${COMMIT_SHA}"
echo "COMMIT_DATE_GMT: ${COMMIT_DATE_GMT}"

echo "All yaml to use:"
cat yaml_list.txt

echo "nvidia-smi:"
nvidia-smi

while read YAML_FILE_NAME; do
    echo "Running optimum-benchmark for: ${YAML_FILE_NAME}.yml"
    if [[ $YAML_FILE_NAME == *"cpu"* ]]; then
        export CUDA_VISIBLE_DEVICES=""
    elif [[ $YAML_FILE_NAME == *"1gpu"* ]]; then
        export CUDA_VISIBLE_DEVICES="0"
    elif [[ $YAML_FILE_NAME == *"2gpu"* ]]; then
        export CUDA_VISIBLE_DEVICES="0,1"
    elif [[ $YAML_FILE_NAME == *"4gpu"* ]]; then
        export CUDA_VISIBLE_DEVICES="0,1,2,3"
    else
        echo "ERROR: could not set CUDA_VISIBLE_DEVICES"
        exit 1
    fi
    echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
    optimum-benchmark --config-dir configs --config-name $YAML_FILE_NAME --multirun

    # $? is the exit status of the most recently-executed command
    if [ $ret -ne 0 ]; then
        echo "Error during the execution of optimum-benchmark. Exiting with error."
        exit 1
    fi
done <yaml_list.txt
