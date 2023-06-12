from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os


# Parse args
# parser = argparse.ArgumentParser(description='Scrape legislation.gov.au')
# parser.add_argument('start', type=int, help='The index of the first document to download')
# Create a directory to store the downloaded files

urls = [
    "https://www.legislation.gov.au/Browse/Results/ByTitle/Acts/InForce/A/0/2/principal",
    "https://www.legislation.gov.au/Browse/Results/ByTitle/Acts/InForce/A/0/3/principal",
    "https://www.legislation.gov.au/Browse/Results/ByTitle/Acts/InForce/A/0/4/principal",
]

if not os.path.exists("./docs"):
    os.makedirs("./docs")

# Set up the webdriver. This assumes you're using Chrome; adjust as necessary.
driver = webdriver.Chrome("chromedriver")

# Open the webpage
driver.get(
    "https://www.legislation.gov.au/Browse/Results/ByTitle/Acts/InForce/A/0/2/principal"
)

# Wait until the page has fully loaded
wait = WebDriverWait(driver, 10)

# Get all download buttons
download_buttons = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, "//input[@value='Download']"))
)

# Iterate over each button
for i in range(len(download_buttons)):
    # Need to find the buttons again because the DOM might have changed
    download_buttons = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//input[@value='Download']"))
    )

    # Click the button
    download_buttons[i].click()

    # Find the "Text" link and click it
    text_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Text')]"))
    )
    text_link.click()

    # Get the page source and parse it with Beautiful Soup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find the div with class "right" and print its inner HTML
    right_div = soup.find("div", {"class": "right"})
    title = driver.title
    url = driver.current_url

    # Write the HTML to a file
    with open(f"./docs/doc{i+101}.txt", "w") as f:
        f.write(f"{title}\n{url}\n{right_div}")

    # Go back to the original page
    driver.back()
    driver.back()

    # Wait for a bit to make sure the page is fully loaded before the next iteration
    time.sleep(3)


# Close the browser
driver.quit()
