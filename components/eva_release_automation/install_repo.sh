#!/bin/bash

set -e

# Check if the repository has been set from the environment variable
if [[ -z "$SOURCE_GITHUB_REPOSITORY" ]] ; then SOURCE_GITHUB_REPOSITORY=EBIvariation/eva-release-automation ; fi
if [[ -z "$SOURCE_GITHUB_REF" ]] ; then SOURCE_GITHUB_REF=main ; fi
if [[ -n "$SOURCE_GITHUB_SHA" ]] ; then SOURCE_GITHUB_REF=$SOURCE_GITHUB_SHA ; fi

#TODO: Remove before merging the PR
SOURCE_GITHUB_REPOSITORY=tcezard/eva-release-automation
SOURCE_GITHUB_REF=partial-release

echo "Clone https://github.com/${SOURCE_GITHUB_REPOSITORY}.git"
git clone https://github.com/${SOURCE_GITHUB_REPOSITORY}.git eva-release-automation
cd eva-release-automation
git checkout ${SOURCE_GITHUB_REF}
git -c user.email="integration-test@ebi.ac.uk" -c user.name="Integration Test" merge origin/use_hard_links

python -m pip install .

cd ..
