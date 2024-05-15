#!/bin/bash/python3

# Import packages which are used throughout the program
import os
import json
import glob
import shutil
import zipfile
import requests # This package may need to be installed manually

def main():
    print("This python script will create a large amount of files and as a result will take up more than 15GB of data. It is also relitively slow.")
    print("Press [ENTER] to achknowledge this and continue with the asset fetching: ", end='')
    input()

    # Check if the MC-Assets directory exists, if so, exit with a warning.
    if os.path.exists('MC-Assets'):
        print('MC-Assets directory already exists, please delete it if you want to refetch all the assets.')
        exit()
    
    # If the above fails, make the MC-Assets directory and change directory into it
    os.makedirs('MC-Assets/assets')
    os.chdir('MC-Assets')

    # Declare some variables to be used later
    mcVersionManifests = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').json()
    mcAssetHashes = []

    for version in mcVersionManifests['versions']:
        if version['id'] == '1.5.2':
            break
        else:
            if version['type'] == 'release':
                mcCurrentVersionManifest = requests.get(version['url']).json()
                mcGameAssetIndex = requests.get(mcCurrentVersionManifest['assetIndex']['url']).json()

                # Save the asset index for later usage, this avoids pointless calls to the API.
                with open(version['id'] + '.json', 'w') as mcCurrentAssetIndex:
                    mcCurrentAssetIndex.write(str(mcGameAssetIndex).replace("'", "\""))

                # Download and extract assets from the currently processing MC version jar file
                print('Downloading MC ' + version['id'] + '.jar', end='')
                open(version['id'] + '.jar', 'wb').write(requests.get(mcCurrentVersionManifest['downloads']['client']['url']).content)
                print(' (Done)')
                print('Extracting assets from MC ' + version['id'] + '.jar', end='')
                with zipfile.ZipFile(version['id'] + '.jar', 'r') as currentJar:
                    for item in currentJar.namelist():
                        if item.startswith('assets/'):
                            currentJar.extract(item, version['id'])
                print(' (Done)')
                print('Deleting MC ' + version['id'] + '.jar', end='')
                os.remove(version['id'] + '.jar')
                print(' (Done)\n')

                # Get a list of assets used for the currently processing version
                print('Populating asset hashes for MC ' + version['id'], end='')
                for asset in mcGameAssetIndex['objects']:
                    mcAssetHashes.append(mcGameAssetIndex['objects'][asset]['hash'])
                print(' (Done)')

    # Remove duplicate hashes and download all the populated assets for Minecraft
    mcAssetHashes = list(set(mcAssetHashes))
    os.chdir('assets')
    totalHashCount = len(mcAssetHashes)
    i = 0
    for mcHash in mcAssetHashes:
        try:
            os.mkdir(mcHash[:2])
        except:
            pass
        currentAssetHashPath = mcHash[:2] + '/' + mcHash
        i += 1
        print(f'Downloading: {mcHash} [{str(i).zfill(len(str(totalHashCount)))}/{totalHashCount}]', end='')
        open(currentAssetHashPath, 'wb').write(requests.get('https://resources.download.minecraft.net/' + currentAssetHashPath).content)
        print(' (Done)')
   
    # Copy the correct assets to each version folder
    os.chdir('..')
    for file in glob.glob('*.json'):
        print(f'Copying {file.strip(".json")} assets to their respective folders', end='')
        if file.strip(".json") == "1.6.1" or "1.6.2" or "1.6.4" or "1.7.2":
            with open(file, 'r') as badFile:
                fileContents = badFile.read()
            fileContents = fileContents.replace("True", "true")
            with open(file, 'w') as badFile:
                badFile.write(fileContents)
        with open(file) as currentManifest:
            currentManifest = json.load(currentManifest)
            for asset in currentManifest['objects']:
                currentHash = currentManifest['objects'][asset]['hash']
                currentVersion = file.strip(".json")
                try:
                    if "/" in asset:
                        os.makedirs(currentVersion + '/' + 'assets/' + asset.rsplit("/", 1)[0])
                except:
                    pass
                if "/" in asset:
                    shutil.copyfile('assets/' + currentHash[:2] + '/' + currentHash, currentVersion + '/assets/' + asset)
                else:
                    shutil.copyfile('assets/' + currentHash[:2] + '/' + currentHash, currentVersion + '/' + asset)
        os.remove(file)
        print(' (Done)')
    
    # Clean up the master assets directory as the script has finished it's sole task
    print("Removing residual asset files")
    shutil.rmtree('assets')
    print(' (Done)')

if __name__ == '__main__':
    main()
