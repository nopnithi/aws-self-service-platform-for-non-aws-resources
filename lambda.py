import os
import shutil
import json
import logging
import datetime
import boto3
import pytz
from git import Repo
from crhelper import CfnResource
from botocore.exceptions import ClientError
from typing import Dict


helper = CfnResource()

@helper.create
def initialize_repo(event, _):
    try:
        logging.info('Starting script...')

        # Get the Azure DevOps data from the environment variables
        azdo_org = os.environ.get('AZDO_ORG')
        azdo_project = os.environ.get('AZDO_PROJECT')
        azdo_init_iac_repo = os.environ.get('AZDO_INIT_IAC_REPO')
        azdo_pat_secret_name = os.environ.get('AZDO_PAT_SECRET_NAME')
        base_path = os.environ.get('BASE_PATH')

        # Retrieve Azure DevOps personal access token from AWS Secrets Manager
        azdo_pat = get_azdo_pat(azdo_pat_secret_name)

        # Get the parameters from the event
        params = {
            'aws_account_id': event['ResourceProperties']['AwsAccountId'],
            'project': event['ResourceProperties']['Project'],
            'environments': event['ResourceProperties']['Environments'].split(','),
            'stacks': event['ResourceProperties']['Stacks'].split(','),
            'initial_environments': event['ResourceProperties']['InitialEnvironments'].split(','),
            'initial_stacks': event['ResourceProperties']['InitialStacks'].split(','),
            'approver_email': event['ResourceProperties']['ApproverEmail']
        }

        # Clone the repository to the destination path
        repo_url = f'https://{azdo_pat}@dev.azure.com/{azdo_org}/{azdo_project}/_git/{azdo_init_iac_repo}'
        clone_repository(repo_url, f'{base_path}/{azdo_init_iac_repo}')

        # Set Git user and email
        git_user = 'Nopnithi Khaokaew (Game)'
        git_email = 'me@nopnithi.dev'
        set_git_config(f'{base_path}/{azdo_init_iac_repo}', git_user, git_email)

        # Generate the .tfvars file from the parameters
        generate_tfvars_file(params, f'{base_path}/{azdo_init_iac_repo}')

        # Commit and push the changes to the remote repository
        commit_and_push_changes(
            f'{base_path}/{azdo_init_iac_repo}', params['project'],
            f'feat: Initialize IaC repository for project "{params["project"]}"'
        )
        logging.info('Script completed successfully.')
    except Exception as e:
        logging.error(f'Error running script: {str(e)}')
        raise e

@helper.update
@helper.delete
def no_op(_, __):
    pass

def handler(event, context):
    helper(event, context)

def clone_repository(repo_url: str, repo_path: str) -> None:
    """
    Clones a Git repository using the GitPython library.
    """
    try:
        logging.info('Cloning repository...')
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        Repo.clone_from(repo_url, repo_path)
        logging.info('Repository cloned successfully.')
    except Exception as e:
        logging.error(f'Error cloning repository: {str(e)}')
        raise e

def set_git_config(repo_path: str, user: str, email: str) -> None:
    """
    Sets the Git user and email for the repository.
    """
    try:
        logging.info('Setting Git user and email...')
        with Repo(repo_path) as repo:
            repo.config_writer().set_value("user", "name", user).release()
            repo.config_writer().set_value("user", "email", email).release()
        logging.info('Git user and email set successfully.')
    except Exception as e:
        logging.error(f"Error setting Git user and email: {str(e)}")
        raise e

def build_tfvars_content(params: Dict[str, str]) -> str:
    """
    Builds the content of the .tfvars file from the received parameters.
    """
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.datetime.now(tz=tz)
    content = f'# Auto-generated via service catalog at {now}\n\n'
    for key, value in params.items():
        if isinstance(value, list):
            value_str = '[' + ', '.join([f'"{v}"' for v in value]) + ']'
        else:
            value_str = f'"{value}"'
        content += f'{key:<21}= {value_str}\n'
    return content

def generate_tfvars_file(params: Dict[str, str], repo_path: str) -> None:
    """
    Generates the .tfvars file from the received parameters.
    """
    try:
        logging.info('Generating .tfvars file...')
        content = build_tfvars_content(params)

        project_path = f'{repo_path}/projects'
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        tfvars_path = f'{project_path}/{params["project"]}.tfvars'
        with open(tfvars_path, 'w') as file:
            file.write(content)

        logging.info(f'{params["project"]}.tfvars file generated successfully.')
    except Exception as e:
        logging.error(f'Error generating .tfvars file: {str(e)}')
        raise e

def commit_and_push_changes(repo_path: str, project: str, commit_message: str) -> None:
    """
    Commits and pushes the changes to the remote repository.
    """
    try:
        logging.info('Committing and pushing changes...')
        with Repo(repo_path) as repo:
            index = repo.index
            index.add(f'projects/{project}.tfvars')
            index.commit(commit_message)
            origin = repo.remote(name='origin')
            origin.push()
        logging.info('Changes committed and pushed successfully.')
    except Exception as e:
        logging.error(f'Error committing and pushing changes: {str(e)}')
        raise e

def get_azdo_pat(secret_name: str) -> str:
    """
    Retrieves the Azure DevOps personal access token from AWS Secrets Manager.
    """
    secrets_manager = boto3.client('secretsmanager')
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret['token']
    except ClientError as e:
        print(f'Error getting secret {secret_name}: {e}')
        raise e
