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
    if [ "cpu" == *$YAML_FILE_NAME* ]; then
        export CUDA_VISIBLE_DEVICES=""
    elif [ "1gpu" == *$YAML_FILE_NAME* ]; then
        export CUDA_VISIBLE_DEVICES="0"
    elif [ "2gpu" == *$YAML_FILE_NAME* ]; then
        export CUDA_VISIBLE_DEVICES="0,1"
    elif [ "4gpu" == *$YAML_FILE_NAME* ]; then
        export CUDA_VISIBLE_DEVICES="0,1,2,3"
    else
        echo "ERROR: could not set CUDA_VISIBLE_DEVICES"
        exit 1
    fi
    echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
    optimum-benchmark --config-dir configs --config-name $YAML_FILE_NAME --multirun
done <yaml_list.txt
