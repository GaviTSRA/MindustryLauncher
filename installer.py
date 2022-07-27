import requests

def getVersions(repo, amount, token):
    res = requests.get(f"https://api.github.com/repos/{repo}/releases?per_page={amount}", headers={"Authorization": "token " + token}).json()
    builds = {}

    for build in res:
        download_url = ""
        tag = build["tag_name"]

        for file in build["assets"]:
            if not "server" in file["name"].lower() and not "android" in file["name"].lower():
                file_size = file["size"]
                asset_id = file["id"]
                name = file["name"]
        download_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
        builds[tag] = (download_url, file_size)

    return builds


def save_file(url, path, file_size, token):
    downloaded = 0
    data = requests.get(url, headers={"Authorization": "token " + token, "Accept": "application/octet-stream"}, stream=True)
    with open(path, "wb") as fi:
        for chunk in data.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                downloaded += len(chunk)
                fi.write(chunk)                
                yield downloaded / file_size