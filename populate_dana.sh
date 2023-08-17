echo "REGRESSION_DATASET_PATH:"
echo $REGRESSION_DATASET_PATH

cd ../dana
nohup npm start &
sleep 4

cd -
python dashboard/initial_populate.py --repository $REGRESSION_DATASET_PATH
