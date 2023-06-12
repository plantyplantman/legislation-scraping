import shutil
from collections import defaultdict
import os
import logging
import re
import os
import json
import urllib.parse
from bs4 import BeautifulSoup
import uuid

# setup the logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# set the log file
log_file = "logs/indexing_legislation.log"
handler = logging.FileHandler(log_file)
logger.addHandler(handler)


# UTILS
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


def copy_directory(source, destination):
    try:
        shutil.copytree(source, destination)
        print(f"Directory copied from {source} to {destination}")
    except shutil.Error as e:
        print(f"Directory copy failed: {e}")
    except OSError as e:
        print(f"Directory copy failed: {e}")


def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"The file '{file_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred while deleting the file '{file_path}': {e}")


def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"The folder '{folder_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"Folder '{folder_path}' not found.")
    except Exception as e:
        print(
            f"An error occurred while deleting the folder '{folder_path}': {e}")

# END UTILS


# Parser
def should_include_postfix(file_name, doc_type):
    if doc_type == 'SECTION':
        # Returns the number of capital letters following the section number
        post_num_pattern = r'SECT\s\d+([A-Z]+)'
        post_num_match = re.search(post_num_pattern, file_name)
        return len(post_num_match.group(1)) if post_num_match else 0
    elif doc_type == 'SCHEDULE':
        # Returns the number of capital letters following the schedule number
        post_num_pattern = r'SCHEDULE\s(\d+)([A-Z]+)'
        post_num_match = re.search(post_num_pattern, file_name)
        return len(post_num_match.group(2)) if post_num_match else 0


def extract_section_details(file_name, directory_name):
    base_url = "https://storage.googleapis.com/law-docs/ACT-LEGISLATION_HTML"

    # match section pattern
    sect_pattern = r'SECT\s(\d+)([A-Z]*)(.*)([\d\.]*)\.html$'
    sect_match = re.search(sect_pattern, file_name)

    if sect_match:
        sect_num = 's' + sect_match.group(1)
        postfix = sect_match.group(2)
        num_of_capital_letters = should_include_postfix(file_name, 'SECTION')
        if postfix and num_of_capital_letters > 1:
            sect_num += postfix[:num_of_capital_letters - 1].lower()
            sect_name = postfix[-1]+sect_match.group(3)
        else:
            sect_name = sect_match.group(2) + sect_match.group(3)
        sect_url = f"{base_url}/{urllib.parse.quote(directory_name)}/{urllib.parse.quote(sect_num)}.html"
        return sect_num, sect_name, sect_url, None

    # match schedule pattern
    schedule_pattern = r'SCHEDULE (\d+)([A-Z]*)\.html$'
    schedule_match = re.search(schedule_pattern, file_name)

    if schedule_match:
        sched_num = 'sch-' + schedule_match.group(1)
        postfix = schedule_match.group(2)
        num_of_capital_letters = should_include_postfix(file_name, 'SCHEDULE')
        if postfix and num_of_capital_letters > 1:
            sched_num += postfix[:num_of_capital_letters - 1].lower()
            sched_name = 'SCHEDULE ' + schedule_match.group(1) + postfix[-1]
        else:
            sched_num += postfix.lower()
            sched_name = 'SCHEDULE ' + schedule_match.group(1) + postfix
        sched_url = f"{base_url}/{urllib.parse.quote(directory_name)}/{urllib.parse.quote(sched_num)}.html"
        return sched_num, sched_name, sched_url, None
    else:
        schedule_pattern = r'SCHEDULE\.html$'
        schedule_match = re.search(schedule_pattern, file_name)
        if schedule_match:
            sched_num = 'sch-0'
            sched_name = 'SCHEDULE'
            sched_url = f"{base_url}/{urllib.parse.quote(directory_name)}/{urllib.parse.quote(sched_num)}.html"
            return sched_num, sched_name, sched_url, None
        else:
            schedule_pattern = r'SCHEDULE\s(.*)\.html$'
            schedule_match = re.search(schedule_pattern, file_name)
            if schedule_match:
                sched_num = 'sch-' + schedule_match.group(1)
                sched_name = 'SCHEDULE ' + schedule_match.group(1)
                sched_url = f"{base_url}/{urllib.parse.quote(directory_name)}/{urllib.parse.quote(sched_num)}.html"
                return sched_num, sched_name, sched_url, None

    # match longtitle pattern
    longtitle_pattern = r'LONG TITLE\.html$'
    longtitle_match = re.search(longtitle_pattern, file_name)

    if longtitle_match:
        sect_url = f"{base_url}/{urllib.parse.quote(directory_name)}/LONG%20TITLE.html"
        # return "LONG TITLE" instead of '0'
        return "LONG TITLE", 'LONG TITLE', sect_url, None

    # match notes pattern
    notes_pattern = r'NOTES\.html$'
    notes_match = re.search(notes_pattern, file_name)

    if notes_match:
        sect_url = f"{base_url}/{urllib.parse.quote(directory_name)}/NOTES.html"
        return "NOTES", 'NOTES', sect_url, None

    if not any([sect_match, schedule_match, longtitle_match, notes_match]):
        logger.error(f'Unmatched file: {file_name}')
        return None, None, None, file_name


def get_index_url(directory_name):
    base_url = "https://storage.googleapis.com/law-docs/2023-05-27__ACT-LEGISLATION_HTML"

    index_url = f"{base_url}/{urllib.parse.quote(directory_name)}/index.html"
    return index_url


def get_combined_url(directory_name):
    base_url = "https://storage.googleapis.com/law-docs/2023-05-27__ACT-LEGISLATION_HTML"

    combined_url = f"{base_url}/{urllib.parse.quote(directory_name)}/combined.html"
    return combined_url


def rename_files_in_directory(directory):
    legislation_name = os.path.basename(directory)
    year_match = re.search(r'\d{4}$', legislation_name)
    if year_match:
        year = year_match.group(0)
    else:
        logger.error(f"Could not get year for {legislation_name}")
        year = None
    sections = []
    unmatched_files = []
    for file in os.listdir(directory):
        f = os.path.splitext(file)[0]
        if f == legislation_name:
            os.rename(os.path.join(directory, file),
                      os.path.join(directory, "index.html"))
            sections.append({
                "id": str(uuid.uuid4()),
                "name": "index",
                "section_order": "index",
                "url": get_index_url(legislation_name)
            })
        else:
            sect_num, sect_name, sect_url, unmatched_file = extract_section_details(
                file, legislation_name)
            if sect_num is not None and sect_name is not None:
                new_file_name = f"{sect_num}.html"

                os.rename(os.path.join(directory, file),
                          os.path.join(directory, new_file_name))

                if sect_num.startswith('sch'):  # split the schedule num
                    _, section_order = sect_num.split('-')
                elif sect_num.startswith('s'):  # split the section num
                    _, section_order = sect_num[0], sect_num[1:]
                else:  # for "LONG TITLE" and "NOTES"
                    section_order = sect_num

                sections.append({
                    "id": str(uuid.uuid4()),
                    "name": sect_name,
                    "section_order": section_order,
                    "url": sect_url
                })
            elif unmatched_file:
                unmatched_files.append(unmatched_file)
            else:
                logger.error(f"Could not extract section details for {file}")
    return {"id": str(uuid.uuid4()),
            "name": legislation_name,
            "year": year,
            "sections": sections,
            "jurisdiction": "ACT",
            "unmatched_files": unmatched_files,
            "index_url": get_index_url(legislation_name),
            "combined_url": get_combined_url(legislation_name)}


def create_legislation_json(directory):
    legislation_details = rename_files_in_directory(directory)
    return legislation_details


def process_all_directories(main_directory):
    all_legislations = []
    missing_sections = {}
    original_file_counts = {}

    for directory in os.listdir(main_directory):
        directory_path = os.path.join(main_directory, directory)
        if os.path.isdir(directory_path):
            original_file_counts[directory] = len(os.listdir(directory_path))

    # Process directories and count sections in JSON
    for directory in os.listdir(main_directory):
        directory_path = os.path.join(main_directory, directory)
        if os.path.isdir(directory_path):
            legislation_dict = create_legislation_json(directory_path)
            section_count = len(legislation_dict["sections"])
            unmatched_files = legislation_dict["unmatched_files"]

            if original_file_counts[directory] != section_count:
                missing_sections[directory] = unmatched_files

            all_legislations.append(legislation_dict)

    with open(os.path.join(main_directory, 'legislations.json'), 'w') as f:
        json.dump(all_legislations, f, indent=2)

    return missing_sections

# END Parser

# Validation


def check_unique_urls(path):
    # Open the json file
    with open(path) as json_file:
        json_data = json.load(json_file)

    url_set = set()

    # List to store duplicate sections
    duplicate_sections = []

    # Iterate through each legislation
    for legislation in json_data:

        # Iterate through each section in the legislation
        for section in legislation['sections']:

            # Get the URL of the section
            url = section.get('url', None)

            if url:
                # If URL is already in the set, it's not unique, add it to duplicate_sections
                if url in url_set:
                    print(section)
                    duplicate_sections.append(section)
                else:
                    # If URL is not in the set, add it to the set
                    url_set.add(url)
    dst_path = os.path.join(os.path.dirname(path), "duplicate_sections.json")

    # Write duplicate sections to a JSON file
    with open(dst_path, 'w') as outfile:
        json.dump(duplicate_sections, outfile, indent=4)


def group_sections_by_url(file_path):
    # Load the data from the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Use a defaultdict to easily group data by section_url
    grouped_data = defaultdict(list)

    # Iterate over each section in data
    for section in data:
        # Append the section to the list of sections for the corresponding section_url
        grouped_data[section["url"]].append(section)

    # Convert back to a regular dict for serialization
    grouped_data = dict(grouped_data)

    # Write the grouped data back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(grouped_data, file, indent=4)


def count_sections(data):
    count = 0
    for legislation in data:
        for section in legislation['sections']:
            count += 1
    return count


def count_files(directory):
    count = 0
    for root, _, files in os.walk(directory):
        count += len(files)
    return count


def count_folders(directory):
    count = 0
    for _, dirnames, _ in os.walk(directory):
        count += len(dirnames)
    return count


def check_sum(target_path, source_path):
    with open(os.path.join(target_path, "legislations.json")) as json_file:
        json_data = json.load(json_file)

    num_legislation_source = count_folders(source_path)
    num_legislation_target = count_folders(target_path)
    num_legislation_json = len(json_data)
    if num_legislation_json == num_legislation_source == num_legislation_target:
        print(GREEN+"Legislation count check passed!" + RESET)
        print(f"    Number of folders source: {num_legislation_source}")
        print(f"    Number of folders target: {num_legislation_target}")
        print(f"    Number of legislations json: {num_legislation_json}")
    else:
        print(RED+"Legislation count check failed!" + RESET)
        print(f"    Number of folders source: {num_legislation_source}")
        print(f"    Number of folders target: {num_legislation_target}")
        print(f"    Number of legislations json: {num_legislation_json}")

    num_files_source = count_files(source_path)
    num_files_target = count_files(target_path)
    num_sections_json = count_sections(json_data)
    if num_sections_json == num_files_source == num_files_target:
        print(GREEN+"Section count check passed!" + RESET)
        print(f"    Number of files source: {num_files_source}")
        print(f"    Number of files target: {num_files_target}")
        print(f"    Number of sections json: {num_sections_json}")
    else:
        print(RED+"Section count check failed!" + RESET)
        print(f"    Number of files source: {num_files_source}")
        print(f"    Number of files target: {num_files_target}")
        print(f"    Number of sections json: {num_sections_json}")

        print(
            RED+f"MISSING {num_files_source - num_files_target} SECTIONS IN TARGET" + RESET)
        print(
            RED+f"MISSING {num_files_source - num_sections_json} SECTIONS IN JSON" + RESET)

# END Validation

# Cleaning


def remove_links(root_dir):
    for legislation_folder in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, legislation_folder)
        if os.path.isdir(folder_path):
            for html_file in os.listdir(folder_path):
                if html_file != 'index.html':
                    html_file_path = os.path.join(folder_path, html_file)
                    with open(html_file_path, 'r', errors='ignore') as f:  # ignore decode errors
                        html = f.read()
                        soup = BeautifulSoup(html, 'html.parser')

                        for a in soup.find_all('a'):
                            # Replace the 'a' tag with its text content
                            a.replace_with(a.text)

                    # Re-encode the file in UTF-8 while writing
                    with open(html_file_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))


def edit_json(filename):
    # Load JSON
    with open(filename, 'r') as f:
        data = json.load(f)

    # Order mapping
    order_mapping = {'index': 1, 'long_name': 2,
                     'section': 3, 'schedule': 4, 'notes': 5}

    # Edit JSON
    for legislation in data:
        for section in legislation['sections']:
            # Determine category
            if section['name'].lower() == 'index':
                category = 'index'
            elif section['name'].lower() == 'long title':
                category = 'long_name'
            elif section['name'].lower().startswith('schedule'):
                category = 'schedule'
            elif section['name'].lower() == 'notes':
                category = 'notes'
            else:
                category = 'section'

            # Assign order value
            section['order_value'] = order_mapping[category]

            # Split section_order into prefix and suffix parts
            match = re.match(r"([0-9]+)([a-z]*)",
                             section['section_order'], re.I)
            if match:
                items = match.groups()
            else:
                items = (section['section_order'],)
            section['section_order_prefix'] = items[0]
            section['section_order_suffix'] = items[1] if len(
                items) > 1 else ''

    # Save JSON
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def remove_string_from_files(root_directory, file_name, string_to_remove):
    for directory_path, directory_names, file_names in os.walk(root_directory):
        if file_name in file_names:
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = file.read()
            data = data.replace(string_to_remove, "")
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(data)

# End Cleaning


# Create mega HTML file


def concatenate_html_files(dir_path):
    # define the regex pattern for s#.html and sch-#.html
    s_pattern = re.compile(r'^s(\d+)([a-zA-Z]*)\.html$')
    sch_pattern = re.compile(r'^sch-(\d+)([a-zA-Z]*)\.html$')

    with open(os.path.join(dir_path, 'legislations.json'), 'r') as f:
        data = json.load(f)

    for root, dirs, files in os.walk(dir_path):
        # sort all the html files
        html_files = sorted(f for f in files if f.endswith('.html'))

        ordered_files = []
        if 'LONG TITLE.html' in html_files:
            ordered_files.append('LONG TITLE.html')
            html_files.remove('LONG TITLE.html')

        s_files = sorted((f for f in html_files if s_pattern.match(f)),
                         key=lambda x: (int(s_pattern.match(x).group(1)), s_pattern.match(x).group(2)))
        ordered_files.extend(s_files)

        sch_files = sorted((f for f in html_files if sch_pattern.match(f)),
                           key=lambda x: (int(sch_pattern.match(x).group(1)), sch_pattern.match(x).group(2)))
        ordered_files.extend(sch_files)

        if 'NOTES.html' in html_files:
            ordered_files.append('NOTES.html')

        # combine all html files into one
        with open(os.path.join(root, 'combined.html'), 'w') as outfile:
            for fname in ordered_files:
                with open(os.path.join(root, fname)) as infile:
                    outfile.write(infile.read())


def modify_html_tags(directory):
    # Walk the directory
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.html'):
                filepath = os.path.join(dirpath, filename)

                # Open and read the file
                with open(filepath, 'r') as file:
                    html_content = file.read()

                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Find all h3 tags and remove them
                for h3_tag in soup.find_all('h3'):
                    h3_tag.decompose()

                # Find all h1 tags and change them to h2
                for h1_tag in soup.find_all('h1'):
                    h1_tag.name = 'h2'

                # Write the modified HTML back to the file
                with open(filepath, 'w') as file:
                    file.write(str(soup))


if __name__ == "__main__":
    main_directory = "COPY_ACT-LEGISLATION_HTML"
    source_directory = "docs/2023-05-18__ACT-LEGISLATION_HTML"
    delete_folder(main_directory)
    copy_directory(source_directory, main_directory)

    missing = process_all_directories(main_directory)
    check_unique_urls(main_directory+"/legislations.json")
    check_sum(main_directory, source_directory)

    print(RED+f"MISSING: {missing}" + RESET)

    # group_sections_by_url(main_directory+"/legislations.json")

    print("Removing links...")
    remove_links(main_directory)

    print("Editing JSON...")
    edit_json(main_directory+"/legislations.json")

    print("Removing unnecessary line breaks from files...")
    LB_ONE = '<p><br/><br/><font size="2"></font><font size="1"></font><br/><br/><font size="1">\n</font><br/><br/><font size="1"> </font><br/><br/><font size="1">\n</font><br/><br/></p>'
    LB_TWO = '<p><br/><br/><font size="2"></font><font size="1"></font><br/><br/><font size="1">\n</font><br/><br/><font size="1"> </font><br/><br/><font size="1"> </font></p><p align="right"></p>'
    LB_THREE = '<p><br/><br/><font size="2"></font><font size="1"></font><br/><br/><font size="1"></font><br/><br/><font size="1"> </font><br/><br/><font size="1"></font><br/><br/><br/><br/></p>'
    remove_string_from_files(main_directory, "index.html", LB_ONE)
    remove_string_from_files(main_directory, "index.html", LB_TWO)
    remove_string_from_files(main_directory, "index.html", LB_THREE)

    print("Concatenating HTML files...")
    concatenate_html_files(main_directory)

    print("Modifying HTML tags...")
    modify_html_tags(main_directory)
