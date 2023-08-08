cd configs && ls -1 *.yaml > ../yaml_list.txt
cd ..
sed -i '/base_config.yaml/d' yaml_list.txt
sed -i 's/.yaml//' yaml_list.txt
echo "COMMIT_SHA: ${COMMIT_SHA}"
echo "COMMIT_DATE_GMT: ${COMMIT_DATE_GMT}"

echo "All yaml to use:"
cat yaml_list.txt

while read YAML_FILE_NAME; do
    echo "Running optimum-benchmark for: ${YAML_FILE_NAME}.yml"
    optimum-benchmark --config-dir configs --config-name $YAML_FILE_NAME --multirun
done <yaml_list.txt
