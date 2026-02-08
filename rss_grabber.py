import argparse
import requests
from bs4 import BeautifulSoup
import urllib.parse

parser = argparse.ArgumentParser(description='RSS Grabber')
parser.add_argument('-i', '--input', type=str, help='File containing the URLs to parse', required=True)
parser.add_argument('-o', '--output', type=str, help='File to write the RSS links to', required=True)
args = parser.parse_args()

def main():
    all_rss_links = []
    with open(args.input, 'r') as f:
        urls = f.readlines()
    for url in urls:
        url = url.strip().strip('/')
        if url.startswith('//'):
            url = 'https:' + url
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching {url}: {e}. Skipping.")
            continue


        base_url = urllib.parse.urlparse(url).scheme + '://' + urllib.parse.urlparse(url).netloc

        soup = BeautifulSoup(response.text, 'lxml')
        rss_links = soup.find_all('link', rel='alternate')
        if len(rss_links) != 0:
            found_rss_link = urllib.parse.urljoin(base_url, rss_links[0]['href'])
            all_rss_links.append(found_rss_link)
            print(f"Found RSS link for {url}: {found_rss_link}")
            continue

        # Try to find RSS link by appending common suffixes to the website base URL
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        for suffix in [
            '/feed', '/feed/', '/rss', '/atom', '/feed.xml',
            '/index.atom', '/index.rss', '/index.xml', '/atom.xml', '/rss.xml',
            '/.rss', '/blog/index.xml', '/blog/index.rss', '/blog/feed.xml', '/blog/index.rss'
        ]:
            rss_link = base_url + suffix
            response = requests.get(rss_link)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                continue
            if response.status_code == 200:
                all_rss_links.append(rss_link)
                print(f"Found RSS link for {url}: {rss_link}")
                break

    with open(args.output, 'w') as f:
        for rss_link in all_rss_links:
            f.write(rss_link + '\n')

if __name__ == "__main__":
    main()
