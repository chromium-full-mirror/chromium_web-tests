#!/bin/bash

# DO NOT USE THIS SCRIPT. THIS SHOULD ONLY BE USED ON THE TOK 'LAB' DEVICE.
if [ "$USER" != "crossbench-lab" ]; then
  echo 'This script should only be run on the lab device in the TOK lab.'
  exit 1
fi

CUJ_DIR=$(dirname "$0")
SECRETS_FILE="/home/crossbench-lab/secrets.hjson"

ADB_DEVICES=("[2401:fa00:480:ee08:877f:adf8:8a66:4840]:5555")
CHROMEOS_DEVICES=("Servo-88541f0f72f8")

clean_git() {
    dir=$1

    echo "Cleaning git checkout $dir"

    cd $dir

    git reset --hard
    git checkout main
    git pull
    git submodule update

    cd -
}

run_and_upload() {
    cd "${CUJ_DIR}/runner"
    poetry run python runner/main.py --target "$1" --secrets-config-file "${SECRETS_FILE}"
    cd -
    cd "${CUJ_DIR}/uploader"
    poetry run python uploader/main.py "${CUJ_DIR}/runner/results/latest"
    cd -
}

if [ -d "${CUJ_DIR}/runner/results.previous" ]; then
    rm -rf "${CUJ_DIR}/runner/results.previous"
fi
if [ -d "${CUJ_DIR}/runner/results" ]; then
    mv "${CUJ_DIR}/runner/results" "${CUJ_DIR}/runner/results.previous"
fi

clean_git "${CUJ_DIR}/runner"

cd "${CUJ_DIR}/runner"
poetry env use 3.11
poetry install
cd -

cd "${CUJ_DIR}/uploader"
poetry env use 3.11
poetry install
cd -

adb kill-server
adb disconnect

for adb_device in ${ADB_DEVICES[@]}; do
    adb connect $adb_device
    adb -s $adb_device reboot
    sleep 120
    adb connect $adb_device

    run_and_upload adb:${adb_device}
done

for chromeos_device in ${CHROMEOS_DEVICES[@]}; do
    ssh $chromeos_device reboot
    sleep 120

    run_and_upload ${chromeos_device}
done

sleep 120
