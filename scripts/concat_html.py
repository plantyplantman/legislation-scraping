import os
import re
from bs4 import BeautifulSoup


def concatenate_html_files(dir_path):
    # define the regex pattern for s#.html and sch-#.html
    s_pattern = re.compile(r'^s(\d+)([a-zA-Z]*)\.html$')
    sch_pattern = re.compile(r'^sch-(\d+)([a-zA-Z]*)\.html$')

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
                    # create a BeautifulSoup object
                    soup = BeautifulSoup(infile, 'html.parser')
                    article_tag = soup.find('article')  # find the article tag
                    if article_tag:
                        # write the contents of the article tag to outfile
                        outfile.write(str(article_tag))


if __name__ == '__main__':
    concatenate_html_files(
        '/Users/home/projects/selenium-py/ACT-LEGISLATION_HTML copy')
