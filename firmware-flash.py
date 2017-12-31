#/usr/bin/python3
# Tested on BQ Aquaris U. Please check the partitions before trying to
# flash an other device

import requests
import json
import subprocess
import os
import sys
import hashlib

from bs4 import BeautifulSoup
from archive import extract


def reboot_bootloader():
    print("I: Rebooting device to bootloader")
    subprocess.call(["adb", "reboot", "bootloader"])


def get_serialnum():
    print("I: Finding serial number")
    # Extract serial number from fastboot
    serialno = subprocess.check_output(
        ['fastboot', 'getvar', 'serialno'], stderr=subprocess.STDOUT) \
        .decode("utf-8").split(": ")[1].split("\n")[0]

    return serialno


def querry():
    print("I: Querrying database")
    # Request firmware download url from BQ API
    apiurl = "http://devices.bq.com/api/getHardReset/" + get_serialnum()

    global firmware
    firmware = json.loads(requests.get(apiurl).content)

    # Find md5sum on official download page
    supporturl = "https://www.bq.com/de/support/" + firmware["product"].replace("_", "-") + "/support-sheet"

    global md5sum
    md5sumsoup = BeautifulSoup(requests.get(supporturl).content.decode(), "html.parser")
    md5sum = md5sumsoup.find(href=firmware["url"]).parent.find_all("span")[1].string.split(": ")[1]

    print("I: Firmware found at " + firmware["url"])
    global firmware_target_folder
    global firmware_target_name

    firmware_target_folder = "firmware_" + \
        firmware["product"] + "_" + firmware["version"]
    firmware_target_name = "firmware_" + \
        firmware["product"] + "_" + firmware["version"] + ".zip"


def download():
    try:
        subprocess.call(["wget", "--continue", firmware["url"], "-O", firmware_target_name])
    except BaseException:
        print("Could not download the firmware")
        raise
        sys.exit(1)


def verify():
    if not hashlib.md5(open(firmware_target_name, 'rb').read()).hexdigest() == md5sum:
        print("E: The download failed, file is corrupted")
        sys.exit[1]
    else:
        print("I: Firmware checksum matches and it can be flashed")


def extract_firmware():
    print("I: Extracting firmware")
    if not os.path.isdir(firmware_target_folder):
        os.mkdir("firmware_" + firmware["product"] + "_" + firmware["version"])
        extract(firmware_target_name, firmware_target_folder)


def flash(partition, image):
    subprocess.call(["fastboot", "flash", partition, image])


def flash_fast():
    print("I: flashing system and boot")

    flash("boot", firmware_target_folder + "/boot.img")
    flash("system", firmware_target_folder + "/system.img")


def flash_full():
    flash("boot", firmware_target_folder + "/boot.img")
    flash("system", firmware_target_folder + "/system.img")
    flash("tz", firmware_target_folder + "/tz.mbn")
    flash("tzbak", firmware_target_folder + "tz.mbn")
    flash("sbl1", firmware_target_folder + "sbl1.mbn")
    flash("sbl1bak", firmware_target_folder + "sbl1.mbn")
    flash("rpm", firmware_target_folder + "rpm.mbn")
    flash("rpmbak", firmware_target_folder + "rpm.mbn")
    flash("mdtp", firmware_target_folder + "mdtp.img")
    flash("aboot", firmware_target_folder + "emmc_appsboot.mbn")
    flash("abootbak", firmware_target_folder + "emmc_appsboot.mbn")
    flash("devcfg", firmware_target_folder + "devcfg.mbn")
    flash("devcfgbak", firmware_target_folder + "devcfg.mbn")
    flash("keymaster", firmware_target_folder + "keymaster.mbn")
    flash("keymasterbak", firmware_target_folder + "keymaster.mbn")
    flash("cmnkib", firmware_target_folder + "cmnlib.mbn")
    flash("cmnlibbak", firmware_target_folder + "cmnlib.mbn")
    flash("cmnkib64", firmware_target_folder + "cmnlib64.mbn")
    flash("cmnkib64bak", firmware_target_folder + "cmnlib64.mbn")


def reboot_system():
    subprocess.call(["fastboot", "reboot"])


reboot_bootloader()
querry()
download()
verify()
extract_firmware()
print("WARN: Do not disconnect the device now or it will end up with no firmware installed!")
flash_fast()
reboot_system()
