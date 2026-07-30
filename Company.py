# Company.py
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import database

class CompanyFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ECE4DA")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        os.makedirs("assets", exist_ok=True)
        self.logo_path_var = tk.StringVar()

        self._build_header()
        self._build_content()
        self.load_company_profile()
        self.load_clients()

    def _build_header(self):
        self.header_frame = tk.Frame(self, bg="#FAF6F0", height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.header_frame.grid_propagate(False)

        self.header_label = tk.Label(
            self.header_frame, 
            text="🏢 Company Profile & Directory", 
            bg="#FAF6F0", 
            fg="#3E2723", 
            font=("Segoe UI", 14, "bold")
        )
        self.header_label.pack(side="left", padx=16, pady=14)

    def _build_content(self):
        content_frame = tk.Frame(self, bg="#ECE4DA")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # Left Panel: Company Settings Form
        self.company_panel = tk.LabelFrame(content_frame, text=" Company Profile Settings ", bg="#FAF6F0", fg="#3E2723", font=("Segoe UI", 10, "bold"), padx=16, pady=16)
        self.company_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.company_panel.grid_rowconfigure(5, weight=1)
        self.company_panel.grid_columnconfigure(0, weight=1)

        self._build_form()

        # Right Panel: Client List / Directory with Add/Delete Feature
        client_panel = tk.LabelFrame(content_frame, text=" Saved Clients Directory ", bg="#FAF6F0", fg="#3E2723", font=("Segoe UI", 10, "bold"), padx=16, pady=16)
        client_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        client_panel.grid_rowconfigure(0, weight=1)
        client_panel.grid_columnconfigure(0, weight=1)

        columns = ("name", "company", "phone", "email")
        self.client_tree = ttk.Treeview(client_panel, columns=columns, show="headings", selectmode="browse")
        self.client_tree.heading("name", text="Client Name")
        self.client_tree.heading("company", text="Company")
        self.client_tree.heading("phone", text="Phone")
        self.client_tree.heading("email", text="Email")

        self.client_tree.column("name", width=120, anchor="w")
        self.client_tree.column("company", width=120, anchor="w")
        self.client_tree.column("phone", width=100, anchor="center")
        self.client_tree.column("email", width=140, anchor="w")

        client_scroll = ttk.Scrollbar(client_panel, orient="vertical", command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=client_scroll.set)

        self.client_tree.grid(row=0, column=0, sticky="nsew", columnspan=2)
        client_scroll.grid(row=0, column=2, sticky="ns")

        client_btn_frame = tk.Frame(client_panel, bg="#FAF6F0")
        client_btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        tk.Button(
            client_btn_frame, text="+ Add Client", command=self.open_client_dialog,
            bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left")

        tk.Button(
            client_btn_frame, text="🗑 Delete Client", command=self.delete_client,
            bg="#A93226", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="right")

    def _build_form(self):
        for widget in self.company_panel.winfo_children():
            widget.destroy()

        profile = database.get_company_profile() or {}
        fields = [
            ("Company Name:", "name"), 
            ("Tagline:", "tagline"), 
            ("Phone:", "phone"), 
            ("Company Gmail:", "email"), 
            ("Website:", "website"), 
            ("Address:", "address")
        ]
        
        form_inner = tk.Frame(self.company_panel, bg="#FAF6F0")
        form_inner.pack(fill="both", expand=True)

        self.entries = {}

        for idx, (label_text, key) in enumerate(fields):
            tk.Label(form_inner, text=label_text, bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).grid(row=idx*2, column=0, sticky="w", pady=(4, 2))
            ent = tk.Entry(form_inner, font=("Segoe UI", 10), width=36)
            ent.insert(0, str(profile.get(key, "")))
            ent.grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 6))
            self.entries[key] = ent

        # Custom Logo Upload Field
        logo_row = len(fields) * 2
        tk.Label(form_inner, text="Company Logo:", bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).grid(row=logo_row, column=0, sticky="w", pady=(4, 2))
        
        logo_frame = tk.Frame(form_inner, bg="#FAF6F0")
        logo_frame.grid(row=logo_row+1, column=0, sticky="ew", pady=(0, 6))

        tk.Button(
            logo_frame, text="Browse Logo...", command=self.browse_logo,
            font=("Segoe UI", 9), bg="#E2E8F0", fg="#0F172A", relief="flat", padx=8, pady=4, cursor="hand2"
        ).pack(side="left")

        saved_logo = profile.get("logo_path", "")
        self.logo_path_var.set(saved_logo)
        init_preview_text = f"Loaded: {os.path.basename(saved_logo)}" if saved_logo and os.path.exists(saved_logo) else "No logo selected"
        
        self.logo_preview_lbl = tk.Label(logo_frame, text=init_preview_text, font=("Segoe UI", 8, "italic"), bg="#FAF6F0", fg="#7D6B5D")
        self.logo_preview_lbl.pack(side="left", padx=10)

        btn_row = tk.Frame(form_inner, bg="#FAF6F0")
        btn_row.grid(row=logo_row+2, column=0, sticky="ew", pady=10)

        tk.Button(
            btn_row, text="💾 Save Changes", command=self.save_company_profile, 
            bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left")

    def browse_logo(self):
        file_path = ""
        try:
            import subprocess
            result = subprocess.run(
                ["zenity", "--file-selection", "--title=Select Company Logo", 
                 "--file-filter=Image files (png jpg jpeg bmp) | *.png *.jpg *.jpeg *.bmp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                file_path = result.stdout.strip()
        except Exception:
            pass

        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Company Logo",
                initialdir=os.path.expanduser("~"),
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")]
            )

        if file_path:
            try:
                target_size = (120, 120)
                im = Image.open(file_path)
                im.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                saved_logo_path = os.path.join("assets", "company_logo.png")
                im.save(saved_logo_path, "PNG")
                
                self.logo_path_var.set(saved_logo_path)
                self.logo_preview_lbl.config(text=f"Loaded: {os.path.basename(file_path)}", fg="#2D6A4F")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process image: {e}")

    def load_company_profile(self):
        profile = database.get_company_profile() or {}
        company_name = profile.get("name", "").strip()
        if company_name:
            self.header_label.config(text=f"🏢 {company_name} - Profile & Directory")
            try:
                top_level_window = self.winfo_toplevel()
                top_level_window.title(f"{company_name} — ERP & Invoice Suite")
                if hasattr(top_level_window, "topbar_title_lbl"):
                    top_level_window.topbar_title_lbl.config(text=company_name.upper())
            except Exception:
                pass
        else:
            self.header_label.config(text="🏢 Company Profile & Directory")

    def load_clients(self):
        for row in self.client_tree.get_children():
            self.client_tree.delete(row)
        for client in database.get_clients():
            self.client_tree.insert("", "end", values=(
                client.get("name", ""),
                client.get("company", ""),
                client.get("phone", ""),
                client.get("email", "")
            ))

    def save_company_profile(self):
        try:
            profile = database.get_company_profile() or {}
            profile.update({
                "name": self.entries["name"].get().strip(),
                "tagline": self.entries["tagline"].get().strip(),
                "phone": self.entries["phone"].get().strip(),
                "email": self.entries["email"].get().strip(),
                "website": self.entries["website"].get().strip(),
                "address": self.entries["address"].get().strip(),
                "logo_path": self.logo_path_var.get().strip(),
            })
            database.save_company_profile(profile)
            self.load_company_profile()
            messagebox.showinfo("Success", "Company profile details updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

    def open_client_dialog(self):
        ClientDialog(self, on_save=self.save_new_client)

    def save_new_client(self, client_data):
        try:
            clients = database.get_clients()
            clients.append(client_data)
            database.save_clients(clients)
            self.load_clients()
            messagebox.showinfo("Success", "New client added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save client: {e}")

    def delete_client(self):
        selected = self.client_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select a client to delete.")
            return
        
        item_values = self.client_tree.item(selected[0])['values']
        client_name = item_values[0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete client '{client_name}'?"):
            try:
                clients = [c for c in database.get_clients() if c.get("name") != client_name]
                database.save_clients(clients)
                self.load_clients()
                messagebox.showinfo("Success", "Client deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete client: {e}")


class ClientDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Add New Client")
        self.geometry("360x440")
        self.configure(bg="#FAF6F0")
        self.resizable(False, False)
        self.on_save = on_save

        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="Add New Client Directory", bg="#FAF6F0", fg="#3E2723", font=("Segoe UI", 12, "bold")).pack(pady=12)

        form_frame = tk.Frame(self, bg="#FAF6F0", padx=20)
        form_frame.pack(fill="both", expand=True)

        fields = [("Client Name:", "name"), ("Company:", "company"), ("Phone:", "phone"), ("Email:", "email"), ("Address:", "address"), ("City/ST/ZIP:", "city")]
        self.ent_dict = {}

        for idx, (lbl, key) in enumerate(fields):
            tk.Label(form_frame, text=lbl, bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).pack(anchor="w")
            ent = tk.Entry(form_frame, font=("Segoe UI", 10), width=30)
            ent.pack(fill="x", pady=(2, 6))
            ent.bind("<Return>", lambda e: self.validate_and_save())
            self.ent_dict[key] = ent

        btn_frame = tk.Frame(self, bg="#FAF6F0")
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))

        tk.Button(
            btn_frame, text="Cancel", command=self.destroy,
            bg="#BDC3C7", fg="#2C3E50", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left")

        tk.Button(
            btn_frame, text="Save Changes" if hasattr(self, 'on_save') else "Save Client", command=self.validate_and_save,
            bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="right")

    def validate_and_save(self):
        data = {k: v.get().strip() for k, v in self.ent_dict.items()}
        if not data["name"]:
            messagebox.showerror("Validation Error", "Client name cannot be empty.", parent=self)
            return
        if self.on_save:
            self.on_save(data)
        self.destroy()