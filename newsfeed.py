import requests
from lxml import etree
from bs4 import BeautifulSoup

def buildnewsfeed():
    # Times of India India News RSS Feed
    rss_url = 'https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms'

    # Fetch the RSS feed content
    response = requests.get(rss_url)
    rss_content = response.content

    # Parse the RSS feed using lxml
    root = etree.fromstring(rss_content)

    # Function to extract plain text from CDATA/HTML content
    def extract_summary_from_cdata(cdata_content):
        soup = BeautifulSoup(cdata_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text if text else 'Summary not available'

    # Extract items
    items = root.xpath('//item')
    articles = []
    for i, item in enumerate(items[:50]):
        title = item.findtext('title')
        link = item.findtext('link')
        pub_date = item.findtext('pubDate')
        description = item.findtext('description')

        # Clean up description (usually in CDATA with tags)
        summary = extract_summary_from_cdata(description)

        # TOI RSS feeds don’t have images in media:thumbnail, so we'll skip image unless extracted from description
        image_url = ''
        soup = BeautifulSoup(description, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            image_url = img['src']

        articles.append({
            'title': title,
            'link': link,
            'pubDate': pub_date,
            'summary': summary,
            'image': image_url
        })

    return articles

# Example usage:
# articles = buildnewsfeed()
# for art in articles[:5]: print(art['title'], art['link'])
