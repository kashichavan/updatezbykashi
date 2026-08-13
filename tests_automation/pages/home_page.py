from selenium.webdriver.common.by import By
from .base_page import BasePage

class HomePage(BasePage):
    """
    Page Object for Kashii Updatez Homepage
    Contains locators and interaction methods for Hero section, Job Grid, YouTube Marquee, and Detail Modal.
    """
    # Locators
    HERO_TITLE = (By.ID, "typewriterText")
    CODE_TERMINAL = (By.CLASS_NAME, "coding-terminal")
    SEARCH_INPUT = (By.ID, "searchInput")
    JOB_CARDS = (By.CLASS_NAME, "catalog-card")
    TODAY_FILTER_BTN = (By.ID, "btnFilterToday")
    YOUTUBE_MARQUEE = (By.ID, "ytMarqueeTrack")
    
    # Detail Modal Locators
    DETAIL_MODAL = (By.ID, "detailModal")
    DETAIL_TITLE = (By.ID, "detailTitle")
    DETAIL_CLOSE_BTN = (By.ID, "btnCloseDetail")

    def __init__(self, driver, base_url="https://kashiiupdatez.online"):
        super().__init__(driver)
        self.base_url = base_url

    def load(self):
        self.open_url(self.base_url)

    def get_hero_title_text(self):
        return self.get_text(self.HERO_TITLE)

    def is_terminal_displayed(self):
        return self.is_displayed(self.CODE_TERMINAL)

    def search_jobs(self, query):
        self.type_text(self.SEARCH_INPUT, query)

    def get_job_cards_count(self):
        try:
            cards = self.find_elements(self.JOB_CARDS)
            return len(cards)
        except Exception:
            return 0

    def click_first_job_card(self):
        cards = self.find_elements(self.JOB_CARDS)
        if cards:
            cards[0].click()

    def is_detail_modal_open(self):
        return self.is_displayed(self.DETAIL_MODAL)

    def close_detail_modal(self):
        self.click(self.DETAIL_CLOSE_BTN)
