import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_meta_descriptions(base_url, output_folder, output_text, stop_scraping, update_stop_flag):
    """Scrapes website for missing meta descriptions and exports to CSV."""

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]
        nonlocal stop_scraping
        random_number = random.randint(1000, 9999)
        filename = f'{base_url[8:]}-meta-descriptions-{random_number}.csv'
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Post Name', 'Post URL', 'Meta Description', 'Posts with Issues'])

            visited_urls = set()
            # Meta-specific counters
            total_pages = 0                  # pages crawled
            pages_missing_meta = 0           # pages where page-level og:description missing
            pages_with_meta = 0              # pages where og:description present
            total_article_rows = 0           # number of article rows written
            article_rows_missing_meta = 0    # article rows with "No description"
            article_counter, issues_counter = 1, 0

            def scrape_page(url):
                nonlocal article_counter, issues_counter, stop_scraping, total_pages, pages_missing_meta, pages_with_meta, total_article_rows, article_rows_missing_meta

                if stop_scraping():
                    output_text.insert(tk.END, "Scraping stopped by user.\n")
                    return
                url = normalize_url(url)
                if url in visited_urls:
                    return
                visited_urls.add(url)

                try:
                    response = requests.get(url)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    output_text.insert(tk.END, f"Failed to fetch {url}: {e}\n")
                    return

                soup = BeautifulSoup(response.text, 'html.parser')
                output_text.insert(tk.END, f"Scraping URL: {url}\n")

                # Count this page
                total_pages += 1
                meta_tag = soup.find('meta', property="og:description")
                meta_desc = meta_tag['content'].strip() if meta_tag and meta_tag.get('content') else "No description"

                if meta_desc == "No description":
                    issues_counter += 1
                    pages_missing_meta += 1
                else:
                    pages_with_meta += 1

                for article in soup.find_all('article'):
                    if stop_scraping():
                        output_text.insert(tk.END, "Scraping stopped by user.\n")
                        return
                    headline = article.find('h2').text.strip() if article.find('h2') else "No headline"
                    link_tag = article.find('a', href=True)
                    if link_tag:
                        full_url = urljoin(base_url, link_tag['href'])
                        csv_writer.writerow([headline, full_url, meta_desc, issues_counter])
                        total_article_rows += 1
                        if meta_desc == "No description":
                            article_rows_missing_meta += 1
                        output_text.insert(tk.END, f"# {article_counter}: {headline}\n URL: {full_url}\n Meta: {meta_desc}\n\n")
                        article_counter += 1

                for link in soup.find_all('a', href=True):
                    full_url = normalize_url(urljoin(base_url, link['href']))
                    base_root = normalize_url(base_url)
                    if base_root in full_url:
                        scrape_page(full_url)

            scrape_page(normalize_url(base_url))
            csv_writer.writerow(['', '', 'Total Posts with Issues:', issues_counter])
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages])
            csv_writer.writerow(['', '', 'Summary - Pages Missing Meta:', pages_missing_meta])
            csv_writer.writerow(['', '', 'Summary - Pages With Meta:', pages_with_meta])
            csv_writer.writerow(['', '', 'Summary - Total Article Rows:', total_article_rows])
            csv_writer.writerow(['', '', 'Summary - Article Rows Missing Meta:', article_rows_missing_meta])

        output_text.insert(tk.END, f"\nScraping complete. Results saved to {filepath}\n")
        messagebox.showinfo("Success", f"Scraping complete! Results saved to {filepath}")

    thread = threading.Thread(target=scrape_process, daemon=True)
    thread.start()
