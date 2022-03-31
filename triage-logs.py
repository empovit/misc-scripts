#!/usr/bin/env python3

# This script takes a URL of a directory in the NGINX-file browser format (https://github.com/mohamnag/nginx-file-browser),
# and downloads its contents into a subdirectory inside the working directory. A name of the destination directory can be
# either given as the second argument (after the URL), or will be derived from the last part of the URL. Files in the known
# archive formats will be unpacked.
#
# Example: http://logs.example.com/#/2022-03-30_20:14:19_fab47716-04e6-401b-8b89-e414d030a298/ will be converted into 
# http://logs.example.com/files/2022-03-30_20:14:19_fab47716-04e6-401b-8b89-e414d030a298/, which returns a JSON list of files
# and subdirectories. The files/directories will be recursively downloaded into "2022-03-30_20-14-19_fab47716-04e6-401b-8b89-e414d030a298".

import shutil
import sys
import os
import requests
from os import path

archive_extensions = []
for a in shutil.get_unpack_formats():
    archive_extensions.extend(a[1])

def download_dir(base_url, dest):
    os.makedirs(dest)
    r = requests.get(base_url)
    for f in r.json():
        f_name = f["name"]
        f_type = f["type"]
        if f_type == "file":
            download_file(path.join(base_url, f_name), path.join(dest, f_name))
            try_unpack(dest, f_name)
        elif f_type == "directory":
            download_dir(path.join(base_url, f_name), path.join(dest, f_name))
        else:
            print(f"Unknown type: {f_type}")

def download_file(base_url, dest):
    r = requests.get(base_url, stream=True)
    with open(dest, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

def try_unpack(dest, name):
    for ext in archive_extensions:
        if name.endswith(ext):
            archive_path = path.join(dest, name)
            dest_path = path.join(dest, name[:-len(ext)])
            shutil.unpack_archive(archive_path, dest_path)
            os.remove(archive_path)
            unpack_all(dest_path)
            break

def unpack_all(directory):
    for f in os.listdir(directory):
        full_path = path.join(directory, f)
        if path.isdir(full_path):
            unpack_all(full_path)
        elif path.isfile(full_path):
            try_unpack(directory, f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {path.basename(__file__)} <url> [<destination inside working directory>]")
        exit(1)

    base_url = sys.argv[1].replace("#", "files")
    if len(sys.argv) > 2:
        dir_name = sys.argv[2]
    else:
        full_path = base_url.split("/")
        dir_name = full_path[-2] if full_path[-1] == "" else full_path[-1]
        dir_name = dir_name.replace(":", "-")
        
    dest_dir = path.join(os.getcwd(), dir_name)
    print(f"Downloading artifacts\n\tSource: {base_url}\n\tDestination: {dest_dir}")
    download_dir(base_url, dest_dir)
