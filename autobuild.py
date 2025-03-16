#!/usr/bin/env python3

import subprocess
import http.client
import requests
import hashlib

def commit(version):
    print("checking git status")
    statcode=subprocess.run("git status|grep 'nothing to commit'", shell=True)
    if statcode!=0:
        print("committing to git")
        commit=f"git commit -am 'autobuild for {version}'"
        tagetc=f"git tag {version}; git push; git push -f origin {version}"
        subprocess.run(commit, shell=True)
        subprocess.run(tagetc, shell=True)

current="2.5.0"

# query github
endpoint="https://api.github.com/repos/scratchfoundation/scratch-desktop/tags"
api=requests.get(endpoint)
jsonresp=api.json()

new_ver=current
url=""

releases=[]
for release in jsonresp:
    if release["prerelease"] == False:
        releases.append(release["tag_name"])

last_release=sorted(releases)[len(releases)-1]

for release in jsonresp:
    if release["tag_name"] == last_release:
        new_ver=release["tag_name"]
        for asset in release["assets"]:
            if asset["name"]=="Mudita-Center.AppImage":
                url=asset["browser_download_url"]

if url=="":
    print("URL not set. Bye.")
    exit()

if new_ver == current:
    print("no new version.")
    exit()

# update strings in files
update_files=["autobuild.py", ".github/workflows/build.yml", "com.mudita.mudita-center.yaml"]
for name in update_files:
    sed_expr=f"sed -e 's,{current},{new_ver},' -i {name}"
    print(sed_expr)
    subprocess.run(sed_expr, shell=True)

# update shasum in com.beeper.beeper.yaml
open('mudita-center.appimage', 'wb').write(requests.get(url).content)


sha256_hash = hashlib.sha256()
with open('mudita-center.appimage',"rb") as f:
    for byte_block in iter(lambda: f.read(4096),b""):
        sha256_hash.update(byte_block)
    shasum=sha256_hash.hexdigest()
    sed_expr=f"sed -e 's,sha256: .*,sha256: {shasum},' -i com.mudita.mudita-center.yaml"
    subprocess.run(sed_expr, shell=True)

commit(new_ver)
