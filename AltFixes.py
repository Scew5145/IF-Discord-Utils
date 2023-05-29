import argparse
import os
import re
import shutil

# This file was written by Sneed#7433 on discord, credit goes to them :D
parser = argparse.ArgumentParser(prog="KiwiScript", description="Script to check that all files in a folder match Infinite Fusion's naming convention by Sneed#7433")
parser.add_argument("-d","--dir", action="store", required=True)
args = parser.parse_args()
directory = args.dir
errorDir = os.path.join(directory, "_BADNAMES")
problemCounter = 0


def bad_name(file):
    shutil.move(os.path.join(directory, file), os.path.join(errorDir, file))


def in_range(number):
    if 1 <= number <= 420:
        return True
    return False


if not os.path.isdir(directory):
    exit("Given path is not a directory or doesn't exist")

dirCorrect = ""
while not dirCorrect == "Y":
    dirCorrect = input(f'Is directory {directory} correct? [Y/n]\n')
    if dirCorrect == "n" or dirCorrect == "N":
        exit("Exiting")

for sprite in os.listdir(directory):

    if not os.path.isfile(os.path.join(directory, sprite)):
        continue

    if len(re.findall("[0-9]{1,3}\.[0-9]{1,3}[a-z]{0,1}.png", sprite)) < 1:
        if not os.path.isdir(errorDir):
            os.mkdir(errorDir)
        problemCounter += 1
        bad_name(sprite)
        continue

    split = sprite.split(".")
    head = int(split[0])
    body = 0
    if split[1].isdigit():
        body = int(split[1])
    else:
        body = int(split[1][:-1])

    if not in_range(head) or not in_range(body):
        problemCounter +=1
        bad_name(sprite)
        continue

print(f'Script found issues with {problemCounter} files and moved them to directory {errorDir}')