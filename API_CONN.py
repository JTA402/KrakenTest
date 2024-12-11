import tkinter as tk
from tkinter import messagebox
import requests
import time
import hashlib
import hmac
import base64
import json
import os

import urllib

# File to store the API keys
API_KEYS_FILE = "api_keys.json"

def save_api_keys_to_file(api_key, api_secret):
    """Save API keys to a file."""
    try:
        with open(API_KEYS_FILE, "w") as file:
            json.dump({"api_key": api_key, "api_secret": api_secret}, file)
        print("API keys saved successfully.")
    except Exception as e:
        print(f"Error saving API keys: {e}")

def load_api_keys_from_file():
    """Load API keys from a file."""
    if not os.path.exists(API_KEYS_FILE):
        return None, None
    try:
        with open(API_KEYS_FILE, "r") as file:
            keys = json.load(file)
            return keys.get("api_key"), keys.get("api_secret")
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return None, None

def generate_kraken_signature(urlpath, data, secret):
    """Generate Kraken API signature."""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def test_kraken_connection():
    """Test connection to Kraken API and return the USD balance."""
    api_key, api_secret = load_api_keys_from_file()
    if not api_key or not api_secret:
        messagebox.showerror("Error", "API keys are not set.")
        return False, None

    url = "https://api.kraken.com/0/private/Balance"
    data = {
        "nonce": str(int(time.time() * 1000))
    }
    headers = {
        "API-Key": api_key,
        "API-Sign": generate_kraken_signature("/0/private/Balance", data, api_secret)
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response_json = response.json()
        if response.status_code == 200 and not response_json.get("error"):
            usd_balance = response_json.get("result", {}).get("ZUSD", "0.0")
            print(f"Connection to Kraken API successful. USD Balance: {usd_balance}")
            return True, usd_balance
        else:
            print(f"Connection failed: {response_json.get('error')}")
            return False, None
    except Exception as e:
        print(f"An error occurred while testing the connection: {str(e)}")
        return False, None


def api_connection_window():
    """GUI to input API keys."""
    def save_keys():
        public_key = public_key_entry.get()
        secret_key = secret_key_entry.get()
        if public_key and secret_key:
            save_api_keys_to_file(public_key, secret_key)
            messagebox.showinfo("Success", "API keys saved successfully.")
            popup.destroy()
        else:
            messagebox.showerror("Error", "Both fields must be filled out.")

    def cancel():
        popup.destroy()

    # Create the popup window
    popup = tk.Toplevel()
    popup.title("API Connection")
    popup.geometry("400x200")
    popup.resizable(False, False)  # Disable resizing

    # Center the window
    window_width = 400
    window_height = 200
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x_position = int((screen_width / 2) - (window_width / 2))
    y_position = int((screen_height / 2) - (window_height / 2))
    popup.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Public Key field
    tk.Label(popup, text="Public Key:").pack(pady=5)
    public_key_entry = tk.Entry(popup, width=50)
    public_key_entry.pack(pady=5)

    # Secret Key field
    tk.Label(popup, text="Secret Key:").pack(pady=5)
    secret_key_entry = tk.Entry(popup, width=50, show="*")  # Mask input for Secret Key
    secret_key_entry.pack(pady=5)

    # Save and Cancel buttons
    button_frame = tk.Frame(popup)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Save", command=save_keys, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

    popup.transient()  # Keep the window on top of the main app
    popup.grab_set()  # Make the popup modal
    popup.mainloop()

if __name__ == "__main__":
    # Test the GUI and connection testing functionality
    print("API Connection Module")
    print("---------------------")
    print("1. Open API Connection GUI")
    print("2. Test Connection")
    choice = input("Enter your choice: ")
    if choice == "1":
        api_connection_window()
    elif choice == "2":
        if test_kraken_connection():
            print("Connection is valid.")
        else:
            print("Connection failed.")
