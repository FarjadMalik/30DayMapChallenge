import requests
import csv
import time
from bs4 import BeautifulSoup


def get_page(session, page_num: int, base_url: str = ""):
    """Fetch a given page number of events; returns BeautifulSoup of the page."""
    params = {"page": page_num}
    resp = session.get(base_url, params=params, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def parse_table(soup):
    """Parse the events table from a BeautifulSoup object and yield dicts per row."""
    rows = soup.select("table tr")[1:]  # skip header row
    for tr in rows:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        # as per table header: Date, Time (utc), Latitude, Longitude, Magnitude, Depth (km), Region, Mode, Map
        if len(cols) < 9:
            # skip incomplete row or footer
            continue
        yield {
            "Date": cols[0],
            "Time (utc)": cols[1],
            "Latitude": cols[2],
            "Longitude": cols[3],
            "Magnitude": cols[4],
            "Depth (km)": cols[5],
            "Region": cols[6],
            "Mode": cols[7],
            "Map": cols[8],
        }

def find_last_page(soup):
    """Find the maximum page number from pagination links in the page."""
    # Look for the “next page” nav, but better to scan all <a> in pagination for the highest number
    page_links = soup.select("a[href*='page=']")
    max_page = 1
    for a in page_links:
        href = a.get("href")
        if href:
            # extract query param page=
            try:
                part = href.split("page=")[-1]
                num = int(part.split("&")[0])
                if num > max_page:
                    max_page = num
            except ValueError:
                pass
    return max_page

def scrape_all(output_csv: str, base_url: str = ""):
    with requests.Session() as session:
        # optional headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Python scraper for NSMC events; +https://yourdomain.example)"
        })

        # determine how many pages
        first_soup = get_page(session, 1, base_url)
        last_page = find_last_page(first_soup)
        print(f"Detected {last_page} pages of events.")

        # open CSV and write header
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Date","Time (utc)","Latitude","Longitude","Magnitude","Depth (km)","Region","Mode","Map"])
            writer.writeheader()

            # iterate each page
            for page in range(1, last_page + 1):
                print(f"Scraping page {page}/{last_page}")
                soup = get_page(session, page, base_url)
                for row in parse_table(soup):
                    writer.writerow(row)
                # polite pause
                time.sleep(0.5)
