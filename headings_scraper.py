import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_h1_headings(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Crawl in-domain pages and report H1 issues: missing, multiple, long (>70), duplicate.

    CSV columns per row:
    - H1 Text
    - Page URL
    - Length
    - Is Missing (1/0)
    - Is Multiple (1/0)
    - Is Long (>70) (1/0)
    - Is Duplicate (1/0)
    - Row Issue (1/0)
    """

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]

        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-h1-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        # In-memory storage to determine duplicates at the end
        rows = []  # each: (h_text, url, length, is_missing, is_multiple, is_long)
        text_to_urls = {}

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'H1 Text', 'Page URL', 'Length',
                'Is Missing', 'Is Multiple', 'Is Long (>70)', 'Is Duplicate', 'Row Issue'
            ])

            visited_urls = set()
            discovered_urls = set()
            total_discovered = 0
            visited_count = 0

            # summary counters
            total_pages = 0
            missing_count = 0
            multiple_count = 0
            long_count = 0

            def scrape_page(url):
                nonlocal total_discovered, visited_count, total_pages, missing_count, multiple_count, long_count

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

                total_pages += 1

                # Extract H1s
                h1_tags = soup.find_all('h1')
                h_texts = [t.get_text(strip=True) for t in h1_tags if t.get_text(strip=True)]

                is_missing_page = (len(h_texts) == 0)
                is_multiple_page = 1 if len(h_texts) > 1 else 0

                if is_missing_page:
                    missing_count += 1
                    # Add a placeholder row for missing
                    rows.append(('No H1', url, 0, 1, 0, 0))
                else:
                    if is_multiple_page:
                        multiple_count += 1
                    for txt in h_texts:
                        length = len(txt)
                        is_long = 1 if length > 70 else 0
                        if is_long:
                            long_count += 1
                        key = txt.lower()
                        text_to_urls.setdefault(key, []).append(url)
                        rows.append((txt, url, length, 0, is_multiple_page, is_long))

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
            for k, urls in text_to_urls.items():
                if k and len(urls) > 1:
                    for u in urls:
                        duplicate_urls.add(u)
            duplicate_count = 0

            # Write rows with duplicate info and row_issue
            for h_text, url, length, is_missing, is_multiple, is_long in rows:
                # "No H1" placeholder should not be considered duplicate
                is_dup = 0 if is_missing else (1 if url in duplicate_urls else 0)
                if is_dup:
                    duplicate_count += 1
                row_issue = 1 if (is_missing or is_multiple or is_long or is_dup) else 0
                csv_writer.writerow([h_text, url, length, is_missing, is_multiple, is_long, is_dup, row_issue])

            # Summary rows
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Pages Missing H1:', missing_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Pages with Multiple H1:', multiple_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - H1 > 70:', long_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Duplicate H1 Rows:', duplicate_count, '', '', '', ''])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nH1 scan complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"H1 scan complete! Results saved to {filepath}")

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


def scrape_h2_headings(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Crawl in-domain pages and report H2 issues: missing, multiple, long (>70), duplicate.

    CSV columns per row:
    - H2 Text
    - Page URL
    - Length
    - Is Missing (1/0)
    - Is Multiple (1/0)
    - Is Long (>70) (1/0)
    - Is Duplicate (1/0)
    - Row Issue (1/0)
    """

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]

        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-h2-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        rows = []  # each: (h_text, url, length, is_missing, is_multiple, is_long)
        text_to_urls = {}

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'H2 Text', 'Page URL', 'Length',
                'Is Missing', 'Is Multiple', 'Is Long (>70)', 'Is Duplicate', 'Row Issue'
            ])

            visited_urls = set()
            discovered_urls = set()
            total_discovered = 0
            visited_count = 0

            # summary counters
            total_pages = 0
            missing_count = 0
            multiple_pages_count = 0
            long_count = 0

            def scrape_page(url):
                nonlocal total_discovered, visited_count, total_pages, missing_count, multiple_pages_count, long_count

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

                total_pages += 1

                # Extract H2s
                h2_tags = soup.find_all('h2')
                h_texts = [t.get_text(strip=True) for t in h2_tags if t.get_text(strip=True)]

                is_missing_page = (len(h_texts) == 0)
                is_multiple_page = 1 if len(h_texts) > 1 else 0

                if is_missing_page:
                    missing_count += 1
                    rows.append(('No H2', url, 0, 1, 0, 0))
                else:
                    if is_multiple_page:
                        multiple_pages_count += 1
                    for txt in h_texts:
                        length = len(txt)
                        is_long = 1 if length > 70 else 0
                        if is_long:
                            long_count += 1
                        key = txt.lower()
                        text_to_urls.setdefault(key, []).append(url)
                        rows.append((txt, url, length, 0, is_multiple_page, is_long))

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
            for k, urls in text_to_urls.items():
                if k and len(urls) > 1:
                    for u in urls:
                        duplicate_urls.add(u)
            duplicate_count = 0

            # Write rows with duplicate info and row_issue
            for h_text, url, length, is_missing, is_multiple, is_long in rows:
                is_dup = 0 if is_missing else (1 if url in duplicate_urls else 0)
                if is_dup:
                    duplicate_count += 1
                row_issue = 1 if (is_missing or is_multiple or is_long or is_dup) else 0
                csv_writer.writerow([h_text, url, length, is_missing, is_multiple, is_long, is_dup, row_issue])

            # Summary rows
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Pages Missing H2:', missing_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Pages with Multiple H2:', multiple_pages_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - H2 > 70:', long_count, '', '', '', ''])
            csv_writer.writerow(['', '', 'Summary - Duplicate H2 Rows:', duplicate_count, '', '', '', ''])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nH2 scan complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"H2 scan complete! Results saved to {filepath}")

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
