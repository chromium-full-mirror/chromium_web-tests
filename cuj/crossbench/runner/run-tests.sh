#!/bin/bash

CROSSBENCH_DIR="/home/crossbench-lab/crossbench"
WEB_TESTS_DIR="/home/crossbench-lab/web-tests"
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

    cd -
}

clean_git $CROSSBENCH_DIR
if [ -d "${CROSSBENCH_DIR}/results.previous" ]; then
    rm -rf "${CROSSBENCH_DIR}/results.previous"
fi
if [ -d "${CROSSBENCH_DIR}/results" ]; then
    mv "${CROSSBENCH_DIR}/results" "${CROSSBENCH_DIR}/results.previous"
fi
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

for i in $(seq 1 5); do
    for target in $WEB_TESTS_DIR/cuj/crossbench/runner/targets/*; do
        poetry run python runner/main.py --device-id $(basename $target) --browser-config-file $target --secrets-config-file ~/secrets.hjson --crossbench $CROSSBENCH_DIR --web-tests $WEB_TESTS_DIR --tests "[dgms][omehl][caei]*" --upload
    done
done