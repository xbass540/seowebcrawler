import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import os
from meta_scraper import scrape_meta_descriptions
from error_scraper import scrape_404_errors

stop_flag = False
output_folder = ""


def ensure_https(url):
    return url if url.startswith(("http://", "https://")) else "https://" + url


def select_folder():
    global output_folder
    folder = filedialog.askdirectory(title="Select Folder for CSV Export")
    if folder:
        output_folder = folder
        folder_label.config(text=f"Selected Folder: {output_folder}")


def create_new_folder():
    global output_folder
    folder = filedialog.asksaveasfilename(
        title="Create New Folder", defaultextension=".folder",
        filetypes=[("Folder", "*.folder")]
    )
    if folder:
        folder_path = os.path.splitext(folder)[0]
        os.makedirs(folder_path, exist_ok=True)
        output_folder = folder_path
        folder_label.config(text=f"Created and Selected: {output_folder}")


def stop_scraping():
    global stop_flag
    return stop_flag


def update_stop_flag():
    global stop_flag
    stop_flag = True


def run_meta_scraper():
    url = url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    if not url or not output_folder:
        messagebox.showerror("Error", "Enter URL and select folder first.")
        return
    output_text.delete(1.0, tk.END)
    scrape_meta_descriptions(url, output_folder, output_text, stop_scraping, update_stop_flag)


def run_error_scraper():
    url = url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    if not url or not output_folder:
        messagebox.showerror("Error", "Enter URL and select folder first.")
        return
    output_text.delete(1.0, tk.END)
    scrape_404_errors(url, output_folder, output_text, stop_scraping, update_stop_flag)


def quit_app():
    root.quit()
    root.destroy()


# GUI setup
root = tk.Tk()
root.title("Meta Descriptions & 404 Errors Analyzer")

root.rowconfigure(5, weight=1)
root.columnconfigure(0, weight=1)

url_label = tk.Label(root, text="Enter Base URL:")
url_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

scrape_meta_button = tk.Button(root, text="Scrape Meta Descriptions", command=run_meta_scraper)
scrape_meta_button.grid(row=0, column=2, padx=10, pady=5)
scrape_404_button = tk.Button(root, text="Scrape 404 Errors", command=run_error_scraper)
scrape_404_button.grid(row=1, column=2, padx=10, pady=5)

folder_label = tk.Label(root, text="No folder selected.")
folder_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
select_folder_button = tk.Button(root, text="Select Folder", command=select_folder)
select_folder_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")
create_folder_button = tk.Button(root, text="Create Folder", command=create_new_folder)
create_folder_button.grid(row=2, column=1, padx=10, pady=5, sticky="w")

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, width=80)
output_text.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

stop_button = tk.Button(root, text="Stop", command=update_stop_flag, bg="red", fg="white")
stop_button.grid(row=6, column=0, padx=10, pady=5, sticky="w")
quit_button = tk.Button(root, text="Quit", command=quit_app, bg="red", fg="white")
quit_button.grid(row=6, column=1, padx=10, pady=5, sticky="w")

root.mainloop()
