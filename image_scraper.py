import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import csv
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox


def scrape_images(base_url, output_folder, output_text, stop_scraping, update_stop_flag, on_complete=None, on_progress=None):
    """Scrapes the website for <img> tags and exports their data to CSV.

    Columns exported:
    - Page Title
    - Page URL
    - Image Src (absolute)
    - Alt Text
    - Has Alt Attribute (Yes/No)
    - Extension (jpg, png, svg, etc.)
    - Alt Too Long (>100) (1/0)
    - Image Size (KB)
    - Size Too Large (>100KB) (1/0)
    - Images with Issues (1 if missing/empty alt OR alt text > 100 chars OR size > 100KB, else 0)
    """

    def scrape_process():
        random_number = random.randint(1000, 9999)
        filename = f"{base_url[8:]}-images-{random_number}.csv"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'Page Title', 'Page URL', 'Image Src', 'Alt Text', 'Has Alt Attribute', 'Extension', 'Alt Too Long (>100)', 'Image Size (KB)', 'Size Too Large (>100KB)', 'Images with Issues'
            ])

            visited_urls = set()
            total_issues_counter = 0
            # Image-specific counters
            total_pages = 0               # pages crawled
            total_images = 0              # total image rows written
            images_missing_alt = 0        # rows with row_issue == 1
            images_with_alt = 0           # rows with row_issue == 0
            images_alt_too_long = 0       # rows where alt text length > 100
            images_size_too_large = 0     # rows where size > 100KB
            image_size_cache = {}         # cache by image src URL -> size in bytes (int) or None if unknown
            recorded_images = set()
            # progress tracking
            discovered_urls = set()
            total_discovered = 0
            visited_count = 0

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

            def get_image_size_bytes(abs_url: str):
                """Attempt to determine image size in bytes.
                Strategy:
                 - HEAD request for Content-Length
                 - If missing, stream GET and stop after exceeding 100KB threshold to avoid large downloads
                Returns: (size_bytes: int|None, size_too_large: bool)
                """
                # Check cache first
                if abs_url in image_size_cache:
                    size = image_size_cache[abs_url]
                    if size is None:
                        return None, False
                    return size, size > 100 * 1024

                threshold = 100 * 1024  # 100KB
                try:
                    head = requests.head(abs_url, allow_redirects=True, timeout=5)
                    cl = head.headers.get('Content-Length')
                    if cl and cl.isdigit():
                        size_int = int(cl)
                        image_size_cache[abs_url] = size_int
                        return size_int, size_int > threshold
                except requests.RequestException:
                    pass

                # Fallback: streamed GET with early stop
                try:
                    with requests.get(abs_url, stream=True, timeout=10) as r:
                        r.raise_for_status()
                        total = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if not chunk:
                                continue
                            total += len(chunk)
                            if total > threshold:
                                image_size_cache[abs_url] = total
                                return total, True
                        image_size_cache[abs_url] = total
                        return total, total > threshold
                except requests.RequestException:
                    image_size_cache[abs_url] = None
                    return None, False

            def normalize_url(u: str) -> str:
                return urldefrag(u)[0]

            def scrape_page(url):
                nonlocal total_issues_counter, visited_count, total_discovered, discovered_urls, total_pages, total_images, images_missing_alt, images_with_alt, images_alt_too_long, images_size_too_large

                if stop_scraping():
                    return
                url = normalize_url(url)
                if url in visited_urls:
                    return
                visited_urls.add(url)

                # Count this page
                total_pages += 1

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

                    # Determine issues (alt-related)
                    is_missing_or_empty = (alt_text_clean == '')
                    is_too_long = (len(alt_text_clean) > 100) if alt_text_clean else False
                    if is_missing_or_empty:
                        images_missing_alt += 1
                    else:
                        # Has some alt text
                        images_with_alt += 1
                        if is_too_long:
                            images_alt_too_long += 1

                    ext = get_extension_from_url(img_src)

                    # Determine image size
                    size_bytes, size_too_large = get_image_size_bytes(img_src)
                    size_kb_display = round(size_bytes / 1024.0, 2) if isinstance(size_bytes, int) else ''
                    if size_too_large:
                        images_size_too_large += 1

                    # Per-row issue flag: 1 if any issue (missing/empty alt, alt too long, or size too large)
                    row_issue = 1 if (is_missing_or_empty or is_too_long or size_too_large) else 0
                    if row_issue:
                        total_issues_counter += 1

                    csv_writer.writerow([
                        page_title, url, img_src, alt_text_clean, has_alt_attr, ext, 1 if is_too_long else 0, size_kb_display, 1 if size_too_large else 0, row_issue
                    ])
                    total_images += 1

                # Follow in-domain links
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
            # Summary row at the end (keep existing)
            csv_writer.writerow(['', '', '', '', '', '', '', 'Total Images with Issues:', total_issues_counter])
            # Additional image-specific summary rows (do not change columns)
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Total Pages Crawled:', total_pages])
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Total Images Recorded:', total_images])
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Images Missing Alt:', images_missing_alt])
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Images With Alt:', images_with_alt])
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Images Alt > 100 chars:', images_alt_too_long])
            csv_writer.writerow(['', '', '', '', '', '', '', 'Summary - Images Size > 100KB:', images_size_too_large])

        if stop_scraping():
            output_text.insert(tk.END, "\nScraping stopped by user.\n")
        else:
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
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    thread = threading.Thread(target=wrapped_process, daemon=True)
    thread.start()
