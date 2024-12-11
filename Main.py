import tkinter as tk
from tkinter import messagebox
import API_CONN  # Ensure API_CONN.py is in the same directory

# Global variable to track connection state
is_connected = False

# Function to update the connection status bar
def update_status(new_status):
    status_var.set(f"Status: {new_status}")
    color = {"Online": "green", "Offline": "red", "Error": "orange"}.get(new_status, "black")
    status_label.config(fg=color)

# Function to update the balance display
def update_balance(balance):
    balance_var.set(f"Balance: ${balance}")

# Define menu functions
def connect():
    """Simulate connecting to Kraken API."""
    global is_connected
    result, balance = API_CONN.test_kraken_connection()
    if result:
        is_connected = True
        update_status("Online")
        update_balance(balance)
        messagebox.showinfo("Connect", "Successfully connected to Kraken.")
    else:
        update_status("Error")
        messagebox.showerror("Connect", "Failed to connect to Kraken. Check your API keys.")

def disconnect():
    """Simulate disconnecting from Kraken API."""
    global is_connected
    if is_connected:
        is_connected = False
        update_status("Offline")
        update_balance("0.00")  # Clear the balance display on disconnect
        messagebox.showinfo("Disconnect", "Successfully disconnected from Kraken.")
    else:
        messagebox.showwarning("Disconnect", "You are already disconnected.")

def test_connection():
    """Test the connection using the stored API keys."""
    if not is_connected:
        messagebox.showwarning("Test Connection", "Please connect before testing the connection.")
        return
    result, balance = API_CONN.test_kraken_connection()
    if result:
        update_status("Online")
        update_balance(balance)
        messagebox.showinfo("Test Connection", "Connection to Kraken API is valid.")
    else:
        update_status("Error")
        messagebox.showerror("Test Connection", "Failed to connect to Kraken. Check your API keys.")

def api_connection():
    API_CONN.api_connection_window()

def trading_pairs():
    print("Trading Pairs settings.")  # Placeholder for trading pairs functionality

def documentation():
    print("Opening documentation.")  # Placeholder for documentation functionality

def about():
    messagebox.showinfo("About", "Unleash the Kraken v1.0\nDeveloped by [Your Name]")

# Initialize the main window
root = tk.Tk()
root.title("Unleash the Kraken")
root.geometry("800x600")

# Create a menu bar
menubar = tk.Menu(root)

# File menu
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Connect", command=connect)
file_menu.add_command(label="Disconnect", command=disconnect)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

# Settings menu
settings_menu = tk.Menu(menubar, tearoff=0)
settings_menu.add_command(label="API Connection", command=api_connection)
settings_menu.add_command(label="Trading Pairs", command=trading_pairs)
settings_menu.add_command(label="Test Connection", command=test_connection)
menubar.add_cascade(label="Settings", menu=settings_menu)

# Help menu
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="Documentation", command=documentation)
help_menu.add_command(label="About", command=about)
menubar.add_cascade(label="Help", menu=help_menu)

# Configure the menu bar
root.config(menu=menubar)

# Create a status bar with two labels
status_frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Balance display (left-aligned)
balance_var = tk.StringVar()
balance_var.set("Balance: $0.00")  # Default balance
balance_label = tk.Label(status_frame, textvariable=balance_var, anchor=tk.W, padx=10)
balance_label.pack(side=tk.LEFT)

# Connection status (right-aligned)
status_var = tk.StringVar()
status_var.set("Status: Offline")  # Default status
status_label = tk.Label(status_frame, textvariable=status_var, anchor=tk.E, padx=10)
status_label.pack(side=tk.RIGHT)

# Start the main loop
root.mainloop()
