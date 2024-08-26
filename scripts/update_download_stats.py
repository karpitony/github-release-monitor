import os
import json
import requests
import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from urllib.parse import urlparse

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


def update_csv(file_path, new_row, headers):
    rows = []
    updated = False

    if os.path.isfile(file_path):
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            
            for i, row in enumerate(rows[1:], start=1):
                if len(row) > 0 and row[0] == new_row[0]:
                    rows[i] = new_row
                    updated = True
                    break

    if not updated:
        rows.insert(1, new_row)

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not rows or rows[0] != headers:
            writer.writerow(headers)
        writer.writerows(rows)


def get_asset_downloads(assets):
    download_counts = {}
    for asset in assets:
        asset_name = asset['name']
        download_count = asset['download_count']
        download_counts[asset_name] = download_count
    return download_counts


def update_project_info_json(new_folder, config_data):
    if new_folder not in config_data["folder_list"]:
        config_data["folder_list"].append(new_folder)
        config_data["last_update"] = datetime.now().strftime('%Y-%m-%d')
        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(config_data, file, indent=4, ensure_ascii=False)


def visualize_two_weeks_data(folder):
    total_csv_path = os.path.join(folder, f"{folder}_total.csv")
    if not os.path.exists(total_csv_path):
        print(f"No total.csv found in {folder}, skipping visualization.")
        return
    
    dates = []
    totals = []
    two_weeks_ago = datetime.now() - timedelta(days=14)

    with open(total_csv_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Skip the header row
        for row in reader:
            date = datetime.strptime(row[0], '%Y-%m-%d')
            if date >= two_weeks_ago:
                dates.append(date)
                totals.append(int(row[1]))
    
    if dates:
        plt.figure(figsize=(10, 6))
        plt.plot(dates, totals, marker='o', linestyle='-', color='b')
        plt.title(f'Downloads Over the Last 14 Days for {folder}')
        plt.xlabel('Date')
        plt.ylabel('Total Downloads')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(folder, f'{folder}_two_weeks.png'))
        plt.close()
        print(f"Two weeks download visualization saved as '{folder}_two_weeks.png' in {folder}.")
    else:
        print(f"No data available for the last 14 days in {folder}.")


if __name__ == "__main__":
    # Load configuration from config.json
    with open('config.json', 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    repositories = config_data.get("repository_links")
    GITHUB_TOKEN = os.getenv('YOUR_GITHUB_TOKEN')
    today = datetime.now().strftime('%Y-%m-%d')
    
    for repo_url in repositories:
        try:
            # Fetch releases information from GitHub API
            releases, user, repo = fetch_releases(repo_url)
        except Exception as e:
            print(f"Error fetching releases: {e}")
            continue

        repo_folder = f"{repo}"
        is_new_folder = not os.path.exists(repo_folder)
        os.makedirs(repo_folder, exist_ok=True)

        if is_new_folder:
            # Update config.json with new folder
            update_project_info_json(repo_folder, config_data)

        for release in releases:
            release_tag = release['tag_name']
            release_assets = release['assets']
            
            asset_downloads = get_asset_downloads(release_assets)
            
            release_file = os.path.join(repo_folder, f"{repo}_{release_tag}.csv")
            headers = ['Date', 'Total'] + list(asset_downloads.keys())
            
            release_data = [today, sum(asset_downloads.values())] + list(asset_downloads.values())
            
            update_csv(release_file, release_data, headers)

        total_file = os.path.join(repo_folder, f"{repo}_total.csv")
        combined_total = sum(sum(get_asset_downloads(release['assets']).values()) for release in releases)
        total_data = [today, combined_total]
        
        update_csv(total_file, total_data, ['Date', 'Total'])
        
        # Visualize data for this repository
        visualize_two_weeks_data(repo_folder)

    print("Download counts recorded successfully.")
