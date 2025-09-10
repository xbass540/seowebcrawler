import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_images(base_url, output_folder, output_text, stop_scraping, update_stop_flag):
    """Scrapes the website for <img> tags and exports their data to CSV.

    Columns exported:
    - Page Title
    - Page URL
    - Image Src (absolute)
    - Alt Text
    - Has Alt Attribute (Yes/No)
    - Extension (jpg, png, svg, etc.)
    - Images with Issues (running count of images missing/empty alt)
    """

    def scrape_process():
        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-images-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'Page Title', 'Page URL', 'Image Src', 'Alt Text', 'Has Alt Attribute', 'Extension', 'Images with Issues'
            ])

            visited_urls = set()
            total_issues_counter = 0
            recorded_images = set()

            def get_extension_from_url(url: str) -> str:
                try:
                    path = urlparse(url).path
                    _, ext = os.path.splitext(path)
                    return ext[1:].lower() if ext else ''
                except Exception:
                    return ''

            def is_image_url(url: str) -> bool:
                """Heuristically determine if a URL points to an image.
                First checks by extension; if unknown, performs a HEAD request to verify Content-Type.
                """
                allowed_ext = {
                    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tif', 'tiff', 'ico', 'avif'
                }
                ext = get_extension_from_url(url)
                if ext in allowed_ext:
                    return True
                # Some CDNs serve images without extensions. Try HEAD to verify Content-Type.
                try:
                    head = requests.head(url, allow_redirects=True, timeout=5)
                    content_type = head.headers.get('Content-Type', '')
                    return content_type.lower().startswith('image/')
                except requests.RequestException:
                    return False

            def is_tracking_pixel(img_tag, abs_url: str) -> bool:
                """Attempt to filter common tracking/analytics pixels.
                Heuristics:
                 - Known tracking domains/paths (e.g., facebook.com/tr)
                 - 1x1 pixel dimensions via width/height/style
                 - CSS display:none
                """
                url_l = abs_url.lower()
                tracking_keywords = [
                    'facebook.com/tr', 'connect.facebook.net', 'google-analytics.com',
                    'googletagmanager.com', 'analytics.google.com', 'doubleclick.net',
                    'adservice.google.com', 'stats.g.doubleclick.net', 'adsystem', 'adroll',
                    'pixel.', '/pixel', 'beacon', 'optimizely', 'hotjar', 'mixpanel',
                    'segment.com', 'matomo', 'clarity.ms'
                ]
                if any(k in url_l for k in tracking_keywords):
                    return True

                # Check for 1x1 or hidden via attributes/styles
                width = (img_tag.get('width') or '').strip()
                height = (img_tag.get('height') or '').strip()
                style = (img_tag.get('style') or '').lower()
                if width == '1' and height == '1':
                    return True
                if 'display:none' in style:
                    return True
                if 'width:1' in style and 'height:1' in style:
                    return True

                return False

            def normalize_url(u: str) -> str:
                return urldefrag(u)[0]

            def scrape_page(url):
                nonlocal total_issues_counter

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
                    return

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.find('title').text.strip() if soup.find('title') else 'No title'
                output_text.insert(tk.END, f"Scraping URL: {url}\n")
                output_text.see('end')

                # Extract images on this page
                for img in soup.find_all('img'):
                    if stop_scraping():
                        return

                    src_raw = img.get('src') or ''
                    if not src_raw:
                        continue
                    img_src = urljoin(url, src_raw)
                    img_src = normalize_url(img_src)

                    # Ensure the src actually points to an image
                    if not is_image_url(img_src):
                        continue

                    # Filter tracking/analytics pixels
                    if is_tracking_pixel(img, img_src):
                        continue

                    # Skip duplicates: only record each (page URL, image src) once
                    unique_key = (url, img_src)
                    if unique_key in recorded_images:
                        continue
                    recorded_images.add(unique_key)

                    has_alt_attr = 'Yes' if img.has_attr('alt') else 'No'
                    alt_text = img.get('alt') if img.has_attr('alt') else ''
                    alt_text_clean = (alt_text or '').strip()

                    # Per-row issue flag: 1 if missing/empty alt, else 0
                    row_issue = 1 if not alt_text_clean else 0
                    if row_issue:
                        total_issues_counter += 1

                    ext = get_extension_from_url(img_src)

                    csv_writer.writerow([
                        page_title, url, img_src, alt_text_clean, has_alt_attr, ext, row_issue
                    ])

                # Follow in-domain links
                for link in soup.find_all('a', href=True):
                    if stop_scraping():
                        return
                    full_url = normalize_url(urljoin(base_url, link['href']))
                    base_root = normalize_url(base_url)
                    if base_root in full_url:
                        scrape_page(full_url)

            scrape_page(normalize_url(base_url))
            # Summary row at the end
            csv_writer.writerow(['', '', '', '', 'Total Images with Alt Issues:', total_issues_counter, ''])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
            output_text.insert(tk.END, f"\nScraping complete. Results saved to {filepath}\n")
            messagebox.showinfo("Success", f"Scraping complete! Results saved to {filepath}")

    thread = threading.Thread(target=scrape_process, daemon=True)
    thread.start()
