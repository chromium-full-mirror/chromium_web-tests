#!/bin/bash

CROSSBENCH_DIR="/home/crossbench-lab/crossbench"
WEB_TESTS_DIR="/home/crossbench-lab/web-tests"
SECRETS_FILE="/home/crossbench-lab/secrets.hjson"

ADB_DEVICES=("[2401:fa00:480:ee08:c68e:cc14:2832:a1b6]:5555" "[2401:fa00:480:ee08:8672:515c:1107:42af]:5555")
CHROMEOS_DEVICES=("C244591" "C289107")

clean_git() {
    dir=$1

    echo "Cleaning git checkout $dir"

    cd $dir

    git reset --hard
    git checkout main
    git pull

    cd -
}

clean_git $CROSSBENCH_DIR
cd $CROSSBENCH_DIR
poetry install
cd -

clean_git $WEB_TESTS_DIR

adb kill-server
adb disconnect

for adb_device in ${ADB_DEVICES[@]}; do
    adb connect $adb_device
    adb -s $adb_device reboot
done

for chromeos_device in ${CHROMEOS_DEVICES[@]}; do
    ssh $chromeos_device reboot
done

sleep 120

for adb_device in ${ADB_DEVICES[@]}; do
    adb connect $adb_device
done

cd $WEB_TESTS_DIR/cuj/crossbench/runner

for target in $WEB_TESTS_DIR/cuj/crossbench/runner/targets/*; do
    poetry run python runner/main.py --device-id $(basename $target) --browser-config-file $target --secrets-config-file ~/secrets.hjson --crossbench $CROSSBENCH_DIR --web-tests $WEB_TESTS_DIR --upload
done
