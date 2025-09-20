import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from tkinter import ttk
import os
from meta_scraper import scrape_meta_descriptions
from error_scraper import scrape_404_errors
from image_scraper import scrape_images
from security_scraper import scrape_security
from page_titles_scraper import scrape_page_titles
from headings_scraper import scrape_h1_headings, scrape_h2_headings

tab_state = {
    'meta': {'stop': False, 'folder': ''},
    'errors': {'stop': False, 'folder': ''},
    'images': {'stop': False, 'folder': ''},
    'security': {'stop': False, 'folder': ''},
    'titles': {'stop': False, 'folder': ''},
    'h1': {'stop': False, 'folder': ''},
    'h2': {'stop': False, 'folder': ''},
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
    # Start indeterminate; switch to determinate on first real progress
    meta_start_btn.config(state='disabled')
    meta_progress.config(mode='indeterminate')
    meta_progress.start(10)
    meta_first_progress = {'switched': False}
    meta_last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            meta_progress.stop()
            meta_start_btn.config(state='normal')
            try:
                if not meta_first_progress['switched']:
                    meta_progress_label.config(text=f"Done ({meta_last_progress['current']}/{max(meta_last_progress['total'], 1)})")
                else:
                    meta_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            meta_last_progress['current'] = current
            meta_last_progress['total'] = total
            if not meta_first_progress['switched']:
                if total and total > 1:
                    meta_progress.stop()
                    meta_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    meta_first_progress['switched'] = True
                else:
                    try:
                        meta_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                meta_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if meta_first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    meta_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_meta_descriptions(url, folder, meta_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


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
    errors_start_btn.config(state='disabled')
    # Start as indeterminate until we have a real total > 1
    errors_progress.config(mode='indeterminate')
    errors_progress.start(10)
    first_progress = {'switched': False}
    last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            errors_progress.stop()
            errors_start_btn.config(state='normal')
            try:
                if not first_progress['switched']:
                    # never switched to determinate, likely only base page
                    errors_progress_label.config(text=f"Done ({last_progress['current']}/{max(last_progress['total'], 1)})")
                else:
                    errors_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            # remember last numbers for done message
            last_progress['current'] = current
            last_progress['total'] = total

            if not first_progress['switched']:
                if total and total > 1:
                    # switch to determinate only when we have more than one URL
                    errors_progress.stop()
                    errors_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    first_progress['switched'] = True
                else:
                    # keep spinning and show discovering label
                    try:
                        errors_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                errors_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            # update percent label
            try:
                if first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    errors_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_404_errors(url, folder, errors_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


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
    images_start_btn.config(state='disabled')
    images_progress.config(mode='indeterminate')
    images_progress.start(10)
    images_first_progress = {'switched': False}
    images_last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            images_progress.stop()
            images_start_btn.config(state='normal')
            try:
                if not images_first_progress['switched']:
                    images_progress_label.config(text=f"Done ({images_last_progress['current']}/{max(images_last_progress['total'], 1)})")
                else:
                    images_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            images_last_progress['current'] = current
            images_last_progress['total'] = total
            if not images_first_progress['switched']:
                if total and total > 1:
                    images_progress.stop()
                    images_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    images_first_progress['switched'] = True
                else:
                    try:
                        images_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                images_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if images_first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    images_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_images(url, folder, images_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


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
    security_start_btn.config(state='disabled')
    security_progress.config(mode='indeterminate')
    security_progress.start(10)
    security_first_progress = {'switched': False}
    security_last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            security_progress.stop()
            security_start_btn.config(state='normal')
            try:
                if not security_first_progress['switched']:
                    security_progress_label.config(text=f"Done ({security_last_progress['current']}/{max(security_last_progress['total'], 1)})")
                else:
                    security_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            security_last_progress['current'] = current
            security_last_progress['total'] = total
            if not security_first_progress['switched']:
                if total and total > 1:
                    security_progress.stop()
                    security_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    security_first_progress['switched'] = True
                else:
                    try:
                        security_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                security_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if security_first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    security_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_security(url, folder, security_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


def run_titles_scraper():
    url = titles_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['titles']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['titles']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('titles')
    titles_output_text.delete(1.0, tk.END)
    titles_start_btn.config(state='disabled')
    titles_progress.config(mode='indeterminate')
    titles_progress.start(10)
    titles_first_progress = {'switched': False}
    titles_last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            titles_progress.stop()
            titles_start_btn.config(state='normal')
            try:
                if not titles_first_progress['switched']:
                    titles_progress_label.config(text=f"Done ({titles_last_progress['current']}/{max(titles_last_progress['total'], 1)})")
                else:
                    titles_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            titles_last_progress['current'] = current
            titles_last_progress['total'] = total
            if not titles_first_progress['switched']:
                if total and total > 1:
                    titles_progress.stop()
                    titles_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    titles_first_progress['switched'] = True
                else:
                    try:
                        titles_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                titles_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if titles_first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    titles_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_page_titles(url, folder, titles_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


def run_h1_scraper():
    url = h1_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['h1']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['h1']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('h1')
    h1_output_text.delete(1.0, tk.END)
    h1_start_btn.config(state='disabled')
    h1_progress.config(mode='indeterminate')
    h1_progress.start(10)
    first_progress = {'switched': False}
    last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            h1_progress.stop()
            h1_start_btn.config(state='normal')
            try:
                if not first_progress['switched']:
                    h1_progress_label.config(text=f"Done ({last_progress['current']}/{max(last_progress['total'], 1)})")
                else:
                    h1_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            last_progress['current'] = current
            last_progress['total'] = total
            if not first_progress['switched']:
                if total and total > 1:
                    h1_progress.stop()
                    h1_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    first_progress['switched'] = True
                else:
                    try:
                        h1_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                h1_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    h1_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_h1_headings(url, folder, h1_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


def run_h2_scraper():
    url = h2_url_entry.get().strip().rstrip("/")
    url = ensure_https(url)
    folder = tab_state['h2']['folder']
    if not url or not folder:
        messagebox.showerror("Error", "Enter URL and select export folder first.")
        return
    tab_state['h2']['stop'] = False
    stop_fn, update_stop_fn = make_stop_functions('h2')
    h2_output_text.delete(1.0, tk.END)
    h2_start_btn.config(state='disabled')
    h2_progress.config(mode='indeterminate')
    h2_progress.start(10)
    first_progress = {'switched': False}
    last_progress = {'current': 0, 'total': 0}
    def on_complete():
        def _done():
            h2_progress.stop()
            h2_start_btn.config(state='normal')
            try:
                if not first_progress['switched']:
                    h2_progress_label.config(text=f"Done ({last_progress['current']}/{max(last_progress['total'], 1)})")
                else:
                    h2_progress_label.config(text='Done')
            except Exception:
                pass
        root.after(0, _done)
    def on_progress(current, total):
        def _update():
            last_progress['current'] = current
            last_progress['total'] = total
            if not first_progress['switched']:
                if total and total > 1:
                    h2_progress.stop()
                    h2_progress.config(mode='determinate', maximum=max(total, 1), value=min(current, max(total, 1)))
                    first_progress['switched'] = True
                else:
                    try:
                        h2_progress_label.config(text=f"Discovering… ({current}/{max(total,1)})")
                    except Exception:
                        pass
            else:
                h2_progress.config(maximum=max(total, 1), value=min(current, max(total, 1)))
            try:
                if first_progress['switched']:
                    pct = int(100 * (0 if total <= 0 else min(current, total) / max(total, 1)))
                    h2_progress_label.config(text=f"{pct}% ({current}/{total})")
            except Exception:
                pass
        root.after(0, _update)
    scrape_h2_headings(url, folder, h2_output_text, stop_fn, update_stop_fn, on_complete=on_complete, on_progress=on_progress)


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
meta_stop_btn = tk.Button(meta_tab, text="Stop", command=lambda: (tab_state.__setitem__('meta', {**tab_state['meta'], 'stop': True}), meta_progress.stop(), meta_start_btn.config(state='normal')), bg='red', fg='white')
meta_stop_btn.grid(row=2, column=2, padx=10, pady=5)

meta_output_text = scrolledtext.ScrolledText(meta_tab, wrap=tk.WORD, height=20, width=80)
meta_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
meta_tab.rowconfigure(3, weight=1)
meta_tab.columnconfigure(1, weight=1)
meta_progress = ttk.Progressbar(meta_tab, mode='determinate', length=200)
meta_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
meta_progress_label = tk.Label(meta_tab, text="0% (0/0)")
meta_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

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
errors_stop_btn = tk.Button(errors_tab, text="Stop", command=lambda: (tab_state.__setitem__('errors', {**tab_state['errors'], 'stop': True}), errors_progress.stop(), errors_start_btn.config(state='normal')), bg='red', fg='white')
errors_stop_btn.grid(row=2, column=2, padx=10, pady=5)

errors_output_text = scrolledtext.ScrolledText(errors_tab, wrap=tk.WORD, height=20, width=80)
errors_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
errors_tab.rowconfigure(3, weight=1)
errors_tab.columnconfigure(1, weight=1)
errors_progress = ttk.Progressbar(errors_tab, mode='determinate', length=200)
errors_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
errors_progress_label = tk.Label(errors_tab, text="0% (0/0)")
errors_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

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
images_stop_btn = tk.Button(images_tab, text="Stop", command=lambda: (tab_state.__setitem__('images', {**tab_state['images'], 'stop': True}), images_progress.stop(), images_start_btn.config(state='normal')), bg='red', fg='white')
images_stop_btn.grid(row=2, column=2, padx=10, pady=5)

images_output_text = scrolledtext.ScrolledText(images_tab, wrap=tk.WORD, height=20, width=80)
images_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
images_tab.rowconfigure(3, weight=1)
images_tab.columnconfigure(1, weight=1)
images_progress = ttk.Progressbar(images_tab, mode='determinate', length=200)
images_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
images_progress_label = tk.Label(images_tab, text="0% (0/0)")
images_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

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
security_stop_btn = tk.Button(security_tab, text="Stop", command=lambda: (tab_state.__setitem__('security', {**tab_state['security'], 'stop': True}), security_progress.stop(), security_start_btn.config(state='normal')), bg='red', fg='white')
security_stop_btn.grid(row=2, column=2, padx=10, pady=5)

security_output_text = scrolledtext.ScrolledText(security_tab, wrap=tk.WORD, height=20, width=80)
security_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
security_tab.rowconfigure(3, weight=1)
security_tab.columnconfigure(1, weight=1)
security_progress = ttk.Progressbar(security_tab, mode='determinate', length=200)
security_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
security_progress_label = tk.Label(security_tab, text="0% (0/0)")
security_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

# Page Titles tab
titles_tab = ttk.Frame(notebook)
notebook.add(titles_tab, text='Page Titles')

tk.Label(titles_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
titles_url_entry = tk.Entry(titles_tab, width=50)
titles_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

titles_export_label = tk.Label(titles_tab, text="No export folder selected.")
titles_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
titles_export_btn = tk.Button(titles_tab, text="Export Folder", command=lambda: select_folder_for('titles', titles_export_label))
titles_export_btn.grid(row=0, column=2, padx=10, pady=5)

titles_start_btn = tk.Button(titles_tab, text="Start", command=run_titles_scraper)
titles_start_btn.grid(row=1, column=2, padx=10, pady=5)
titles_stop_btn = tk.Button(titles_tab, text="Stop", command=lambda: (tab_state.__setitem__('titles', {**tab_state['titles'], 'stop': True}), titles_progress.stop(), titles_start_btn.config(state='normal')), bg='red', fg='white')
titles_stop_btn.grid(row=2, column=2, padx=10, pady=5)

titles_output_text = scrolledtext.ScrolledText(titles_tab, wrap=tk.WORD, height=20, width=80)
titles_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
titles_tab.rowconfigure(3, weight=1)
titles_tab.columnconfigure(1, weight=1)
titles_progress = ttk.Progressbar(titles_tab, mode='determinate', length=200)
titles_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
titles_progress_label = tk.Label(titles_tab, text="0% (0/0)")
titles_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

# H1 Headings tab
h1_tab = ttk.Frame(notebook)
notebook.add(h1_tab, text='H1 Headings')

tk.Label(h1_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
h1_url_entry = tk.Entry(h1_tab, width=50)
h1_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

h1_export_label = tk.Label(h1_tab, text="No export folder selected.")
h1_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
h1_export_btn = tk.Button(h1_tab, text="Export Folder", command=lambda: select_folder_for('h1', h1_export_label))
h1_export_btn.grid(row=0, column=2, padx=10, pady=5)

h1_start_btn = tk.Button(h1_tab, text="Start", command=run_h1_scraper)
h1_start_btn.grid(row=1, column=2, padx=10, pady=5)
h1_stop_btn = tk.Button(h1_tab, text="Stop", command=lambda: (tab_state.__setitem__('h1', {**tab_state['h1'], 'stop': True}), h1_progress.stop(), h1_start_btn.config(state='normal')), bg='red', fg='white')
h1_stop_btn.grid(row=2, column=2, padx=10, pady=5)

h1_output_text = scrolledtext.ScrolledText(h1_tab, wrap=tk.WORD, height=20, width=80)
h1_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
h1_tab.rowconfigure(3, weight=1)
h1_tab.columnconfigure(1, weight=1)
h1_progress = ttk.Progressbar(h1_tab, mode='determinate', length=200)
h1_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
h1_progress_label = tk.Label(h1_tab, text="0% (0/0)")
h1_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

# H2 Headings tab
h2_tab = ttk.Frame(notebook)
notebook.add(h2_tab, text='H2 Headings')

tk.Label(h2_tab, text="Enter Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
h2_url_entry = tk.Entry(h2_tab, width=50)
h2_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

h2_export_label = tk.Label(h2_tab, text="No export folder selected.")
h2_export_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
h2_export_btn = tk.Button(h2_tab, text="Export Folder", command=lambda: select_folder_for('h2', h2_export_label))
h2_export_btn.grid(row=0, column=2, padx=10, pady=5)

h2_start_btn = tk.Button(h2_tab, text="Start", command=run_h2_scraper)
h2_start_btn.grid(row=1, column=2, padx=10, pady=5)
h2_stop_btn = tk.Button(h2_tab, text="Stop", command=lambda: (tab_state.__setitem__('h2', {**tab_state['h2'], 'stop': True}), h2_progress.stop(), h2_start_btn.config(state='normal')), bg='red', fg='white')
h2_stop_btn.grid(row=2, column=2, padx=10, pady=5)

h2_output_text = scrolledtext.ScrolledText(h2_tab, wrap=tk.WORD, height=20, width=80)
h2_output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
h2_tab.rowconfigure(3, weight=1)
h2_tab.columnconfigure(1, weight=1)
h2_progress = ttk.Progressbar(h2_tab, mode='determinate', length=200)
h2_progress.grid(row=4, column=0, padx=10, pady=5, sticky='w')
h2_progress_label = tk.Label(h2_tab, text="0% (0/0)")
h2_progress_label.grid(row=4, column=1, padx=10, pady=5, sticky='w')

# Global quit button
quit_button = tk.Button(root, text="Quit", command=quit_app, bg='red', fg='white')
quit_button.pack(side='left', padx=10, pady=(0, 10))

root.mainloop()
