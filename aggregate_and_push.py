import argparse
import huggingface_hub
from glob import glob
import os
from pathlib import Path
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
    help="Hugging Face Hub repository id to push to.",
)

args = parser.parse_args()

available_commits = glob("sweeps/*/", recursive=False)

commit_subdirectory = None
for subdir in available_commits:
    if args.commit in subdir:
        commit_subdirectory = Path(subdir).parts[1]
        break

if commit_subdirectory is None:
    raise ValueError(f"Requested to save results for the SHA {args.commit}, which was not found among {available_commits}.")

repo_id = "fxmarty/transformers-regressions"
files_info = huggingface_hub.list_files_info(repo_id, repo_type="dataset")

paths = [f.rfilename for f in files_info]

if any(args.commit in path for path in paths):
    print(f"WARNING: the commit {args.commit} has already been tested. This warning can be ignored if the regression is expected to rerun for this commit.")

api = huggingface_hub.HfApi(token=args.token)

available_benchmarks_for_commit = glob(f"sweeps/{commit_subdirectory}/*/", recursive=False)

operations = []
for benchmark_dir in available_benchmarks_for_commit:
    operations.extend([
        huggingface_hub.CommitOperationAdd(
            path_in_repo=os.path.join("raw_results", commit_subdirectory, benchmark_dir, file_name), path_or_fileobj=os.path.join(benchmark_dir, file_name)
        )
        for file_name in os.listdir(benchmark_dir)
    ])

# TODO: add aggregation in the same commit (to later be visualized by e.g. dana),
# it could be in a proper dataset that is updated.

new_pr = api.create_commit(
    repo_id=repo_id,
    repo_type="dataset",
    operations=operations,
    commit_message=f"Adding regression benchmark for the transformers SHA {args.commit}",
)