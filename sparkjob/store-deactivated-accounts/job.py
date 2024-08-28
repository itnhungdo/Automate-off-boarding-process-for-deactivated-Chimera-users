import os
import requests
import git
from git import Repo
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import argparse

def __parse_args():
    parser = argparse.ArgumentParser(description="Delete deactivated accounts and create merge requests in GitLab.")
    
    parser.add_argument('--access-token', required=True, help="GitLab access token")
    parser.add_argument('--base-url', required=True, help="Base URL of the GitLab API")
    parser.add_argument('--project-id', required=True, help="Project ID or namespace/project_name")
    parser.add_argument('--target-branch', required=True, default='master', help="The branch to merge into (default: 'master')")
    parser.add_argument('--repo-path', required=True, help="Path to the Git repository")
    parser.add_argument('--slack-token', required=True, help="Slack token for authenticating the Slack API")
    
    args = parser.parse_args()
    
    return args
def delete_deactivated_accounts(access_token, base_url, project_id, target_branch, repo_path, users_to_delete, slack_token):
    """
    This function deletes deactivated user files from a repository, commits the changes,
    creates a new branch for each department, and submits a merge request.
    
    Parameters:
    - access_token: GitLab personal access token
    - base_url: Base URL of the GitLab API
    - project_id: Project ID or namespace/project_name
    - target_branch: The branch to merge into (e.g., 'master')
    - repo_path: Path to the local Git repository
    - users_to_delete: Dictionary with departments as keys and lists of user names as values
    - slack_token: Slack token for sending notifications
    """
    
    # Initialize repository
    repo = Repo(repo_path)
    repo.git.checkout(target_branch)

    # Loop through each department and process user deletions
    for department, users in users_to_delete.items():
        # Create a unique branch name using department name and timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        source_branch = f'delete-deactivated-accounts-{department}-{timestamp}'
        
        repo.git.checkout('-b', source_branch)
        
        # Delete user files in the department
        for user in users:
            user_file = f"{user}.yaml"
            file_path = os.path.join(repo_path, 'department', department, user_file)

            if os.path.exists(file_path):
                os.remove(file_path)
                repo.git.rm(file_path)
                print(f"Deleted {file_path}")
            else:
                print(f"File {file_path} does not exist")
        
        # Commit changes and push to remote
        commit_message = f"Delete deactivated accounts in {department} department"
        repo.git.add(update=True)
        repo.git.commit('-m', commit_message)
        
        origin = repo.remote(name='origin')
        origin.push(source_branch)
        
        # Create Merge Request
        url = f'{base_url}/projects/{project_id}/merge_requests'
        headers = {
            'Private-Token': access_token
        }

        data = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': commit_message,
            'description': f'Automatically created MR for deleting deactivated accounts in the {department} department.'
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            mr_url = response.json()['web_url']
            print(f"Merge request created successfully for {department}: {mr_url}")
            notify_slack(slack_token, department, mr_url)
        else:
            print(f"Failed to create merge request for {department}: {response.status_code}, {response.text}")
        
        # Checkout back to the target branch before processing the next department
        repo.git.checkout(target_branch)

def notify_slack(slack_token, department, mr_url):
    """
    Sends a notification to the 'chimera-users' Slack channel with the details of the merge request
    and mentions the department owners.

    Parameters:
    - slack_token: The Slack token for authenticating the Slack API
    - department: The department name for which the MR was created
    - mr_url: The URL of the created merge request
    """
    client = WebClient(token=slack_token)
    mention_text = f"@{department}-owners"

    message = f"{mention_text} Merge request created successfully for *{department}* department: {mr_url}"

    try:
        response = client.chat_postMessage(
            channel="chimera-users",
            text=message
        )
        print(f"Slack notification sent successfully for {department}")
    except SlackApiError as e:
        print(f"Error sending Slack message: {e.response['error']}")

if __name__ == "__main__":
    args = __parse_args()
    users_to_delete = {
        "department1": ["user1", "user2"],
        "department2": ["user3", "user4"]
    }
    delete_deactivated_accounts(
        args.access_token,
        args.base_url,
        args.project_id,
        args.target_branch,
        args.repo_path,
        users_to_delete,
        args.slack_token
    )
   
