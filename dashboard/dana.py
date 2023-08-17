from typing import Dict
import requests
import git
import json

TRANSFORMERS_PATH = "/home/fxmarty/hf_internship/transformers"
API_URL = "http://localhost:7000/"

def get_header():
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer admin",
    }

def get_build_id(commit_sha: str):
    repository = git.Repo(TRANSFORMERS_PATH)
    commit = repository.commit(commit_sha)
    build_id = commit.count()
    return build_id

def add_project(project_id: str, description: str):
    session = requests.Session()
    header = get_header()

    data = {
        "username": "admin",
        "password": "admin",
    }

    login_result = session.post(API_URL + "login", data=json.dumps(data), headers=header)

    data = {
        "projectId": project_id,
        "description": description,
        "users": "",
    }
    result = session.post(API_URL + "admin/addProject", data=json.dumps(data), headers=header)

    if result.status_code != 200:
        raise ValueError(f"add_project failed with status code {result.status_code} and result: {result.text}")

    return result


def add_build(project_id: str, commit_sha: str, override: bool = False, strict: bool = True):

    repository = git.Repo(TRANSFORMERS_PATH)
    commit = repository.commit(commit_sha)

    author = commit.author.name
    email = commit.author.email
    title = commit.summary
    build_id = commit.count()
    sha_abbreviation = commit_sha[:8]

    header = get_header()

    data = {
        "projectId": project_id,
        "build": {
            "buildId": build_id,
            "infos": {
                "hash": commit_sha,
                "abbrevHash": sha_abbreviation,
                "authorName": author,
                "authorEmail": email,
                "subject": title,
                "url": None,
            }
        },
        "override": override,
    }

    result = requests.post(API_URL + "apis/addBuild", data=json.dumps(data), headers=header)

    if strict and result.status_code != 200:
        raise ValueError(f"add_build failed with status code {result.status_code} and result: {result.text}")

    return result


def add_series(project_id: str, serie_id: str, description: str, analyse: Dict, strict: bool = True):
    data = {
        "projectId": project_id,
        "serieId": serie_id,
        "description": description,
        "analyse": analyse,
    }

    header = get_header()

    result = requests.post(API_URL + "apis/addSerie", data=json.dumps(data), headers=header)

    if strict and result.status_code != 200:
        raise ValueError(f"add_series failed with status code {result.status_code} and result: {result.text}")

    return result

def add_sample(project_id: str, serie_id: str, sample: Dict, override: bool = False, strict: bool = True):

    data = {
        "projectId": project_id,
        "serieId": serie_id,
        "sample": sample,
        "override": override,
    }

    header = get_header()

    result = requests.post(API_URL + "apis/addSample", data=json.dumps(data), headers=header)

    if strict and result.status_code != 200:
        raise ValueError(f"add_sample failed with status code {result.status_code} and result: {result.text}")

    return result

if __name__ == "__main__":
    #add_build("Test", "26ce4dd8b79dce59e183a8aeefe20e7e98a49113")

    """
    analyse = {"benchmark": {"range": "5%", "required": 2, "trend": "smaller"}}
    add_series(project_id="Test", serie_id="new_inference", description="This is a new esries.", analyse=analyse)

    sample = {
        "buildId": 1003,
        "value": 1200,
    }
    add_sample(project_id="Test", serie_id="new_inference", sample=sample)
    add_sample(project_id="Test", serie_id="inference.dummy", sample=sample)
    """
    add_project("Training", description="Benchmarks related to training")
