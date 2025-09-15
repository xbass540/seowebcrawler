import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_404_errors(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Scrapes website for 404 errors and exports to CSV."""

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]

        random_number = random.randint(1000, 9999)
        filename = f'{base_url[8:]}-404-errors-{random_number}.csv'
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Post Name', 'Post URL', 'Not Found', 'Posts with Issues'])

            visited_urls = set()
            discovered_urls = set()
            # 404-specific counters
            total_pages = 0
            article_counter, issues_counter = 1, 0
            # progress counters
            total_discovered = 0
            visited_count = 0

            def scrape_page(url):
                nonlocal article_counter, issues_counter, total_pages, visited_count, total_discovered, discovered_urls

                url = normalize_url(url)
                if stop_scraping():   # check stop flag
                    return

                if url in visited_urls:
                    return
                visited_urls.add(url)
                total_pages += 1

                try:
                    response = requests.get(url)
                    if response.status_code == 404:
                        csv_writer.writerow([f"Article {article_counter}", url, "404 Not Found", issues_counter])
                        issues_counter += 1
                        output_text.insert(tk.END, f"404 Not Found: {url}\n")
                        output_text.see("end")
                        # count this as visited and update progress before returning
                        visited_count += 1
                        if on_progress:
                            try:
                                on_progress(visited_count, max(total_discovered, 1))
                            except Exception:
                                pass
                        return
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    output_text.insert(tk.END, f"Failed to fetch {url}: {e}\n")
                    output_text.see("end")
                    # count this as visited and update progress on error
                    visited_count += 1
                    if on_progress:
                        try:
                            on_progress(visited_count, max(total_discovered, 1))
                        except Exception:
                            pass
                    return

                # ✅ Progress update for valid pages
                output_text.insert(tk.END, f"Scraping URL: {url}\n")
                output_text.see("end")

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.find('title').text.strip() if soup.find('title') else "No title"
                csv_writer.writerow([page_title, url, "Page Found", issues_counter])
                article_counter += 1

                for link in soup.find_all('a', href=True):
                    if stop_scraping():   # double-check stop flag
                        return
                    full_url = normalize_url(urljoin(base_url, link['href']))
                    base_root = normalize_url(base_url)
                    if base_root in full_url:
                        # track discovered for determinate progress
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

            # seed discovered with base url
            base_norm = normalize_url(base_url)
            discovered_urls.add(base_norm)
            total_discovered = 1
            if on_progress:
                try:
                    on_progress(0, total_discovered)
                except Exception:
                    pass
            scrape_page(base_norm)
            csv_writer.writerow(['', '', 'Total Pages with Issues:', issues_counter])
            # Additional 404-specific summary rows (do not change columns)
            csv_writer.writerow(['', '', 'Summary - Total Pages Crawled:', total_pages])
            csv_writer.writerow(['', '', 'Summary - Pages with 404:', issues_counter])
            csv_writer.writerow(['', '', 'Summary - Pages OK:', max(total_pages - issues_counter, 0)])
            # finalize progress at 100%
            if on_progress:
                try:
                    on_progress(visited_count, max(total_discovered, 1))
                except Exception:
                    pass

        # ✅ Print only once at the end
        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nScraping complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"Scraping complete! Results saved to {filepath}")

    def wrapped_process():
        try:
            scrape_process()
        finally:
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    # Run in background thread
    thread = threading.Thread(target=wrapped_process, daemon=True)
    thread.start()
