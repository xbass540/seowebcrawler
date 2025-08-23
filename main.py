import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import random

# Global variable to manage thread stopping
stop_scraping = False
output_folder = ""  # Folder selected by the user for CSV export

def select_folder():
    global output_folder
    folder = filedialog.askdirectory(
        title="Select Existing Folder for CSV Export"
    )
    if folder:
        output_folder = folder
        folder_label.config(text=f"Selected Folder: {output_folder}")

def create_new_folder():
    global output_folder
    folder = filedialog.asksaveasfilename(
        title="Create New Folder for CSV Export",
        initialfile="",
        filetypes=[("Folder", "*.folder")],
        defaultextension=".folder",
    )
    if folder:
        folder_path = os.path.splitext(folder)[0]  # Remove the dummy extension
        os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
        output_folder = folder_path
        folder_label.config(text=f"Created and Selected Folder: {output_folder}")

def normalize_url(url):
    url = url.strip().rstrip("/")  # Trim spaces & trailing slashes
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url

def scrape_meta_descriptions():
    global stop_scraping, output_folder
    base_url = normalize_url(url_entry.get())
    if not base_url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return

    if not output_folder:
        messagebox.showerror("Error", "Please select or create a folder for exporting the CSV.")
        return

    output_text.delete(1.0, tk.END)
    stop_scraping = False

    def scrape_process():
        global stop_scraping
        random_number = random.randint(1000, 9999)
        filename = f'{base_url.replace("https://","").replace("http://","")}-meta-descriptions-{random_number}.csv'

        csv_file = open(os.path.join(output_folder, filename), 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Post Name', 'Post URL', 'Meta Description', 'Posts with Issues'])

        visited_urls = set()
        article_counter = 1
        issues_counter = 0

        def scrape_page(url):
            nonlocal article_counter, issues_counter
            global stop_scraping
            if stop_scraping:
                output_text.insert(tk.END, "Scraping stopped by user.\n")
                output_text.see("end")
                return
            if url in visited_urls:
                return
            visited_urls.add(url)

            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                output_text.insert(tk.END, f"Failed to fetch {url}: {e}\n")
                output_text.see("end")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            output_text.insert(tk.END, f"Scraping URL: {url}\n")
            output_text.see("end")

            meta_description_tag = soup.find('meta', property="og:description")
            meta_description = meta_description_tag['content'].strip() if meta_description_tag and 'content' in meta_description_tag.attrs and meta_description_tag['content'] else "No description"

            if meta_description == "No description":
                issues_counter += 1

            for article in soup.find_all('article'):
                if stop_scraping:
                    output_text.insert(tk.END, "Scraping stopped by user.\n")
                    output_text.see("end")
                    return
                headline = article.find('h2').text.strip() if article.find('h2') else "No headline"
                article_url = article.find('a', href=True)
                if article_url:
                    full_url = urljoin(base_url, article_url['href'])
                    article_info = f"# {article_counter}: {headline} \n URL: {full_url}\n Meta Description: {meta_description}\n\n"
                    output_text.insert(tk.END, article_info)
                    output_text.see("end")
                    csv_writer.writerow([headline, full_url, meta_description, issues_counter])
                    article_counter += 1

            for link in soup.find_all('a', href=True):
                if stop_scraping:
                    output_text.insert(tk.END, "Scraping stopped by user.\n")
                    output_text.see("end")
                    return
                full_url = urljoin(base_url, link['href'])
                if base_url in full_url:
                    scrape_page(full_url)

        scrape_page(base_url)

        if not stop_scraping:
            csv_writer.writerow(['', '', 'Total Posts with Issues:', issues_counter])
            output_text.insert(tk.END, f"\nScraping complete. Results saved to {os.path.join(output_folder, filename)}\n")
            output_text.see("end")
            messagebox.showinfo("Success", f"Scraping complete! Results saved to {os.path.join(output_folder, filename)}")

        csv_file.close()

    thread = threading.Thread(target=scrape_process)
    thread.daemon = True
    thread.start()

def scrape_404_errors():
    global stop_scraping, output_folder
    base_url = normalize_url(url_entry.get())
    if not base_url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return

    if not output_folder:
        messagebox.showerror("Error", "Please select or create a folder for exporting the CSV.")
        return

    output_text.delete(1.0, tk.END)
    stop_scraping = False

    def scrape_process():
        global stop_scraping
        random_number = random.randint(1000, 9999)
        filename = f'{base_url.replace("https://","").replace("http://","")}-404-errors-{random_number}.csv'

        csv_file = open(os.path.join(output_folder, filename), 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Post Name', 'Post URL', 'Not Found', 'Posts with Issues'])

        visited_urls = set()
        article_counter = 1
        issues_counter = 0

        def scrape_page(url):
            nonlocal article_counter, issues_counter
            global stop_scraping
            if stop_scraping:
                output_text.insert(tk.END, "Scraping stopped by user.\n")
                output_text.see("end")
                return
            if url in visited_urls:
                return
            visited_urls.add(url)

            try:
                response = requests.get(url)
                if response.status_code == 404:
                    output_text.insert(tk.END, f"404 Not Found: {url}\n")
                    output_text.see("end")
                    csv_writer.writerow([f"Article {article_counter}", url, "404 Not Found", issues_counter])
                    issues_counter += 1
                    return
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                output_text.insert(tk.END, f"Failed to fetch {url}: {e}\n")
                output_text.see("end")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            output_text.insert(tk.END, f"Scraping URL: {url}\n")
            output_text.see("end")

            page_title = soup.find('title').text.strip() if soup.find('title') else "No title"
            csv_writer.writerow([page_title, url, "Page Found", issues_counter])
            article_counter += 1

            for link in soup.find_all('a', href=True):
                full_url = urljoin(base_url, link['href'])
                if base_url in full_url:
                    scrape_page(full_url)

        scrape_page(base_url)

        if not stop_scraping:
            csv_writer.writerow(['', '', 'Total Pages with Issues:', issues_counter])
            output_text.insert(tk.END, f"\nScraping complete. Results saved to {os.path.join(output_folder, filename)}\n")
            output_text.see("end")
            messagebox.showinfo("Success", f"Scraping complete! Results saved to {os.path.join(output_folder, filename)}")

        csv_file.close()

    thread = threading.Thread(target=scrape_process)
    thread.daemon = True
    thread.start()

def stop_scrape():
    global stop_scraping
    stop_scraping = True

def quit_app():
    global root
    root.quit()
    root.destroy()

# GUI
root = tk.Tk()
root.title("Meta Descriptions & 404 Errors Analyzer")

root.rowconfigure(6, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

url_label = tk.Label(root, text="Enter Website URL:")
url_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

select_folder_button = tk.Button(root, text="Select Existing Folder", command=select_folder)
select_folder_button.grid(row=1, column=0, pady=10, padx=5)

create_folder_button = tk.Button(root, text="Create New Folder", command=create_new_folder)
create_folder_button.grid(row=1, column=1, pady=10, padx=5)

folder_label = tk.Label(root, text="No folder selected", anchor="w")
folder_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10)

execute_button = tk.Button(root, text="Find Missing Meta Descriptions", command=scrape_meta_descriptions)
execute_button.grid(row=3, column=0, pady=10, padx=5)

errors_button = tk.Button(root, text="404 Errors", command=scrape_404_errors)
errors_button.grid(row=3, column=1, pady=10, padx=5)

stop_button = tk.Button(root, text="Stop", command=stop_scrape, bg="red", fg="white")
stop_button.grid(row=4, column=0, pady=10, padx=5, sticky="w")

quit_button = tk.Button(root, text="Quit App", command=quit_app, bg="red", fg="white")
quit_button.grid(row=4, column=1, pady=10, padx=5, sticky="e")

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
output_text.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

root.mainloop()
