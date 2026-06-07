#!/usr/bin/env python
#
# Copyright © 2022 Github Lzhiyong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=not-callable, line-too-long, no-else-return

import os
import requests
import tarfile
import shutil
import argparse
import subprocess
import json
from pathlib import Path

def untar(source, target):
    tar = tarfile.open(source)
    names = tar.getnames()
    if Path(target).is_dir():
        pass
    else:
        Path(target).mkdir()

    for name in names:
        tar.extract(name, target)
    tar.close()

def download(url, filename, target):
    print("downloading {}".format(filename))
    content = requests.get(url).content
    with open(filename, 'wb') as file:
        file.write(content)
    # extract tar file
    print("extracting {} to {}".format(filename, target))
    untar(filename, target)
    # delete file
    if Path(filename).exists():
        Path(filename).unlink()

def patches():
    inc = Path.cwd() / "src/incremental_delivery/sysprop/include"
    if not inc.exists():
        inc.mkdir()
    shutil.copy2(Path("patches/misc/IncrementalProperties.sysprop.h"), inc)
    shutil.copy2(Path("patches/misc/IncrementalProperties.sysprop.cpp"), inc.parent)

    shutil.copy2(Path("patches/misc/deployagent.inc"), Path("src/adb/fastdeploy/deployagent"))
    shutil.copy2(Path("patches/misc/deployagentscript.inc"), Path("src/adb/fastdeploy/deployagent"))

    shutil.copy2(Path("patches/misc/platform_tools_version.h"), Path("src/soong/cc/libbuildversion/include"))
    
    pattern = "\'s#frameworks/base/tools/aapt2/Configuration.proto#Configuration.proto#g\'"
    pattern2 = "\'s#frameworks/base/tools/aapt2/Resources.proto#Resources.proto#g\'"
    subprocess.run("sed -i {} {}".format(pattern2, Path.cwd() / "src/base/tools/aapt2/ApkInfo.proto"), shell=True)
    subprocess.run("sed -i {} {}".format(pattern, Path.cwd() / "src/base/tools/aapt2/Resources.proto"), shell=True)
    subprocess.run("sed -i {} {}".format(pattern, Path.cwd() / "src/base/tools/aapt2/ResourcesInternal.proto"), shell=True)
    subprocess.run("sed -i {} {}".format(pattern2, Path.cwd() / "src/base/tools/aapt2/ResourcesInternal.proto"), shell=True)
    
    pattern3 = "\'s#/usr/src/googletest#${CMAKE_SOURCE_DIR}/src/googletest#g\'"
    subprocess.run("sed -i {} {}".format(pattern3, Path.cwd() / "src/abseil-cpp/CMakeLists.txt"), shell=True)

    # symlink googletest to boringssl/**/googletest
    src = Path.cwd() / "src/googletest"
    dest = Path.cwd() / "src/boringssl/src/third_party/googletest"
    subprocess.run("ln -sf {} {}".format(src, dest), shell=True)

def check(command):
    try:
        output = subprocess.check_output("command -v {}".format(command), shell=True)
        print(output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("please install the {} package".format(command))
        exit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tags", default="master", help="Specify the Git cloning tags or branch")
    args = parser.parse_args()
    
    # check necessary packages
    check("git")
    check("go")
    check("bison")
    check("flex")
    
    # မူရင်းအတိုင်း repos.json ကို ဖတ်ပါသည်
    with open('repos.json', 'r') as file:
        repos = json.load(file)
        
    # Android 14 အတွက် မရှိမဖြစ်လိုအပ်သော repos လမ်းကြောင်းများကို မူရင်းစာရင်းထဲသို့ ပေါင်းထည့်ပေးခြင်း
    a14_repos = [
        {"path": "src/base", "url": "https://android.googlesource.com/platform/frameworks/base"},
        {"path": "src/logging", "url": "https://android.googlesource.com/platform/system/logging"},
        {"path": "src/core", "url": "https://android.googlesource.com/platform/system/core"},
        {"path": "src/libziparchive", "url": "https://android.googlesource.com/platform/system/libziparchive"},
        {"path": "src/incremental_delivery", "url": "https://android.googlesource.com/platform/system/incremental_delivery"}
    ]
    
    # ထပ်နေသော လမ်းကြောင်းများကို ဖယ်ထုတ်ပြီး စာရင်းထဲ ထည့်သွင်းပါသည်
    existing_paths = {r['path'] for r in repos}
    for r in a14_repos:
        if r['path'] not in existing_paths:
            repos.append(r)
    
    # git clone submodules (မူရင်းအတိုင်း သတိပေးချက်များနှင့် error များကို ပိတ်မထားဘဲ အကုန်ပြပါမည်)
    for repo in repos:
        if not Path(repo['path']).exists():
            subprocess.run('git clone --depth 1 --branch {} {} {}'.format(args.tags, repo['url'], repo['path']), shell=True)
    
    # patch files
    try:
        patches()
    except Exception as e:
        print("Warning during patches: {}".format(e))
    
    print("download success!!")

if __name__ == "__main__":
    main()
