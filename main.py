from kijiji_scrapper import KijijiUrlIterator, ApartmentsPageIterator

url = 'https://www.kijiji.ca/b-appartement-condo/ville-de-montreal/c37l1700281'
pages = KijijiUrlIterator(url)
print(pages.page, pages.max_page)

for page in pages:
    print(page)

page = ApartmentsPageIterator(url)
for item in page:
    print(item.price)
print(page.rss_url)
print()
