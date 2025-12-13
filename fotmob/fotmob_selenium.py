import os
import time
import logging
import warnings
import random

# Suppress only the pkg_resources deprecation warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"pkg_resources is deprecated as an API"
)

# Reduce noise from selenium-wire logs
logging.getLogger("seleniumwire").setLevel(logging.WARNING)
logging.getLogger("selenium.webdriver").setLevel(logging.WARNING)

from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

WAIT_PAGE_LOAD = 20
WAIT_CAPTURE_REQUESTS = 10
MATCHES_SECTION_SELECTOR = "div[class*='LeagueMatchesByDates']"
MATCH_LINK_SELECTOR = "a[class*='MatchWrapper']"

class FotmobSelenium:
    def __init__(self):
        self.profile_path = os.getenv('FOTMOB_SELENIUM_PROFILE_PATH')
        self.matches_url = os.getenv('FOTMOB_SELENIUM_MATCHES_URL')

        if not self.profile_path:
            raise ValueError("FOTMOB_SELENIUM_PROFILE_PATH environment variable is required")
        if not self.matches_url:
            raise ValueError("FOTMOB_SELENIUM_MATCHES_URL environment variable is required")

        logging.debug(f"Using Firefox profile: {self.profile_path}")

        self.options = Options()
        self.options.add_argument("-headless")
        self.options.profile = self.profile_path
        self.options.profile.set_preference("devtools.jsonview.enabled", False)

    def get_api_data(self, url):
        data = None

        try:
            with webdriver.Firefox(options=self.options) as driver:
                driver.set_page_load_timeout(WAIT_PAGE_LOAD)

                driver.get(url)

                wait = WebDriverWait(driver, WAIT_PAGE_LOAD)

                data = wait.until(
                    lambda d: (
                        text := d.execute_script(
                            "return document.documentElement.textContent"
                        )
                    ) and text.strip()
                )
        except TimeoutException as e:
            logging.error(f"API timeout: {e}")
        except Exception as e:
            logging.exception(f"Error in get_api_data: {e}")

        return data


    def get_api_token(self):
        token = None

        try:
            with webdriver.Firefox(options=self.options) as driver:
                driver.set_page_load_timeout(WAIT_PAGE_LOAD)

                logging.info(f"==> Navigating to Fotmob matches URL: {self.matches_url}")
                driver.get(self.matches_url)

                wait = WebDriverWait(driver, WAIT_PAGE_LOAD)
                matches_section = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, MATCHES_SECTION_SELECTOR))
                )
                logging.info("<== Fotmob matches page received")

                match_links = matches_section.find_elements(By.CSS_SELECTOR, MATCH_LINK_SELECTOR)
                if not match_links:
                    logging.error("No match links found on matches URL")
                    return None

                delay = random.uniform(3, 8)
                logging.debug(f"Waiting {delay:.2f} seconds before navigating to match URL")
                time.sleep(delay)

                match_url = match_links[0].get_attribute("href")
                logging.info(f"==> Navigating to Fotmob match URL: {match_url}")
                driver.get(match_url)

                logging.info(f"    Waiting {WAIT_CAPTURE_REQUESTS}s for background requests to be captured...")
                time.sleep(WAIT_CAPTURE_REQUESTS)
                logging.info("<== Fotmob match details page received")

                match_request = next(
                    (req for req in driver.requests if req.response and '/api/data/matchDetails' in req.url),
                    None
                )

                if match_request:
                    token = match_request.headers.get('x-mas')
                    if not token:
                        logging.error("'x-mas' header not found in match details request")
                else:
                    logging.error("Match details request not found in captured requests")
                    logging.debug("Captured requests: %s",
                                  [req.url for req in driver.requests if req.response])
        except TimeoutException as e:
            logging.error(f"Timeout loading page or waiting for elements: {e}")
        except Exception as e:
            logging.exception(f"Error in get_api_token: {e}")

        return token
