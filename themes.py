import tkinter as tk # Import tkinter

"""
UI themes for the WiFi Brute Forcer.

This module defines color palettes for different seasons and provides
functions to apply these themes to the application.
"""

# Define color palettes for each season
THEMES = {
    "winter": {
        "bg_color": "#ADD8E6",  # Light blue
        "fg_color": "#000000",  # Black
        "btn_bg": "#87CEEB",  # Sky blue
        "btn_active_bg": "#708090",  # Slate gray
        "entry_bg": "#B0C4DE",  # Light steel blue
        "listbox_bg": "#B0C4DE",  # Light steel blue
        "select_bg": "#778899",  # Light slate gray
    },
    "summer": {
        "bg_color": "#FFFFE0",  # Light yellow
        "fg_color": "#000000",  # Black
        "btn_bg": "#FFD700",  # Gold
        "btn_active_bg": "#FFA500",  # Orange
        "entry_bg": "#F0E68C",  # Khaki
        "listbox_bg": "#F0E68C",  # Khaki
        "select_bg": "#FFDEAD",  # Navajo white
    },
    "autumn": {
        "bg_color": "#F5DEB3",  # Wheat
        "fg_color": "#000000",  # Black
        "btn_bg": "#D2B48C",  # Tan
        "btn_active_bg": "#CD853F",  # Peru
        "entry_bg": "#DEB887",  # Burlywood
        "listbox_bg": "#DEB887",  # Burlywood
        "select_bg": "#BC8F8F",  # Rosy brown
    },
    "spring": {
        "bg_color": "#90EE90",  # Light green
        "fg_color": "#000000",  # Black
        "btn_bg": "#3CB371",  # Medium sea green
        "btn_active_bg": "#2E8B57",  # Sea green
        "entry_bg": "#98FB98",  # Pale green
        "listbox_bg": "#98FB98",  # Pale green
        "select_bg": "#8FBC8F",  # Dark sea green
    },
    "dark": {  # Default dark theme
        "bg_color": "#2e2e2e",
        "fg_color": "#ffffff",
        "btn_bg": "#444444",
        "btn_active_bg": "#555555",
        "entry_bg": "#3e3e3e",
        "listbox_bg": "#3e3e3e",
        "select_bg": "#555555",
    }
}

# --- Theme application functions (to be implemented later) ---

def get_current_theme() -> dict:
    """
    Returns the current theme's color palette.
    For now, defaults to "dark".
    """
    # TODO: Implement logic to get the actual current theme
    # For now, it will be managed by the application state.
    # This function might be better placed in the main app logic
    # if the current theme is stored there.
    global CURRENT_THEME_NAME
    return THEMES.get(CURRENT_THEME_NAME, THEMES["dark"])

def set_current_theme_name(theme_name: str):
    """Sets the global current theme name."""
    global CURRENT_THEME_NAME
    if theme_name in THEMES:
        CURRENT_THEME_NAME = theme_name
    else:
        print(f"Warning: Theme '{theme_name}' not found. Current theme unchanged.")

# --- Auto-detect season ---
import datetime

def get_season(date=None):
    """
    Determines the season for a given date.
    If no date is provided, uses the current date.
    """
    if date is None:
        date = datetime.date.today()

    month = date.month
    day = date.day

    if (month == 12 and day >= 21) or month == 1 or month == 2 or (month == 3 and day < 20):
        return "winter"
    elif (month == 3 and day >= 20) or month == 4 or month == 5 or (month == 6 and day < 21):
        return "spring"
    elif (month == 6 and day >= 21) or month == 7 or month == 8 or (month == 9 and day < 22):
        return "summer"
    else: # (month == 9 and day >= 22) or month == 10 or month == 11 or (month == 12 and day < 21)
        return "autumn"

# Initialize current theme based on season
CURRENT_THEME_NAME = get_season()
if CURRENT_THEME_NAME not in THEMES: # Fallback if seasonal theme is not defined
    CURRENT_THEME_NAME = "dark"


# --- Theme application functions ---

def apply_theme_to_widget(widget, theme_colors: dict):
    """
    Applies the given theme colors to a specific widget.
    This is a placeholder and will need to be more specific
    based on widget types.
    """
    # General properties
    if 'bg' in widget.config():
        widget.config(bg=theme_colors.get("bg_color"))
    if 'fg' in widget.config():
        widget.config(fg=theme_colors.get("fg_color"))
    if 'activebackground' in widget.config():
        widget.config(activebackground=theme_colors.get("btn_active_bg"))
    if 'activeforeground' in widget.config(): # For checkbuttons, radiobuttons, buttons
        widget.config(activeforeground=theme_colors.get("fg_color")) # Assuming fg_color for active text

    # Specific widget types
    widget_type = widget.winfo_class()

    # General properties like bg, fg, activebackground, activeforeground are set above.
    # Here, we handle specifics like selectcolor or widget-specific relief/border.

    if widget_type == "Checkbutton" or widget_type == "Radiobutton":
        # selectcolor is the color of the check/radio mark itself when selected.
        # The bg/fg of the text part of the widget is handled by general properties.
        # activebackground/activeforeground for the text part is also handled by general properties.
        widget.config(
            selectcolor=theme_colors.get("btn_active_bg")
        )
    elif widget_type == "Button":
        # Ensure button-specific properties are set. General properties cover some of this.
        widget.config(
            bg=theme_colors.get("btn_bg"), # Specific button background
            activebackground=theme_colors.get("btn_active_bg"), # Specific button active background
            relief=tk.RAISED
        )
    elif widget_type == "Entry":
        widget.config(
            bg=theme_colors.get("entry_bg"),
            insertbackground=theme_colors.get("fg_color") # Cursor color
        )
    elif widget_type == "Listbox":
        widget.config(
            bg=theme_colors.get("listbox_bg"),
            selectbackground=theme_colors.get("select_bg")
        )
    elif widget_type == "Label" or widget_type == "Frame": # No widget-specifics beyond general.
        pass


# Redundant button configuration block removed. The one inside "elif widget_type == 'Button'" is sufficient.
# Ensure no duplication. The previous logic had two blocks for "Button".

    # if widget_type == "Button":
    #     widget.config(
    #         bg=theme_colors.get("btn_bg"),
    #         fg=theme_colors.get("fg_color"), # Ensure fg is also set
            activebackground=theme_colors.get("btn_active_bg"),
            activeforeground=theme_colors.get("fg_color"), # Ensure active fg is also set
            relief=tk.RAISED # Default relief for buttons
        )
    elif widget_type == "Entry":
        widget.config(
            bg=theme_colors.get("entry_bg"),
            insertbackground=theme_colors.get("fg_color") # Cursor color
        )
    elif widget_type == "Listbox":
        widget.config(
            bg=theme_colors.get("listbox_bg"),
            selectbackground=theme_colors.get("select_bg")
        )
    elif widget_type == "Label" or widget_type == "Frame" or widget_type == "Checkbutton":
        # Already handled by general properties for bg and fg
        pass


def apply_theme_to_app(app_root, theme_name: str):
    """
    Applies the specified theme to the entire application.
    Iterates through all widgets and applies theme colors.
    """
    if theme_name not in THEMES:
        print(f"Warning: Theme '{theme_name}' not found. Using default dark theme.")
        theme_colors = THEMES["dark"]
    else:
        theme_colors = THEMES[theme_name]

    # Apply to root window
    app_root.configure(bg=theme_colors.get("bg_color"))

    # Apply to all child widgets
    for widget in app_root.winfo_children():
        apply_recursively(widget, theme_colors)

def apply_recursively(widget, theme_colors: dict):
    """
    Recursively applies theme to a widget and its children.
    """
    apply_theme_to_widget(widget, theme_colors)
    for child in widget.winfo_children():
        apply_recursively(child, theme_colors)

if __name__ == '__main__':
    # Example usage (optional, for testing the module directly)
    import tkinter as tk
    root = tk.Tk()
    root.title("Theme Test")
    root.geometry("300x200")

    # Create some widgets
    tk.Label(root, text="This is a label").pack(pady=5)
    tk.Entry(root).pack(pady=5)
    tk.Button(root, text="Test Button").pack(pady=5)
    tk.Checkbutton(root, text="Test Checkbutton").pack(pady=5)
    listbox = tk.Listbox(root, height=3)
    listbox.insert(tk.END, "Item 1")
    listbox.insert(tk.END, "Item 2")
    listbox.pack(pady=5)

    # Apply a theme
    # apply_theme_to_app(root, "winter")
    # apply_theme_to_app(root, "summer")
    # apply_theme_to_app(root, "autumn")
    # apply_theme_to_app(root, "spring")
    apply_theme_to_app(root, "dark") # Default

    root.mainloop()
