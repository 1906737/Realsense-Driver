import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import threading

def find_esp32_port():
    """Scan all COM ports and try to find the one connected to the ESP32."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Common keywords for ESP32/Arduino serial chips
        desc = port.description.upper()
        if any(kw in desc for kw in ["USB", "UART", "CP210", "CH340"]):
            return port.device
    return None

class GPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 GPS Dashboard")
        self.root.geometry("550x450")
        self.root.configure(bg="#1e1e1e")

        # --- UI STYLING ---
        style = ttk.Style()
        style.configure("TLabel", background="#1e1e1e", foreground="#ecf0f1", font=("Segoe UI", 11))
        
        # --- TOP DISPLAY AREA ---
        self.lbl_status = ttk.Label(root, text="Searching for ESP32...", font=("Segoe UI", 9, "italic"))
        self.lbl_status.pack(pady=10)

        self.lbl_coords = tk.Label(root, text="Lat/Lon: ---", bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 16, "bold"))
        self.lbl_coords.pack(pady=5)

        self.lbl_time = ttk.Label(root, text="📅 Date/Time: ---")
        self.lbl_time.pack(pady=5)

        self.lbl_sats = ttk.Label(root, text="🛰️ Satellites: 0")
        self.lbl_sats.pack(pady=5)

        # --- RAW DATA LOG ---
        ttk.Label(root, text="Raw Serial Feed:", font=("Segoe UI", 9, "bold")).pack(pady=(15, 0))
        self.log_area = scrolledtext.ScrolledText(root, width=60, height=10, bg="#2d2d2d", fg="#888", font=("Consolas", 9))
        self.log_area.pack(pady=10, padx=10)

        # --- SERIAL THREADING ---
        self.port = find_esp32_port()
        self.running = True
        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.thread.start()

    def update_ui(self, line):
        """Parses the GPS string and updates the GUI elements."""
        # Log the raw line to the text box
        self.log_area.insert(tk.END, line + "\n")
        self.log_area.see(tk.END)

        try:
            # Check for the expected keywords in your string
            if "Location:" in line and "Satellites:" in line:
                # Splitting logic based on your specific format
                # Location: [data] Date/Time: [data] Satellites: [data]
                parts = line.split("Date/Time:")
                loc_section = parts[0].replace("Location:", "").strip()
                
                parts2 = parts[1].split("Satellites:")
                time_section = parts2[0].strip()
                sat_section = parts2[1].strip()

                # Update UI Colors based on GPS Lock
                if "INVALID" in loc_section:
                    self.lbl_coords.config(text=f"Location: {loc_section}", fg="#e74c3c")
                else:
                    self.lbl_coords.config(text=f"Location: {loc_section}", fg="#2ecc71")

                self.lbl_time.config(text=f"📅 {time_section}")
                self.lbl_sats.config(text=f"🛰️ Satellites: {sat_section}")
                self.lbl_status.config(text=f"Connected on {self.port}", foreground="#3498db")
        except Exception:
            # Silently ignore parsing errors for malformed lines
            pass

    def read_serial(self):
        """Background thread to read data from the serial port."""
        if not self.port:
            self.root.after(0, lambda: self.lbl_status.config(text="Error: ESP32 not found! Plug it in and restart.", foreground="red"))
            return

        try:
            # Open port (ensure 9600 matches your Serial.begin)
            with serial.Serial(self.port, 115200, timeout=1) as ser:
                while self.running:
                    if ser.in_waiting > 0:
                        raw_data = ser.readline()
                        try:
                            line = raw_data.decode('utf-8').strip()
                            if line:
                                self.root.after(0, self.update_ui, line)
                        except UnicodeDecodeError:
                            pass # Skip lines with garbage characters
        except Exception as e:
            # Pass 'e' as a default argument to the lambda to avoid NameError
            self.root.after(0, lambda err=e: self.lbl_status.config(text=f"Serial Error: {err}", foreground="red"))

if __name__ == "__main__":
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()
