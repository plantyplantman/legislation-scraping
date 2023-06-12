import json
import shutil
import re
import os


def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
        print(f"File copied from {source} to {destination}")
    except shutil.Error as e:
        print(f"File copy failed: {e}")
    except OSError as e:
        print(f"File copy failed: {e}")


def main():
    # Load the data from the file
    with open('ACT-LEGISLATION_HTML/legislations.json', 'r') as f:
        data = json.load(f)

    total_legislations = len(data)
    i = 1
    for legislation in data:
        legislation['index_url'] = re.sub(
            r'2023-05-27__', '', legislation['index_url'])
        legislation['combined_url'] = re.sub(
            r'2023-05-27__', '', legislation['combined_url'])
        print("processed {}/{}".format(i, total_legislations))
        i += 1

    # Write the modified data back to the file
    with open('ACT-LEGISLATION_HTML/legislations.json', 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    if not os.path.exists('ACT-LEGISLATION_HTML/legislations.json.bak'):
        copy_file('ACT-LEGISLATION_HTML/legislations.json',
                  'ACT-LEGISLATION_HTML/legislations.json.bak')

    main()
