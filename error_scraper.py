import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_404_errors(base_url, output_folder, output_text, stop_scraping, update_stop_flag):
    """Scrapes website for 404 errors and exports to CSV."""

    def scrape_process():
        nonlocal stop_scraping
        random_number = random.randint(1000, 9999)
        filename = f'{base_url[8:]}-404-errors-{random_number}.csv'
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Post Name', 'Post URL', 'Not Found', 'Posts with Issues'])

            visited_urls = set()
            article_counter, issues_counter = 1, 0

            def scrape_page(url):
                nonlocal article_counter, issues_counter, stop_scraping

                if stop_scraping():
                    output_text.insert(tk.END, "Scraping stopped by user.\n")
                    output_text.see("end")
                    return
                if url in visited_urls:
                    return
                visited_urls.add(url)

                try:
                    response = requests.get(url)
                    if response.status_code == 404:
                        csv_writer.writerow([f"Article {article_counter}", url, "404 Not Found", issues_counter])
                        issues_counter += 1
                        output_text.insert(tk.END, f"404 Not Found: {url}\n")
                        output_text.see("end")
                        return
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    output_text.insert(tk.END, f"Failed to fetch {url}: {e}\n")
                    output_text.see("end")
                    return

                # ✅ Add this: show progress for pages that are working
                output_text.insert(tk.END, f"Scraping URL: {url}\n")
                output_text.see("end")

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.find('title').text.strip() if soup.find('title') else "No title"
                csv_writer.writerow([page_title, url, "Page Found", issues_counter])
                article_counter += 1

                for link in soup.find_all('a', href=True):
                    full_url = urljoin(base_url, link['href'])
                    if base_url in full_url:
                        scrape_page(full_url)

            scrape_page(base_url)
            csv_writer.writerow(['', '', 'Total Pages with Issues:', issues_counter])

        output_text.insert(tk.END, f"\nScraping complete. Results saved to {filepath}\n")
        messagebox.showinfo("Success", f"Scraping complete! Results saved to {filepath}")

    thread = threading.Thread(target=scrape_process, daemon=True)
    thread.start()
