import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_meta_descriptions(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
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
            discovered_urls = set()
            # progress counters
            total_discovered = 0
            visited_count = 0
            # Meta-specific counters
            total_pages = 0                  # pages crawled
            pages_missing_meta = 0           # pages where page-level og:description missing
            pages_with_meta = 0              # pages where og:description present
            total_article_rows = 0           # number of article rows written
            article_rows_missing_meta = 0    # article rows with "No description"
            article_counter, issues_counter = 1, 0

            def scrape_page(url):
                nonlocal article_counter, issues_counter, stop_scraping, total_pages, pages_missing_meta, pages_with_meta, total_article_rows, article_rows_missing_meta, visited_count, total_discovered, discovered_urls

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
                    # count this as visited and update progress on error
                    visited_count += 1
                    if on_progress:
                        try:
                            on_progress(visited_count, max(total_discovered, 1))
                        except Exception:
                            pass
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
                        if full_url not in discovered_urls and full_url not in visited_urls:
                            discovered_urls.add(full_url)
                            total_discovered += 1
                            if on_progress:
                                try:
                                    on_progress(visited_count, max(total_discovered, 1))
                                except Exception:
                                    pass
                        scrape_page(full_url)

                # after parsing and discovering links, mark this page as visited for progress
                visited_count += 1
                if on_progress:
                    try:
                        on_progress(visited_count, max(total_discovered, 1))
                    except Exception:
                        pass

            # seed discovered with base url and start
            base_norm = normalize_url(base_url)
            discovered_urls.add(base_norm)
            total_discovered = 1
            if on_progress:
                try:
                    on_progress(0, total_discovered)
                except Exception:
                    pass
            scrape_page(base_norm)
            csv_writer.writerow(['', '', 'Total Posts with Issues:', issues_counter])
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages])
            csv_writer.writerow(['', '', 'Summary - Pages Missing Meta:', pages_missing_meta])
            csv_writer.writerow(['', '', 'Summary - Pages With Meta:', pages_with_meta])
            csv_writer.writerow(['', '', 'Summary - Total Article Rows:', total_article_rows])
            csv_writer.writerow(['', '', 'Summary - Article Rows Missing Meta:', article_rows_missing_meta])

        output_text.insert(tk.END, f"\nScraping complete. Results saved to {filepath}\n")
        messagebox.showinfo("Success", f"Scraping complete! Results saved to {filepath}")
        if on_complete:
            try:
                on_complete()
            except Exception:
                pass

    def wrapped_process():
        try:
            scrape_process()
        finally:
            # In case the function returned early due to stop, ensure on_complete is called
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    thread = threading.Thread(target=wrapped_process, daemon=True)
    thread.start()
