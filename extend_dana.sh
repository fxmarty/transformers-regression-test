echo "REGRESSION_DATASET_PATH:"
echo $REGRESSION_DATASET_PATH

cd ../dana
nohup npm start &
sleep 4

cd -
python dashboard/extend.py --repository $REGRESSION_DATASET_PATH --commit $COMMIT_SHA
