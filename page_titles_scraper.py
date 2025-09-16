import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_page_titles(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Crawl in-domain pages and report title issues: missing, short (<30), long (>60), duplicate.

    CSV columns per row:
    - Page Title
    - Page URL
    - Title Length
    - Is Missing (1/0)
    - Is Short (1/0)
    - Is Long (1/0)
    - Is Duplicate (1/0)
    - Row Issue (1/0)
    """

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]

        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-page-titles-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        # In-memory storage to determine duplicates at the end
        rows = []  # each: (title, url, length, is_missing, is_short, is_long)
        title_to_urls = {}

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'Page Title', 'Page URL', 'Title Length',
                'Is Missing', 'Is Short', 'Is Long', 'Is Duplicate', 'Row Issue'
            ])

            visited_urls = set()
            discovered_urls = set()

            # progress counters
            total_discovered = 0
            visited_count = 0

            # summary counters
            total_pages = 0
            missing_count = 0
            short_count = 0
            long_count = 0

            def scrape_page(url):
                nonlocal total_discovered, visited_count, total_pages, missing_count, short_count, long_count

                if stop_scraping():
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
                    output_text.see('end')
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
                output_text.see('end')

                # Count this page
                total_pages += 1

                # Extract title
                title_tag = soup.find('title')
                title = title_tag.text.strip() if title_tag and title_tag.text else ''
                length = len(title)
                is_missing = 1 if not title else 0
                is_short = 1 if (not is_missing and length < 30) else 0
                is_long = 1 if (not is_missing and length > 60) else 0

                # Track for duplicates
                key = title.lower() if title else ''
                title_to_urls.setdefault(key, []).append(url)
                rows.append((title, url, length, is_missing, is_short, is_long))

                # Update simple counters
                if is_missing:
                    missing_count += 1
                if is_short:
                    short_count += 1
                if is_long:
                    long_count += 1

                # Discover in-domain links
                for link in soup.find_all('a', href=True):
                    if stop_scraping():
                        return
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

                # Mark this page visited for progress (after discovery phase)
                visited_count += 1
                if on_progress:
                    try:
                        on_progress(visited_count, max(total_discovered, 1))
                    except Exception:
                        pass

            # Seed discovered with base URL and start
            base_norm = normalize_url(base_url)
            discovered_urls.add(base_norm)
            total_discovered = 1
            if on_progress:
                try:
                    on_progress(0, total_discovered)
                except Exception:
                    pass
            scrape_page(base_norm)

            # Compute duplicates
            duplicate_urls = set()
            for k, urls in title_to_urls.items():
                if k and len(urls) > 1:
                    for u in urls:
                        duplicate_urls.add(u)
            duplicate_count = 0

            # Write rows with duplicate info and row_issue
            for title, url, length, is_missing, is_short, is_long in rows:
                is_duplicate = 1 if url in duplicate_urls else 0
                if is_duplicate:
                    duplicate_count += 1
                row_issue = 1 if (is_missing or is_short or is_long or is_duplicate) else 0
                csv_writer.writerow([title or 'No title', url, length, is_missing, is_short, is_long, is_duplicate, row_issue])

            # Summary rows
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Missing Titles:', missing_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Short Titles (<30):', short_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Long Titles (>60):', long_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Duplicate Title Pages:', duplicate_count, '', '', '', ''])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nPage Titles scan complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"Page Titles scan complete! Results saved to {filepath}")

    def wrapped_process():
        try:
            scrape_process()
        finally:
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    thread = threading.Thread(target=wrapped_process, daemon=True)
    thread.start()
