from ghapi.all import GhApi
import requests
import zipfile
import io
from requests.auth import HTTPBasicAuth

USERNAME = ""
TOKEN = "" # Requires actions scope
BRANCH = ""

api = GhApi(owner='VowpalWabbit', repo='vowpal_wabbit',token=TOKEN)
runs_for_branch = api.actions.list_workflow_runs_for_repo(branch=BRANCH).workflow_runs
commit_id_for_most_recent_run = runs_for_branch[0].head_commit.id
runs_for_commit_id = [x for x in runs_for_branch if x.head_commit.id == commit_id_for_most_recent_run]

macos_wheel_run = next(x for x in runs_for_commit_id if x.name == "Build MacOS Python Wheels")
linux_wheel_run = next(x for x in runs_for_commit_id if x.name == "Build Linux Python Wheels")
windows_wheel_run = next(x for x in runs_for_commit_id if x.name == "Build Windows Python Wheels")
artifacts = []
artifacts.extend(api.actions.list_workflow_run_artifacts(macos_wheel_run.id).artifacts)
artifacts.extend(api.actions.list_workflow_run_artifacts(linux_wheel_run.id).artifacts)
artifacts.extend(api.actions.list_workflow_run_artifacts(windows_wheel_run.id).artifacts)

for artifact in artifacts:
    r = requests.get(artifact.archive_download_url,  auth=HTTPBasicAuth(USERNAME, TOKEN))
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()
