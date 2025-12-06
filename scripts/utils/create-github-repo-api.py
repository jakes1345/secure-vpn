#!/usr/bin/env python3
"""Create GitHub repo and push using GitHub API"""
import sys
import subprocess
import json
import urllib.request
import urllib.error

def create_github_repo(token, username, repo_name, description="Secure VPN Browser with comprehensive privacy features"):
    """Create a GitHub repository using the API"""
    url = "https://api.github.com/user/repos"
    
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode())
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return True, result.get("clone_url"), result.get("ssh_url")
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        return False, f"HTTP {e.code}: {error_data}", None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 create-github-repo.py <token> <username> <repo-name>")
        print("Get token from: https://github.com/settings/tokens")
        sys.exit(1)
    
    token = sys.argv[1]
    username = sys.argv[2]
    repo_name = sys.argv[3]
    
    print(f"Creating repository: {username}/{repo_name}...")
    success, result, ssh_url = create_github_repo(token, username, repo_name)
    
    if success:
        print(f"✅ Repository created!")
        print(f"   HTTPS: {result}")
        print(f"   SSH: {ssh_url}")
        
        # Add remote and push
        print("\n📡 Adding remote...")
        subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", ssh_url])
        
        print("⬆️  Pushing to GitHub...")
        result = subprocess.run(["git", "push", "-u", "origin", "main"])
        
        if result.returncode == 0:
            print("\n✅✅✅ Successfully pushed to GitHub! ✅✅✅")
            print(f"\nRepository: https://github.com/{username}/{repo_name}")
        else:
            print("\n❌ Push failed. Check your SSH key is added to GitHub.")
    else:
        print(f"❌ Failed to create repository: {result}")
