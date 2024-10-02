import requests
from lxml import etree
from bs4 import BeautifulSoup
import json

def buildnewsfeed():
    # URL of the RSS feed
    rss_url = 'https://www.republicworld.com/rss/india.xml'

    # Fetch the RSS feed content
    response = requests.get(rss_url)
    rss_content = response.content

    # Parse the RSS feed using lxml
    root = etree.fromstring(rss_content)

    # Function to extract the summary from CDATA content
    def extract_summary_from_cdata(cdata_content):
        soup = BeautifulSoup(cdata_content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ""
        if paragraphs:
            for para in paragraphs:
                text = text + para.get_text().strip()
                return text
        return 'Summary not available'

    # Iterate through the RSS feed items
    items = root.xpath('//item')
    articles = []
    i = 0
    for item in items:
        i += 1
        if i > 50:
            break
        title = item.findtext('title')
        link = item.findtext('link')
        pub_date = item.findtext('pubDate')
        description = item.findtext('description')

        content_encoded_element = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        content_encoded = content_encoded_element.text if content_encoded_element is not None else description

        summary = extract_summary_from_cdata(content_encoded)

        image = item.xpath('media:thumbnail/@url', namespaces={"media": "http://search.yahoo.com/mrss/"})
        image_url = image[0] if image else ''

        articles.append({
            'title': title,
            'link': link,
            'pubDate': pub_date,
            'summary': summary,
            'image': image_url
        })

    return articles
#print(buildnewsfeed())