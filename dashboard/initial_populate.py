import argparse
import huggingface_hub
import os
from glob import glob
import csv
from tqdm import tqdm

from dana import add_project, add_build, add_series, add_sample, get_build_id

def split_path(path):
    return os.path.normpath(path).split(os.path.sep)

METRIC_TO_TREND = {
    "latency": "smaller",
    "throughput": "higher",
}

parser = argparse.ArgumentParser()

parser.add_argument(
    "--repository",
    type=str,
    help="Hugging Face Hub dataset repository id, or local directory to the data.",
)

args = parser.parse_args()

if not os.path.isdir(args.repository):
    raise NotImplementedError("Only local dataset dir is implemented.")

# NOTE: We assume all sweeps in a benchmark have the same metrics.
# We assume as well that the number of sweeps is constant for a given benchmark, and that a given sweep always reprensents the same hyperparameters.
# TODO: Relax this assumption. We assume as well that for a given (benchmark, sweep), the metrics do NOT change over time.
# We do NOT assume that the same benchmarks are done over time. New benchmarks can be added.

# Step 1: Separate on two projects: inference and training.
add_project("Inference", description="Benchmarks related to inference")
add_project("Training", description="Benchmarks related to training")

# Step 2: Add all commits data.
commits_data_paths = glob(os.path.join(args.repository, "raw_results") + "/*/", recursive=False)
available_commits = []
for commit_data_path in commits_data_paths:
    subdirectory_name = split_path(commit_data_path)[-1]
    available_commits.append(subdirectory_name.split("_")[-1])

# It is sligthly ugly to add the commit data twice, but we do it for readability.
for commit_sha in tqdm(available_commits, desc="Adding builds"):
    add_build("Training", commit_sha)
    add_build("Inference", commit_sha)

# Step 3: Add all benchmark series. A serie is a single (benchmark, sweep, metric)
available_series = glob(os.path.join(args.repository, "raw_results") + "/*/*/", recursive=False)

parsed_series = set()
unique_series = {}
for serie_path in available_series:
    raw_serie_name = split_path(serie_path)[-1]

    if raw_serie_name in parsed_series:
        continue
    parsed_series.add(raw_serie_name)

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

    with open(os.path.join(sweeps_paths[0], result_name)) as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"')
        data_read = [row for row in reader]
        metrics_list = data_read[0]
        try:
            metrics_list.remove("")  # optimum-benchmark adds an empty column, not sure why
        except ValueError:
            pass

    for i in range(n_sweeps):
        for metric_name in metrics_list:
            full_serie_name = serie_name + f"_{i}_{metric_name}"
            full_serie_name = full_serie_name.replace("(", "_")
            full_serie_name = full_serie_name.replace(")", "_")
            full_serie_name = full_serie_name.replace("/", "_")
            full_serie_name = full_serie_name.replace(".", "_")

            unique_series[full_serie_name] = {"project_id": project_id, "result_name": result_name, "metric_name": metric_name, "serie_subpath": os.path.join(raw_serie_name, str(i))}

for serie_name, serie_data in tqdm(unique_series.items(), desc="Adding series"):
    analyse = {
        "benchmark": {
            "range": "10%",
            "required": 5,
            "trend": "smaller",
        }
    }

    print("project_id", serie_data["project_id"])
    print("serie_id", serie_name)
    add_series(project_id=serie_data["project_id"], serie_id=serie_name, description="", analyse=analyse)

# Step 4: Add data for all series.
for commit_data_path in tqdm(commits_data_paths, desc="Adding samples for each commit"):
    subdirectory_name = split_path(commit_data_path)[-1]
    commit_sha = subdirectory_name.split("_")[-1]

    for serie_name, serie_data in unique_series.items():
        result_path = os.path.join(commit_data_path, serie_data["serie_subpath"], serie_data["result_name"])
        if not os.path.isdir(os.path.join(commit_data_path, serie_data["serie_subpath"])):
            print(f"WARNING: series {serie_name} not available for SHA {commit_sha}")
            continue
        else:
            print(f"INFO: series {serie_name} available for SHA {commit_sha}")
        with open(result_path) as fp:
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
            metric_data = metrics_data[serie_data["metric_name"]]

        sample = {
            "buildId": get_build_id(commit_sha),
            "value": metric_data,
        }
        add_sample(project_id=serie_data["project_id"], serie_id=serie_name, sample=sample)

print("Adding data to dana successful.")
