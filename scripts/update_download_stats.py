import os
import json
import requests
import csv
from datetime import datetime
from urllib.parse import urlparse
import git


def fetch_releases(repo_url):
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    user, repo = path_parts[-2], path_parts[-1]
    
    api_url = f'https://api.github.com/repos/{user}/{repo}/releases'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch releases for {user}/{repo}, status code: {response.status_code}")
    
    return response.json(), user, repo


def update_csv(file_path, new_row, headers, today):
    
    rows = []
    if os.path.isfile(file_path):
        with open(file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
    isFirst = False
    if rows:
        existing_headers = rows[0]
        existing_row = rows[1]
        
        # Remove columns missing in new headers from existing rows
        extra_columns = [col for col in existing_headers if col not in headers]
        for row in rows:
            for col in extra_columns:
                if col in row:
                    row.remove(col)
        
        # Add columns present in new headers but missing in existing rows
        missing_columns = [col for col in headers if col not in existing_headers]
        for row in rows:
            for col in missing_columns:
                row.append(0)

        # Update lastday if existing and new data rows are identical
        if existing_row[1:] == new_row[1:]:
            existing_row[-1] = new_row[-1]
        else:
            rows.insert(1, new_row)
    else:
        rows.append(new_row)
        isFirst = True
        
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
        
        if isFirst:
            my_repo.git.add(file_path)
        my_repo.git.commit('-m', f'Last update ; {today}')
        my_repo.git.push()


def get_asset_downloads(assets):
    download_counts = {}
    for asset in assets:
        asset_name = asset['name']
        download_count = asset['download_count']
        download_counts[asset_name] = download_count
    return download_counts


if __name__ == "__main__":
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    repositories = settings.get("repository_link")
    GITHUB_TOKEN = os.getenv('YOUR_GITHUB_TOKEN')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Initialize Git repository object
    my_repo = git.Repo('.')
    
    for repo_url in repositories:
        try:
            # Fetch releases information from GitHub API
            releases, user, repo = fetch_releases(repo_url)
        except Exception as e:
            print(f"Error fetching releases: {e}")
            continue

        repo_folder = f"{repo}"
        os.makedirs(repo_folder, exist_ok=True)

        releases_data = {}
        version_assets = {}

        for release in releases:
            release_tag = release['tag_name']
            release_assets = release['assets']
            
            asset_downloads = get_asset_downloads(release_assets)
            releases_data[release_tag] = asset_downloads
            
            version_assets[release_tag] = sorted(set(asset_downloads.keys()))

        for release_tag, asset_downloads in releases_data.items():
            release_file = os.path.join(repo_folder, f"{repo}_{release_tag}.csv")
            assets_name = version_assets.get(release_tag, [])

            headers = ['firstday', 'total'] + assets_name + ['lastday']
            release_data = [today]
            total_downloads = sum(asset_downloads.values())
            release_data.append(total_downloads)
            for asset_name in assets_name:
                release_data.append(asset_downloads.get(asset_name, 0))
            release_data.append(today)

            update_csv(release_file, release_data, headers, today)

       
        total_file = os.path.join(repo_folder, f"{repo}_total.csv")
        combined_total = sum(sum(asset_downloads.values()) for asset_downloads in releases_data.values())
        total_data = [today, combined_total, today]

        update_csv(total_file, total_data, ['firstday', 'total', 'lastday'], today)

    
    print("Download counts recorded successfully.")