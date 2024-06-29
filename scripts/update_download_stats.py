import os
import json
import requests
import csv
from datetime import datetime
from urllib.parse import urlparse

# settings.json 파일에서 리포지토리 목록 가져오기
with open('settings.json', 'r') as f:
    settings = json.load(f)

repositories = settings.get("repository_link", [])

# GitHub API 토큰 (환경 변수에서 가져오기)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# 현재 날짜
today = datetime.now().strftime('%Y-%m-%d')

def fetch_releases(repo_url):
    # URL 파싱하여 사용자명과 리포지토리명 추출
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    user, repo = path_parts[-2], path_parts[-1]
    
    api_url = f'https://api.github.com/repos/{user}/{repo}/releases'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    response = requests.get(api_url, headers=headers)
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
        if rows[1][0] == new_row[0]:  # 중복값 처리
            rows[1] = new_row
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
    releases, user, repo = fetch_releases(repo_url)

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