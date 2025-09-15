import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_security(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Scrapes the website to verify HTTPS usage, detect mixed content, and report security headers.

    Columns exported per row:
    - Page Title
    - Page URL
    - Protocol (HTTP/HTTPS)
    - Is HTTP Page (1/0)
    - Has Mixed Content (1/0)
    - Mixed Items Count
    - HSTS (Strict-Transport-Security)
    - CSP (Content-Security-Policy present? Yes/No)
    - X-Content-Type-Options (present? Yes/No)
    - X-Frame-Options (present? Yes/No)
    - Referrer-Policy (present? Yes/No)
    - Row Issue (1/0) -> 1 if HTTP page or mixed content present
    """

    def scrape_process():
        def normalize_url(u: str) -> str:
            return urldefrag(u)[0]

        def is_same_site(url_a: str, url_b: str) -> bool:
            try:
                a = urlparse(url_a)
                b = urlparse(url_b)
                return a.netloc == b.netloc
            except Exception:
                return False

        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-security-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'Page Title', 'Page URL', 'Protocol', 'Is HTTP Page', 'Has Mixed Content', 'Mixed Items Count',
                'HSTS', 'CSP', 'X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy', 'Row Issue'
            ])

            visited_urls = set()
            discovered_urls = set()
            total_issues_counter = 0
            # Page scheme counters
            total_pages = 0
            https_pages = 0
            http_pages = 0
            other_pages = 0
            # progress counters
            total_discovered = 0
            visited_count = 0

            def collect_resource_urls(soup: BeautifulSoup, page_url: str):
                resources = []
                # CSS
                for tag in soup.find_all('link', href=True):
                    rel = ' '.join(tag.get('rel', [])).lower()
                    if 'stylesheet' in rel or tag.get('as') == 'style':
                        resources.append(urljoin(page_url, tag['href']))
                # JS
                for tag in soup.find_all('script', src=True):
                    resources.append(urljoin(page_url, tag['src']))
                # Images/media
                for tag in soup.find_all(['img', 'audio', 'video', 'source', 'iframe'], src=True):
                    resources.append(urljoin(page_url, tag['src']))
                # Picture srcset (take each candidate URL)
                for tag in soup.find_all(['img', 'source']):
                    srcset = tag.get('srcset')
                    if srcset:
                        parts = [p.strip().split(' ')[0] for p in srcset.split(',') if p.strip()]
                        for p in parts:
                            resources.append(urljoin(page_url, p))
                return resources

            def check_mixed_content(page_url: str, resources: list) -> (bool, int):
                page_scheme = urlparse(page_url).scheme.lower()
                if page_scheme != 'https':
                    return False, 0  # mixed content is only relevant for https pages
                mixed_count = 0
                for r in resources:
                    try:
                        if urlparse(r).scheme.lower() == 'http':
                            mixed_count += 1
                    except Exception:
                        # ignore malformed resource URLs
                        continue
                return (mixed_count > 0), mixed_count

            def security_headers_summary(headers: dict) -> tuple:
                hsts = 'Yes' if headers.get('Strict-Transport-Security') else 'No'
                csp = 'Yes' if headers.get('Content-Security-Policy') else 'No'
                xcto = 'Yes' if headers.get('X-Content-Type-Options') else 'No'
                xfo = 'Yes' if headers.get('X-Frame-Options') else 'No'
                refpol = 'Yes' if headers.get('Referrer-Policy') else 'No'
                return hsts, csp, xcto, xfo, refpol

            def scrape_page(url):
                nonlocal total_issues_counter, total_pages, https_pages, http_pages, other_pages, total_discovered, visited_count, discovered_urls

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
                page_title = soup.find('title').text.strip() if soup.find('title') else 'No title'
                output_text.insert(tk.END, f"Scraping URL: {url}\n")
                output_text.see('end')

                # Protocol and page counters
                proto = urlparse(url).scheme.upper() or ''
                is_http_page = 1 if proto.lower() == 'http' else 0
                total_pages += 1
                if proto.lower() == 'https':
                    https_pages += 1
                elif proto.lower() == 'http':
                    http_pages += 1
                else:
                    other_pages += 1

                # Mixed content detection
                res_urls = collect_resource_urls(soup, url)
                has_mixed, mixed_count = check_mixed_content(url, res_urls)
                has_mixed_flag = 1 if has_mixed else 0

                # Headers
                hsts, csp, xcto, xfo, refpol = security_headers_summary(response.headers)

                # Row issue: HTTP page or mixed content
                row_issue = 1 if (is_http_page or has_mixed_flag) else 0
                if row_issue:
                    total_issues_counter += 1

                csv_writer.writerow([
                    page_title, url, proto, is_http_page, has_mixed_flag, mixed_count,
                    hsts, csp, xcto, xfo, refpol, row_issue
                ])

                # Follow in-domain links only
                for link in soup.find_all('a', href=True):
                    if stop_scraping():
                        return
                    full_url = normalize_url(urljoin(base_url, link['href']))
                    base_root = normalize_url(base_url)
                    if base_root in full_url and is_same_site(full_url, base_root):
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

            # seed discovered with base URL and start
            base_norm = normalize_url(base_url)
            discovered_urls.add(base_norm)
            total_discovered = 1
            if on_progress:
                try:
                    on_progress(0, total_discovered)
                except Exception:
                    pass
            scrape_page(base_norm)
            # Summary row (keep existing)
            csv_writer.writerow(['', '', '', '', '', '', '', '', '', '', 'Total Rows with Issues:', total_issues_counter])
            # Additional summary rows (do not change columns)
            csv_writer.writerow(['', '', '', '', '', '', '', '', '', '', 'Summary - ALL Pages:', total_pages])
            csv_writer.writerow(['', '', '', '', '', '', '', '', '', '', 'Summary - HTTPS Pages:', https_pages])
            csv_writer.writerow(['', '', '', '', '', '', '', '', '', '', 'Summary - HTTP Pages:', http_pages])
            csv_writer.writerow(['', '', '', '', '', '', '', '', '', '', 'Summary - Other Pages:', other_pages])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nSecurity scan complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"Security scan complete! Results saved to {filepath}")
        if on_complete:
            try:
                on_complete()
            except Exception:
                pass

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
