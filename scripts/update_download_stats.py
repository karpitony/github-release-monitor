import os
import json
import requests
import csv
from datetime import datetime
from urllib.parse import urlparse


with open('settings.json', 'r') as f:
    settings = json.load(f)

repositories = settings.get("repository_link", [])

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
today = datetime.now().strftime('%Y-%m-%d')

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

def write_csv(file_path, data, headers):
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)
        writer.writerows(data)

def update_csv(file_path, new_row, headers):
    rows = []
    if os.path.isfile(file_path):
        with open(file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
    
    if rows:
        # 기존 데이터의 첫 행을 헤더로, 두 번째 행을 데이터로 간주
        header, *data_rows = rows
        existing_row = data_rows[0] if data_rows else None

        if existing_row and existing_row[1:] == new_row[1:]:  # total과 에셋들을 비교
            existing_row[-1] = new_row[-1]  # 중복 시 lastday만 업데이트
        else:
            rows.insert(1, new_row)
    else:
        rows.append(new_row)
        
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

def get_asset_downloads(assets):
    download_counts = {}
    for asset in assets:
        asset_name = asset['name']
        download_count = asset['download_count']
        download_counts[asset_name] = download_count
    return download_counts

for repo_url in repositories:
    try:
        releases, user, repo = fetch_releases(repo_url)
    except Exception as e:
        print(f"Error fetching releases: {e}")
        continue

    repo_folder = f"{repo}"
    os.makedirs(repo_folder, exist_ok=True)

    all_assets = set()
    releases_data = {}

    for release in releases:
        release_tag = release['tag_name']
        release_assets = release['assets']
        asset_downloads = get_asset_downloads(release_assets)
        for asset in asset_downloads:
            all_assets.add(asset)
        
        releases_data[release_tag] = asset_downloads

    for release_tag, asset_downloads in releases_data.items():
        release_file = os.path.join(repo_folder, f"{repo}_{release_tag}.csv")
        
        headers = ['firstday', 'total'] + sorted(all_assets) + ['lastday']
        release_data = [today]
        total_downloads = sum(asset_downloads.values())
        release_data.append(total_downloads)
        for asset in sorted(all_assets):
            release_data.append(asset_downloads.get(asset, 0))
        release_data.append(today)

        update_csv(release_file, release_data, headers)

    total_file = os.path.join(repo_folder, f"{repo}_total.csv")
    combined_total = sum(sum(asset_downloads.values()) for asset_downloads in releases_data.values())
    total_data = [today, combined_total, today]

    update_csv(total_file, total_data, ['firstday', 'total', 'lastday'])

print("Download counts recorded successfully.")
