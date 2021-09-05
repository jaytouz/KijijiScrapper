import re
import requests
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver


class KijijiUrlIterator:
    """Iterator of pages url based on a starting search result from kijiji"""

    def __init__(self, starting_url, max_page=1000):
        self.url = starting_url
        self.page = self.find_page(self.url)
        self.format_first_page_url()
        self.max_page = self.find_max_page(max_page=max_page)

    def format_first_page_url(self):
        """Adds /page-1/ inside the url if not present"""
        url_att = self.url.split('/')
        if url_att[-2] != 'page-1':
            url_att.insert(-1, 'page-1')
            self.url = '/'.join(url_att)

    def find_max_page(self, max_page: int) -> int:
        """
        Finds the max page in a search result. Calls the url of the search result with a big page number.
        Kijiji automatically reset to the max page if the number is to high. If Kijiji doesn't change the url, max_page
        is to small and it's not the real max_page.

        Parameters
        ----------
        max_page : int
            Page number to call in the search result. Should be high to trigger Kijiji callback function to reset to
            the actual last search page.
        Returns
        -------
        actual_max_page : int
            highest number of page in the search results found with kijiji callback

        """
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome('chromedriver/chromedriver.exe', options=options)
        max_page_url = re.sub('/(page-\w+)/', f'/page-{max_page}/', self.url)
        driver.get(max_page_url)
        actual_max_page = self.find_page(driver.current_url)
        driver.close()
        return actual_max_page

    @staticmethod
    def find_page(url):
        """
        find the page number in the url

        Returns
        -------
        page_num : int
            page number in url, if no pattern is found, it's the first page.
        """
        pattern = '/(page-\w+)/'  # looking for .../page-(any_number)/...
        page_att = re.findall(pattern, url)
        if page_att:
            # extract page number
            page_num_str = page_att[0].split('page-')[-1]
            page_num =  int(page_num_str)
        else:
            page_num =  0
        return page_num

    def __iter__(self):
        self.page = 0
        return self

    def __next__(self):
        if self.page < self.max_page:
            if self.page == 0:
                pass
            else:
                self.url = self.url.replace(f'page-{self.page}', f'page-{self.page + 1}')
            self.page += 1
            return self.url
        else:
            # reset to first page
            self.url = self.url.replace(f'page-{self.page}', f'page-{1}')
            self.page = 0
            raise StopIteration


class ApartmentsPageIterator:
    """Iterator of apartment for a search page"""

    def __init__(self, url):
        self.url = url
        self.idx = 0
        self.items = self.parse_items()

    def __len__(self):
        return len(self.items)

    def parse_items(self):
        """
        Finds all item in the rss-srp version of the page's url. An item is an html class containing all the
        ad's info.

        Returns
        -------
        items : list
            list of html item containing all the ad's info.
        """
        html_page = requests.get(self.rss_url)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        items = soup.findAll('item')
        return items

    @property
    def rss_url(self):
        """Get's the rss-srp url version. It seems to be an xml version of the page."""
        rss_url = self.url.replace('kijiji.ca/b-', 'kijiji.ca/rss-srp-')
        return rss_url

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx < len(self):
            item = self.items[self.idx]
            self.idx += 1
            return ApartmentItem(item)
        else:
            # reset
            self.idx = 0
            raise StopIteration


class ApartmentItem:
    """Apartment item found on a search page result. This class contains all the accessor to the relevant data"""

    def __init__(self, item_class, full_data=True):
        """

        Parameters
        ----------
        item_class : str
            str of html containing data from the ad snippet in a search result.
        full_data : bool
            If true, will use the link to access data not accessible from the snippet and only from the ad's url. False
            will limit to the data found in the snippet.
        """
        self.item_class = item_class
        self.full_data = full_data
        if full_data:
            html_page = requests.get(self.link)
            self.app_soup = BeautifulSoup(html_page.text, 'html.parser')

    @property
    def title(self):
        """Ad title"""
        title = self.item_class.find('title').text
        return title

    @property
    def link(self):
        """Url to the ad"""
        link = self.item_class.find('link').text
        if not link:
            link = self.item_class.find('guid').text
        return link

    @property
    def description(self):
        """Ad's description"""
        description = self.item_class.find('description').text
        return description

    @property
    def enclosure(self):
        """Image information in the snippet"""
        enclosure = self.item_class.find('enclosure').text
        return enclosure

    @property
    def img_url(self):
        """Image's url"""
        img_url = self.enclosure['url']
        return img_url

    @property
    def img_type(self):
        """Image type """
        img_type = self.enclosure['type']
        return img_type

    @property
    def pub_date(self) -> datetime:
        """Published date of the ad"""
        date_str = self.item_class.find('pubdate').text
        datetime_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
        return datetime_obj

    @property
    def guid(self):
        """Id, was found to be the url of the ad"""
        guid = self.item_class.find('guid').text
        return guid

    @property
    def geo_lat(self):
        """Latitude of the apartment ad"""
        geo_lat = self.item_class.find('geo:lat').text
        return float(geo_lat)

    @property
    def geo_long(self):
        """Longitude of the apartment ad"""
        geo_long = self.item_class.find('geo:long').text
        return float(geo_long)

    @property
    def price(self):
        """Monthly price for the rent"""
        price = self.item_class.find('g-core:price').text
        return price

    @property
    def size(self):
        """Apartment size"""
        if self.full_data:
            size_txt = self.app_soup.findAll('span', {"class": 'noLabelValue-3861810455'})[1].text  # 'Pièces: size'
            size = size_txt.split(': ')[-1]
            return size
        else:
            return np.nan

    @property
    def number_of_bathroom(self):
        """Number of bathroom in the apartment"""
        if self.full_data:
            size_txt = self.app_soup.findAll('span', {"class": 'noLabelValue-3861810455'})[
                2].text  # 'Salles de bain: size'
            size = size_txt.split(': ')[-1]
            return size
        else:
            return np.nan
