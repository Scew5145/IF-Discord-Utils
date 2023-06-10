from pathlib import Path
import re
import json
import filecmp

# The goal of this is to diff two sets of folders of custombattlers images and output a list of collisions as
# a txt file. Anything beyond that should likely go elsewhere

regex_valid_names = "(0|[1-9][0-9]{0,2})\\.(0|[1-9][0-9]{0,2})[a-z]?\\.png"


def export_collisions(target_folder, source_folder, output_filename):
    target_indexed = index_folder(target_folder)  # , debug_output_file="F:/InfiniteFusion/target.json")
    source_indexed = index_folder(source_folder)  # , debug_output_file="F:/InfiniteFusion/source.json")
    # Source should be the "new" files - basically the ones that we might need polls for
    collisions = {}
    for key in source_indexed:
        if key == "BAD_FILES":
            continue
        if key in target_indexed:
            source_raw = [str(Path(source_folder, file).absolute()) for file in source_indexed[key]["filenames"]]
            target_raw = [str(Path(target_folder, file).absolute()) for file in target_indexed[key]["filenames"]]
            source_dupechecked = check_for_duplicates(target_raw, source_raw)
            if len(source_dupechecked):
                collisions[key] = {
                    "new_count": source_indexed[key]["count"],
                    "old_count": target_indexed[key]["count"],
                    "new_files": source_dupechecked,
                    "old_files": target_raw
            }
    with open(output_filename, 'w') as output_file:
        json.dump(collisions, output_file, indent=4)
    return


def check_for_duplicates(target, source):
    dupes = set()
    for target_filename in target:
        for source_filename in source:
            if filecmp.cmp(target_filename, source_filename):
                dupes.add(source_filename)
    for dupe in dupes:
        source.remove(dupe)
    return source


def index_folder(input_folder, debug_output_file=""):
    bad_files = set()
    name_pattern = re.compile(regex_valid_names)
    input_indexed = {}  # stored as (head_id, body_id) : {all the data}
    input_path = Path(input_folder)
    for target_file in input_path.glob("*.png"):
        if name_pattern.fullmatch(target_file.name):
            split_name = target_file.stem.split(".")
            if len(split_name) == 2:  # trim a,b,c, etc. - this can be more efficient but meh
                split_name[1] = ''.join(c for c in split_name[1] if c.isdigit())
            indexed_name = '.'.join(split_name)
            if indexed_name in input_indexed:
                input_indexed[indexed_name]["count"] += 1
                input_indexed[indexed_name]["filenames"].append(target_file.name)
            else:
                input_indexed[indexed_name] = {
                    "count": 1,
                    "filenames": [target_file.name]
                }
        else:
            bad_files.add(target_file)
    input_indexed["BAD_FILES"] = [file.name for file in bad_files]
    # meant to be writable straight to json - good for debugging and stuff
    if debug_output_file != "":
        with open(debug_output_file, 'w') as output_file:
            json.dump(input_indexed, output_file, indent=4)
    return input_indexed


if __name__ == '__main__':
    export_collisions("F:/InfiniteFusion/Full Sprite pack 1-89 (April 2023)/Full Sprite pack 1-89 (April 2023)/CustomBattlers",
                      "F:/InfiniteFusion/voted/output/to swap", "F:/InfiniteFusion/collision_text.json")


