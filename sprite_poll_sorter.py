import json
import random
import re
from os.path import join, exists, basename
import shutil
import glob
import filecmp
import requests
import time

sprite_path = "F:/InfiniteFusion/voted"
keep_path = sprite_path + "/to keep as is"
swap_path = sprite_path + "/to swap"
# "F:/InfiniteFusion/MainSpritesVotingExports/392023Export.json"
input_channel_json = "F:/InfiniteFusion/MainSpritesVotingExports/06042023Export.json"
start_id = "1094654399588085830"

temp_folder = "F:/InfiniteFusion/voted/_temp"

old_name_regex = re.compile('\\d+\\.\\d+(old)?\\.png', re.IGNORECASE)


def sort_polls():
    json_file = open(input_channel_json, encoding='utf-8')
    channel_export = json.load(json_file)
    found_start = False
    looking_for_winner = False
    images = []
    buffer_count = 0
    for message in channel_export['messages']:
        if message['id'] == start_id:
            print('Starting Sort')
            found_start = True
        if not found_start:
            continue
        if not looking_for_winner:
            print(f"parsing: {message['id']} {message['content']}")
            if len(message['attachments']) < 2:
                print(f"skipping, not enough images to be a poll set {message['id']}")
                continue
            images = []
            for attachment in message['attachments']:
                name_start = attachment['url'].rfind('/')
                if attachment['url'].endswith("empty.png"):
                    continue
                image_name = join(sprite_path, attachment['url'][name_start + 1:])
                images.append(image_name)
                print(image_name)
            sortable_poll = True
            entries_to_remove = []
            for i in range(len(images)):
                image = images[i]
                if not exists(image):
                    buffer_count += 1
                    if buffer_count == 50:
                        print("buffering for a bit to slow down requests")
                        buffer_count = 0
                        time.sleep(float(random.randrange(0, 5)))
                    temp_image_name = find_file_from_source(message['attachments'][i]['url'])
                    if temp_image_name == "":
                        print(f"Missing {image}, skipping poll")
                        sortable_poll = False
                        break
                    images[i] = temp_image_name

            if sortable_poll:
                looking_for_winner = True
        else:
            # If we got here, THIS message should be the poll results. If we fail to parse it's because
            # something is formatted incorrectly, or there's something broken with the script
            if len(message['embeds']) != 1:
                print("SOMETHING BAD HAPPENED, CAN'T PARSE POLL RESULTS")
                return
            results = message['embeds'][0]['description']
            parse_start = results.find("**Final Result**") + 17
            parse_end = results.rfind("users voted")
            string_to_parse = results[parse_start:parse_end]
            string_to_parse = string_to_parse[:string_to_parse.rfind(']') + 1]
            lines = string_to_parse.split('\n')
            if len(lines) != len(images):
                print("Different number of images from number of vote categories! wtf!")
                print(f"Vote Category count: {len(lines)} Image Count: {len(images)}")
                return
            vote_max = (-1, 0)
            for i in range(0, len(lines)):
                number_start = lines[i].rfind('[') + 1
                number_end = lines[i].find(' ', number_start)
                count = int(lines[i][number_start:number_end])
                print(count)
                if count > vote_max[1]:
                    vote_max = (i, count)
            print(f"Winner: {images[vote_max[0]]}")
            winner_basename = basename(images[vote_max[0]])
            if not old_name_regex.match(winner_basename):
                for image in images:
                    image_basename = basename(image)
                    if old_name_regex.match(image_basename):
                        pass
                        shutil.move(image, swap_path + '/' + basename(image))
                    elif image_basename == winner_basename:
                        pass
                        shutil.move(image, swap_path + '/' + basename(image))
                    else:
                        pass
                        shutil.move(image, keep_path + '/' + basename(image))
            else:
                for image in images:
                    image_basename = basename(image)
                    shutil.move(image, keep_path + '/' + basename(image))

            looking_for_winner = False

    if not found_start:
        print(f"Something bad happened, because we couldn't find the first message @ {start_id}. What gives?")


def find_file_from_source(source_image):
    r = requests.get(source_image, allow_redirects=True)
    temp_image = temp_folder + "/" + basename(source_image)
    if not exists(temp_image):
        # return ""
        # comment out this early return to try to get the file from discord
        print("Downloading image...")
        open(temp_image, 'wb').write(r.content)
    for file in glob.glob(sprite_path + "/*.png"):
        if filecmp.cmp(file, temp_image):
            print(f"Found match! {file}")
            return file
    return ""


if __name__ == '__main__':
    # print(filecmp.cmp("F:/InfiniteFusion/voted/96.294a.png", "F:/InfiniteFusion/voted/_temp/96.294.png"))
    sort_polls()

