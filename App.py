# App.py
import tkinter as tk
from tkinter import ttk
from Invoice import InvoiceFrame
from Inventory import InventoryFrame
from Company import CompanyFrame
import database

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Global style configuration for larger, touch/click-friendly dropdowns
        style = ttk.Style()
        style.theme_use('clam')  # Ensures custom styles render reliably across operating systems
        style.configure('TCombobox', 
                        padding=6, 
                        fieldbackground="#FDFCFA", 
                        background="#D5C9BB", 
                        font=("Segoe UI", 10))
        style.map('TCombobox', fieldbackground=[('readonly', '#FDFCFA')])

        # Load company profile to set dynamic window title
        profile = database.get_company_profile() or {}
        company_name = profile.get("name", "Example Furniture").strip()
        
        self.title(f"{company_name} — ERP & Invoice Suite")
        self.geometry("1150x700")
        self.minsize(1050, 620)
        self.configure(bg="#ECE4DA")

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_nav_tabs()
        
        # Container for changing frames
        self.container = tk.Frame(self, bg="#ECE4DA")
        self.container.grid(row=2, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self._init_frames()
        
        # Change default landing page to Inventory.py (InventoryFrame)
        self.show_frame("InventoryFrame")

    def _build_topbar(self):
        bar = tk.Frame(self, bg="#3E2723", height=48)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(5, weight=1)

        profile = database.get_company_profile() or {}
        company_name = profile.get("name", "EXAMPLE FURNITURE").strip().upper()

        tk.Label(bar, text="🪑", bg="#3E2723", fg="#C8956C", font=("Segoe UI", 16)).grid(row=0, column=0, padx=(16, 6))
        
        # Keep reference to update later if profile changes
        self.topbar_title_lbl = tk.Label(bar, text=company_name, bg="#3E2723", fg="#C8956C", font=("Segoe UI", 14, "bold"))
        self.topbar_title_lbl.grid(row=0, column=1, sticky="w")
        
        tk.Frame(bar, bg="#5D4037", width=1).grid(row=0, column=2, sticky="ns", padx=12, pady=8)
        tk.Label(bar, text="ERP Suite", bg="#3E2723", fg="#C4B5A5", font=("Segoe UI", 9)).grid(row=0, column=3, sticky="w")
        
        self.topbar_status = tk.Label(bar, text="● DRAFT", bg="#3E2723", fg="#FDCB6E", font=("Segoe UI", 9, "bold"))
        self.topbar_status.grid(row=0, column=6, padx=16)

    def _build_nav_tabs(self):
        nav_bar = tk.Frame(self, bg="#5D4037", height=38)
        nav_bar.grid(row=1, column=0, sticky="ew")
        nav_bar.grid_propagate(False)
        
        # Global Navigation Tabs available across pages
        tk.Button(nav_bar, text=" 📦 Inventory Catalog ", command=lambda: self.show_frame("InventoryFrame"), bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, cursor="hand2").pack(side="left", padx=2, pady=4)
        tk.Button(nav_bar, text=" 🧾 Invoice Generator ", command=lambda: self.show_frame("InvoiceFrame"), bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, cursor="hand2").pack(side="left", padx=2, pady=4)
        tk.Button(nav_bar, text=" 🏢 Company & Clients ", command=lambda: self.show_frame("CompanyFrame"), bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, cursor="hand2").pack(side="left", padx=2, pady=4)

    def _init_frames(self):
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        frame_classes = {
            "InvoiceFrame": lambda parent: InvoiceFrame(parent, self.topbar_status),
            "InventoryFrame": InventoryFrame,
            "CompanyFrame": CompanyFrame
        }

        for name, FClass in frame_classes.items():
            frame = FClass(self.container)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, page_name):
        # Refresh top bar title dynamically every time a frame is raised/switched
        profile = database.get_company_profile() or {}
        company_name = profile.get("name", "EXAMPLE FURNITURE").strip().upper()
        if company_name:
            self.topbar_title_lbl.config(text=company_name)
            self.title(f"{profile.get('name', 'Example Furniture')} — ERP & Invoice Suite")

        frame = self.frames[page_name]
        
        # Refresh dynamic catalog values and dropdowns when switching back to Invoice view
        if page_name == "InvoiceFrame":
            if hasattr(frame, "catalog"):
                frame.catalog = database.get_catalog()
                if hasattr(frame, "cat_cb"):
                    frame.cat_cb["values"] = ["(custom item)"] + list(frame.catalog.keys())
            
            if hasattr(frame, "cust_cb"):
                clients = database.get_clients()
                client_names = [cl["name"] for cl in clients]
                frame.cust_cb.set_full_values(client_names)

        frame.tkraise()

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()