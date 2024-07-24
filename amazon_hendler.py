import time

from amazoncaptcha import AmazonCaptcha
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from sheetAPI import SheetAPI

chrome_binary = (
    "binaries/your_path_to_chrome_driver"
) # TODO: Change to your chrome driver path


class AmazonScraper:
    def __init__(self, chrome_binary_path, sheet_id_read, sheet_id_write):
        self.chrome_binary_path = chrome_binary_path
        self.sheet_read = SheetAPI(sheet_id_read)
        self.sheet_write = SheetAPI(sheet_id_write)
        self.driver = None

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.binary_location = self.chrome_binary_path
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )

    def handle_captcha(self):
        try:
            link = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='a-row a-text-center']//img")
                    )
                )
                .get_attribute("src")
            )

            captcha = AmazonCaptcha.fromlink(link)
            captcha_value = captcha.solve()

            input_captcha = self.driver.find_element(By.ID, "captchacharacters")
            input_captcha.send_keys(captcha_value)

            continue_shopping_button = self.driver.find_element(
                By.CLASS_NAME, "a-button-text"
            )
            continue_shopping_button.click()
        except (NoSuchElementException, TimeoutException):

            print("No captcha found, proceeding with delivery change.")

    def change_delivery_zip_code(self, zip_code):
        delivery_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "nav-global-location-slot"))
        )
        delivery_button.click()

        zip_code_input = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.ID, "GLUXZipUpdateInput"))
        )
        zip_code_input.send_keys(zip_code)

        apply_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "GLUXZipUpdate"))
        )
        apply_button.click()
        self.driver.refresh()
        print("Zip code changed")

    def search_and_scrape(self, query):
        all_results = []
        for search_term in query:
            search_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".nav-search-field input")
                )
            )
            search_field.clear()
            search_field.send_keys(search_term)
            search_field.send_keys("\ue007")

            sold_items = []
            for index in range(10):
                search_results = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "h2.a-size-mini a.a-link-normal")
                    )
                )
                if index >= len(search_results):
                    break

                element_to_click = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "h2.a-size-mini a.a-link-normal")
                    )
                )
                element_to_click.click()

                back_steps = 1
                try:
                    sold_button = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                "div#dynamic-aod-ingress-box a.a-link-normal",
                            )
                        )
                    )
                    time.sleep(5)
                    sold_button.click()
                    back_steps = 2

                    try:
                        seller_elements = WebDriverWait(self.driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, '//div[@id="aod-offer-soldBy"]')
                            )
                        )

                        for element in seller_elements[2:]:
                            a_tag = element.find_element(
                                By.XPATH, './/a[@class="a-size-small a-link-normal"]'
                            )
                            store_name = a_tag.text
                            link = a_tag.get_attribute("href")
                            sold_items.append({store_name: link})

                            print(f"Store Name: {store_name}, Link: {link}")
                    except TimeoutException:

                        print("Seller elements not found.")
                        back_steps = 1
                except TimeoutException:

                    print("Sold button not found, skipping.")
                    back_steps = 1

                for _ in range(back_steps):
                    self.driver.back()

            all_results.extend(sold_items)

        return all_results

    def run(self, query, zip_code="11235"):
        self.setup_driver()
        self.driver.get("https://www.amazon.com")
        self.handle_captcha()
        self.change_delivery_zip_code(zip_code)
        data = self.search_and_scrape(query)
        self.driver.quit()

        return data

    def execute(self):
        query = self.sheet_read.read("Sheet1", column=1)
        data = self.run(query)
        self.sheet_write.write("Sheet1", "A2", data)


if __name__ == "__main__":
    scraper = AmazonScraper(
        chrome_binary_path=chrome_binary,
        sheet_id_read="1C3ZVJbKMq5Xyj94_q-XRv30AQpiPlq2gwUhV3IaCX-A",
        sheet_id_write="1sOwAUpYDJ68ZUulLo173LnC_WKyA7NNwi9A5Pee0bHk",
    )
    scraper.execute()
