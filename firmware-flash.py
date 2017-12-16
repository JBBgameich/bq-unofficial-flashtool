#/usr/bin/python3
# Tested on BQ Aquaris U. Please check the partitions before trying to
# flash an other device

import requests
import json
import subprocess
import os
import sys

from archive import extract


def reboot_bootloader():
    print("I: Rebooting device to bootloader")
    subprocess.call(["adb", "reboot", "bootloader"])


def get_serialnum():
    print("I: Finding serial number")
    # Extract serial number from fastboot
    _getvar_serialno = subprocess.check_output(
        ['fastboot', 'getvar', 'serialno'], stderr=subprocess.STDOUT)
    _serialno_string = _getvar_serialno.decode("utf-8")
    _serialno_string_split = _serialno_string.split(": ")
    serialno = _serialno_string_split[1].split("\n")
    return serialno[0]


def querry():
    print("I: Querrying database")
    # Request firmware download url from BQ API
    apiurl = "http://devices.bq.com/api/getHardReset/" + get_serialnum()
    apiresponse = requests.get(apiurl)

    global firmware
    firmware = json.loads(apiresponse.content)

    print("I: Firmware found at " + firmware["url"])
    global firmware_target_folder
    global firmware_target_name

    firmware_target_folder = "firmware_" + \
        firmware["product"] + "_" + firmware["version"]
    firmware_target_name = "firmware_" + \
        firmware["product"] + "_" + firmware["version"] + ".zip"


def download():
    if not os.path.isfile(firmware_target_name):
        try:
            with open(firmware_target_name, "wb") as f:
                response = requests.get(firmware["url"], stream=True)
                total_length = response.headers.get('content-length')

                print(
                    "Downloading %s" %
                    firmware_target_name +
                    " (" +
                    total_length +
                    " bytes)")

                if total_length is None:  # no content length header
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write("\r[%s%s]" %
                                         ('=' * done, ' ' * (50 - done)))
                        sys.stdout.flush()
                print()
        except BaseException:
            print("Could not download the firmware")
            raise


def extract_firmware():
    print("I: Extracting firmware")
    if not os.path.isdir(firmware_target_folder):
        os.mkdir("firmware_" + firmware["product"] + "_" + firmware["version"])
        extract(firmware_target_name, firmware_target_folder)


def flash(partition, image):
    subprocess.call(["fastboot", "flash", partition, image])


def flash_fast():
    print("I: flashing system and boot")
    print("WARN: Do not disconnect the device now or it will end up with no firmware installed!")

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
extract_firmware()
flash_fast()
reboot_system()
