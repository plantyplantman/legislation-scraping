from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List


def scrape_austlii(urls: List[str]) -> List[str]:
    """
    Scrape a list of AustLII pages and save the results to files

    args:
    urls: a list of urls to scrape

    returns:
    a list of the scraped articles

    """
    driver = webdriver.Chrome()
    res = []
    for url in urls:
        res.append(scrape_austlii_url(url, driver))
    return res


def scrape_austlii_url(url: str, driver: webdriver.Chrome) -> str:
    """Scrape a single AustLII page and save the result to a file"""
    driver.get(url)
    article = driver.find_elements(By.TAG_NAME, 'article')
    article = article[0].text

    # Extract the title from the first line of the article text
    title = article.split('\n')[0]

    # Replace any characters in title that are not suitable for filenames
    title = "".join(c for c in title if c.isalnum()
                    or c in [' ', '.']).rstrip()

    with open("docs/austlii" + title + ".txt", "w") as f:
        f.write(article)
    return article


if __name__ == "__main__":
    print(scrape_austlii(
        ["http://www.austlii.edu.au/cgi-bin/viewdb/au/legis/act/consol_act/cma2007232/"]))
