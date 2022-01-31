from typing import List
import github
import github.GithubException
import requests
import zipfile
import io
from requests.auth import HTTPBasicAuth
import argparse


class Artifact:
    name: str
    url: str

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def download(self, dest_dir: str, username: str, token: str):
        r = requests.get(self.url, auth=HTTPBasicAuth(username, token))
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dest_dir)


def get_artifacts_for_run(
    run: github.WorkflowRun, username: str, token: str
) -> List[Artifact]:
    artifacts = []
    response = requests.get(
        run.artifacts_url, auth=HTTPBasicAuth(username, token)
    ).json()
    for artifact in response["artifacts"]:
        artifacts.append(Artifact(artifact["name"], artifact["archive_download_url"]))
    return artifacts


if __name__ == "__main__":
    DEFAULT_WORKFLOWS = "build_python_wheels.yml,build_python_wheels_aarch64.yml,build_python_wheels_macos.yml,build_python_wheels_windows.yml"
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--token", type=str, required=True)
    parser.add_argument("--commit", type=str, required=True)
    parser.add_argument(
        "--out_dir",
        type=str,
        default="out",
        help="Destination dir of downloaded artifacts",
    )
    parser.add_argument(
        "--max_lookback",
        type=int,
        default=100,
        help="How many runs backwards to search for the desired commit",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="Vowpalwabbit/vowpal_wabbit",
        help="Github account and repo to search",
    )
    parser.add_argument(
        "--workflows",
        type=str,
        default=DEFAULT_WORKFLOWS,
        help="Comma separated list of workflows to download artifacts for",
    )
    args = parser.parse_args()

    workflows_to_process = args.workflows.split(",")

    api = github.Github(args.username, args.token)
    repo = api.get_repo(args.repo)
    found_workflow_runs = []
    for workflow in workflows_to_process:
        try:
            found_workflow = repo.get_workflow(workflow)
        except github.GithubException as e:
            raise ValueError(f"Unknown workflow '{workflow}'")

        found_run = None
        for run in found_workflow.get_runs():
            if run.head_sha == args.commit:
                print("Found run for {}".format(workflow))
                found_run = run
                break
        if found_run is None:
            raise ValueError(
                f"Could not find run for {args.commit} in {workflow}. You can try increasing max lookback."
            )

        found_workflow_runs.append((workflow, found_run))

    found_artifacts = []
    for name, run in found_workflow_runs:
        artifacts = get_artifacts_for_run(run, args.username, args.token)
        found_artifacts.extend(artifacts)
        print("Discovered {} artifacts for {}".format(len(artifacts), name))

    for artifact in found_artifacts:
        print(f"Downloading {artifact.name}...")
        artifact.download(args.out_dir, args.username, args.token)
