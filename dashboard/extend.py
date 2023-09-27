from dana import add_project, add_build, add_series, add_sample, get_build_id, get_description
import argparse
import os
from glob import glob
import csv
from tqdm import tqdm

parser = argparse.ArgumentParser()

parser.add_argument(
    "--token",
    type=str,
    help="Hugging Face write token for the repository to push to.",
)
parser.add_argument(
    "--commit",
    type=str,
    help="Commit SHA for the given regression benchmark to aggregate and push to the Hub.",
)
parser.add_argument(
    "--repository",
    type=str,
    help="Hugging Face Hub dataset repository id, or local directory to the data.",
)

args = parser.parse_args()

def split_path(path):
    return os.path.normpath(path).split(os.path.sep)


if not os.path.isdir(args.repository):
    raise NotImplementedError("Only local dataset dir is implemented.")

# NOTE: We assume two projects "Training" and "Inference" are already available.
# We do not assume all the series already exist, they are created if not.
# We assume the sweeps are constant over time for an existing serie.


# Step 1: Add commit information to all projects.
add_build("Training", args.commit, override=True)
add_build("Inference", args.commit, override=True)

# Gather relevant data from the series for this commit SHA.
available_series = glob(os.path.join(args.repository, "raw_results") + "/*/*/", recursive=False)

relevant_series_paths = []
for serie_path in available_series:
    if args.commit in serie_path:
        relevant_series_paths.append(serie_path)

unique_series = {}
# serie_path is a multirun directory.
for serie_path in relevant_series_paths:
    raw_serie_name = split_path(serie_path)[-1]

    sweeps_paths = glob(serie_path + "/*/", recursive=False)
    n_sweeps = len(sweeps_paths)

    if "training" in raw_serie_name:
        project_id = "Training"
        result_name = "training_results.csv"
        serie_name = raw_serie_name.replace("_training_", "_")
        serie_name = serie_name.replace("_training", "")
    elif "inference" in raw_serie_name:
        project_id = "Inference"
        result_name = "inference_results.csv"
        serie_name = raw_serie_name.replace("_inference_", "_")
        serie_name = serie_name.replace("_inference", "")
    else:
        raise ValueError(f"The serie name {raw_serie_name} should contain either `training` or `inference`.")


    for i in range(n_sweeps):
        with open(os.path.join(sweeps_paths[i], result_name)) as fp:
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            data_read = [row for row in reader]
            metrics_list = data_read[0]
            try:
                metrics_list.remove("")  # optimum-benchmark adds an empty column, not sure why
            except ValueError:
                pass

            values_list = data_read[1]
            if values_list[0] == "0":
                del values_list[0]

            metrics_data = {metric_name: float(metric_value) for (metric_name, metric_value) in zip(metrics_list, values_list)}


        for metric_name, metric_data in metrics_data.items():
            if metric_name not in ["warmup.runtime(s)", "warmup.throughput(samples/s)", "overall_training.runtime(s)", "overall_training.throughput(samples/s)"]:
                full_serie_name = serie_name + f"_{i}_{metric_name}"
                full_serie_name = full_serie_name.replace("(", "_")
                full_serie_name = full_serie_name.replace(")", "_")
                full_serie_name = full_serie_name.replace("/", "_")
                full_serie_name = full_serie_name.replace(".", "_")

                unique_series[full_serie_name] = {"project_id": project_id, "result_name": result_name, "metric_data": metric_data, "serie_path": os.path.join(serie_path, str(i)), "multirun_dir": serie_path}

# Step 2: Add missing series, and data to the series.
for serie_name, serie_data in tqdm(unique_series.items(), desc="Adding series and data"):
    analyse = {
        "benchmark": {
            "range": "10%",
            "required": 5,
            "trend": "smaller",
        }
    }

    description = get_description(multirun_dir=serie_data["multirun_dir"], sweep_dir=serie_data["serie_path"])
    result = add_series(project_id=serie_data["project_id"], serie_id=serie_name, description=description, analyse=analyse, strict=False)

    if "serieId already exist" in result.text:
        print(f"INFO: the series {serie_name} already exists. Simply adding data.")
    else:
        if result.status_code == 200:
            print(f"INFO: Creating the series {serie_name} and adding data.")
        else:
            raise ValueError(f"add_series failed with status code {result.status_code} and result: {result.text}")


    sample = {
        "buildId": get_build_id(args.commit),
        "value": serie_data["metric_data"],
    }
    result = add_sample(project_id=serie_data["project_id"], serie_id=serie_name, sample=sample, strict=False)

    if "Sample already exist" in result.text:
        print(f"INFO: the sample for SHA {args.commit} already exists for the series {serie_name}. Skipping.")
    else:
        if result.status_code == 200:
            print(f"INFO: Adding data for the series {serie_name}.")
        else:
            raise ValueError(f"add_sample failed with status code {result.status_code} and result: {result.text}")



