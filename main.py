import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from tkinter import ttk
import os
from meta_scraper import scrape_meta_descriptions
from error_scraper import scrape_404_errors
from image_scraper import scrape_images
from security_scraper import scrape_security

tab_state = {
    'meta': {'stop': False, 'folder': ''},
    'errors': {'stop': False, 'folder': ''},
    'images': {'stop': False, 'folder': ''},
    'security': {'stop': False, 'folder': ''},
}


def ensure_https(url):
    return url if url.startswith(("http://", "https://")) else "https://" + url


def select_folder_for(tab_key, label_widget):
    folder = filedialog.askdirectory(title="Select Export Folder")
    if folder:
        tab_state[tab_key]['folder'] = folder
        label_widget.config(text=f"Export Folder: {folder}")




def make_stop_functions(tab_key):
    def stop_scraping():
        return tab_state[tab_key]['stop']
    def update_stop_flag():
        tab_state[tab_key]['stop'] = True
    return stop_scraping, update_stop_flag


def run_meta_scraper():
    url = meta_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['meta']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    # Reset stop flag for this run and wire stop functions
    tab_state['meta']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('meta')
    meta_output_text.delete(1.0, tk.END)
    scrape_meta_descriptions(url, folder, meta_output_text, stop_fn, update_stop_fn)


def run_error_scraper():
    url = errors_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['errors']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['errors']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('errors')
    errors_output_text.delete(1.0, tk.END)
    scrape_404_errors(url, folder, errors_output_text, stop_fn, update_stop_fn)


def run_image_scraper():
    url = images_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['images']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['images']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('images')
    images_output_text.delete(1.0, tk.END)
    scrape_images(url, folder, images_output_text, stop_fn, update_stop_fn)


def run_security_scraper():
    url = security_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['security']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['security']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('security')
    security_output_text.delete(1.0, tk.END)
    scrape_security(url, folder, security_output_text, stop_fn, update_stop_fn)


def quit_app():
    root.quit()
    root.destroy()


# GUI setup
root = tk.Tk()
root.title("SEO Analyzer")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True, padx=10, pady=10)

# Meta tab
meta_tab = ttk.Frame(notebook)
notebook.add(meta_tab, text='Meta Descriptions')

tk.Label(meta_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
meta_url_entry = tk.Entry(meta_tab, width=50)
meta_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

meta_export_label = tk.Label(meta_tab, text="No export folder selected.")
meta_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
meta_export_btn = tk.Button(meta_tab, text="Export Folder", command=lambda: select_folder_for('meta', meta_export_label))
meta_export_btn.grid(row=0, column=2, padx=10, pady=5)

meta_start_btn = tk.Button(meta_tab, text="Start", command=run_meta_scraper)
meta_start_btn.grid(row=1, column=2, padx=10, pady=5)
meta_stop_btn = tk.Button(meta_tab, text="Stop", command=lambda: tab_state.__setitem__('meta', {**tab_state['meta'], 'stop': True}), bg='red', fg='white')
meta_stop_btn.grid(row=2, column=2, padx=10, pady=5)

meta_output_text = scrolledtext.ScrolledText(meta_tab, wrap=tk.WORD, height=20, width=80)
meta_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
meta_tab.rowconfigure(3, weight=1)
meta_tab.columnconfigure(1, weight=1)

# 404 Errors tab
errors_tab = ttk.Frame(notebook)
notebook.add(errors_tab, text='404 Errors')

tk.Label(errors_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
errors_url_entry = tk.Entry(errors_tab, width=50)
errors_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

errors_export_label = tk.Label(errors_tab, text="No export folder selected.")
errors_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
errors_export_btn = tk.Button(errors_tab, text="Export Folder", command=lambda: select_folder_for('errors', errors_export_label))
errors_export_btn.grid(row=0, column=2, padx=10, pady=5)

errors_start_btn = tk.Button(errors_tab, text="Start", command=run_error_scraper)
errors_start_btn.grid(row=1, column=2, padx=10, pady=5)
errors_stop_btn = tk.Button(errors_tab, text="Stop", command=lambda: tab_state.__setitem__('errors', {**tab_state['errors'], 'stop': True}), bg='red', fg='white')
errors_stop_btn.grid(row=2, column=2, padx=10, pady=5)

errors_output_text = scrolledtext.ScrolledText(errors_tab, wrap=tk.WORD, height=20, width=80)
errors_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
errors_tab.rowconfigure(3, weight=1)
errors_tab.columnconfigure(1, weight=1)

# Images tab
images_tab = ttk.Frame(notebook)
notebook.add(images_tab, text='Images')

tk.Label(images_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
images_url_entry = tk.Entry(images_tab, width=50)
images_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

images_export_label = tk.Label(images_tab, text="No export folder selected.")
images_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
images_export_btn = tk.Button(images_tab, text="Export Folder", command=lambda: select_folder_for('images', images_export_label))
images_export_btn.grid(row=0, column=2, padx=10, pady=5)

images_start_btn = tk.Button(images_tab, text="Start", command=run_image_scraper)
images_start_btn.grid(row=1, column=2, padx=10, pady=5)
images_stop_btn = tk.Button(images_tab, text="Stop", command=lambda: tab_state.__setitem__('images', {**tab_state['images'], 'stop': True}), bg='red', fg='white')
images_stop_btn.grid(row=2, column=2, padx=10, pady=5)

images_output_text = scrolledtext.ScrolledText(images_tab, wrap=tk.WORD, height=20, width=80)
images_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
images_tab.rowconfigure(3, weight=1)
images_tab.columnconfigure(1, weight=1)

# Security tab
security_tab = ttk.Frame(notebook)
notebook.add(security_tab, text='Security')

tk.Label(security_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
security_url_entry = tk.Entry(security_tab, width=50)
security_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

security_export_label = tk.Label(security_tab, text="No export folder selected.")
security_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
security_export_btn = tk.Button(security_tab, text="Export Folder", command=lambda: select_folder_for('security', security_export_label))
security_export_btn.grid(row=0, column=2, padx=10, pady=5)

security_start_btn = tk.Button(security_tab, text="Start", command=run_security_scraper)
security_start_btn.grid(row=1, column=2, padx=10, pady=5)
security_stop_btn = tk.Button(security_tab, text="Stop", command=lambda: tab_state.__setitem__('security', {**tab_state['security'], 'stop': True}), bg='red', fg='white')
security_stop_btn.grid(row=2, column=2, padx=10, pady=5)

security_output_text = scrolledtext.ScrolledText(security_tab, wrap=tk.WORD, height=20, width=80)
security_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
security_tab.rowconfigure(3, weight=1)
security_tab.columnconfigure(1, weight=1)

# Global quit button
quit_button = tk.Button(root, text="Quit", command=quit_app, bg='red', fg='white')
quit_button.pack(side='left', padx=10, pady=(0, 10))

root.mainloop()
