# Inventory.py
import tkinter as tk
from tkinter import ttk, messagebox
import database

class InventoryFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ECE4DA")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_content()
        self.load_data()

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#FAF6F0", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header_frame.grid_propagate(False)

        tk.Label(
            header_frame, 
            text="📦 Inventory & Catalog Management", 
            bg="#FAF6F0", 
            fg="#3E2723", 
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=16, pady=14)

        # Action Buttons
        tk.Button(
            header_frame, 
            text="🗑 Delete Item", 
            command=self.delete_item, 
            bg="#A93226", 
            fg="white", 
            font=("Segoe UI", 9, "bold"), 
            relief="flat", 
            padx=12, 
            pady=6, 
            cursor="hand2"
        ).pack(side="right", padx=6, pady=12)

        tk.Button(
            header_frame, 
            text="✏ Edit Item", 
            command=self.open_edit_dialog, 
            bg="#D4AC0D", 
            fg="#3E2723", 
            font=("Segoe UI", 9, "bold"), 
            relief="flat", 
            padx=12, 
            pady=6, 
            cursor="hand2"
        ).pack(side="right", padx=6, pady=12)

        tk.Button(
            header_frame, 
            text="+ Add Item", 
            command=self.open_add_dialog, 
            bg="#3E2723", 
            fg="white", 
            font=("Segoe UI", 9, "bold"), 
            relief="flat", 
            padx=12, 
            pady=6, 
            cursor="hand2"
        ).pack(side="right", padx=6, pady=12)

    def _build_content(self):
        content_frame = tk.Frame(self, bg="#ECE4DA")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        columns = ("id", "name", "category", "price", "stock")
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Item Name / Description")
        self.tree.heading("category", text="Category")
        self.tree.heading("price", text="Unit Price (₹)")
        self.tree.heading("stock", text="Stock Qty")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=350, anchor="w")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("price", width=120, anchor="e")
        self.tree.column("stock", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", lambda e: self.open_edit_dialog())

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        try:
            catalog = database.get_catalog()
            # Handle both dictionary formats and nested category tuples/lists structure from database.py
            if isinstance(catalog, dict):
                row_id = 1
                for category, items in catalog.items():
                    for item in items:
                        # item can be a tuple like (name, price) or dict
                        if isinstance(item, (list, tuple)):
                            name, price = item[0], item[1]
                            self.tree.insert("", "end", values=(
                                row_id, name, category, f"{float(price):.2f}", 0
                            ))
                        elif isinstance(item, dict):
                            self.tree.insert("", "end", values=(
                                item.get("id", row_id),
                                item.get("name", ""),
                                item.get("category", category),
                                f"{float(item.get('price', 0.0)):.2f}",
                                item.get("stock", 0)
                            ))
                        row_id += 1
            elif isinstance(catalog, list):
                for item in catalog:
                    if isinstance(item, dict):
                        self.tree.insert("", "end", values=(
                            item.get("id", ""),
                            item.get("name", ""),
                            item.get("category", "General"),
                            f"{float(item.get('price', 0.0)):.2f}",
                            item.get("stock", 0)
                        ))
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load inventory: {e}")

    def open_add_dialog(self):
        ItemFormDialog(self, title="Add Inventory Item", on_save=self.save_new_item)

    def open_edit_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item to edit.")
            return
        
        item_values = self.tree.item(selected[0])['values']
        item_data = {
            "id": item_values[0],
            "name": item_values[1],
            "category": item_values[2],
            "price": item_values[3],
            "stock": item_values[4]
        }
        ItemFormDialog(self, title="Edit Inventory Item", initial_data=item_data, on_save=lambda data: self.update_item(item_data["id"], data))

    def save_new_item(self, data):
        try:
            catalog = database.get_catalog()
            if isinstance(catalog, dict):
                cat = data["category"]
                if cat not in catalog:
                    catalog[cat] = []
                catalog[cat].append((data["name"], data["price"]))
                database.save_catalog(catalog)
            self.load_data()
            messagebox.showinfo("Success", "Item added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save item: {e}")

    def update_item(self, item_id, data):
        try:
            catalog = database.get_catalog()
            if isinstance(catalog, dict):
                # Rebuild or update matching item
                found = False
                for cat, items in catalog.items():
                    for idx, item in enumerate(items):
                        if isinstance(item, (list, tuple)) and item[0] == data["name"]:
                            items[idx] = (data["name"], data["price"])
                            found = True
                            break
                    if found:
                        break
                database.save_catalog(catalog)
            self.load_data()
            messagebox.showinfo("Success", "Item updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update item: {e}")

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item to delete.")
            return
        
        item_values = self.tree.item(selected[0])['values']
        item_name = item_values[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item_name}'?"):
            try:
                catalog = database.get_catalog()
                if isinstance(catalog, dict):
                    for cat, items in catalog.items():
                        catalog[cat] = [item for item in items if not (isinstance(item, (list, tuple)) and item[0] == item_name)]
                    database.save_catalog(catalog)
                self.load_data()
                messagebox.showinfo("Success", "Item deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete item: {e}")


class ItemFormDialog(tk.Toplevel):
    def __init__(self, parent, title, initial_data=None, on_save=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x420")
        self.configure(bg="#FAF6F0")
        self.resizable(False, False)
        self.on_save = on_save

        # Make window modal
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=title, bg="#FAF6F0", fg="#3E2723", font=("Segoe UI", 12, "bold")).pack(pady=14)

        form_frame = tk.Frame(self, bg="#FAF6F0", padx=20)
        form_frame.pack(fill="both", expand=True)

        # Fields
        tk.Label(form_frame, text="Item Name / Description:", bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).pack(anchor="w")
        self.name_ent = tk.Entry(form_frame, font=("Segoe UI", 10), width=32)
        self.name_ent.pack(fill="x", pady=(2, 10))

        tk.Label(form_frame, text="Category:", bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).pack(anchor="w")
        self.cat_ent = tk.Entry(form_frame, font=("Segoe UI", 10), width=32)
        self.cat_ent.pack(fill="x", pady=(2, 10))

        tk.Label(form_frame, text="Unit Price (₹):", bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).pack(anchor="w")
        self.price_ent = tk.Entry(form_frame, font=("Segoe UI", 10), width=32)
        self.price_ent.pack(fill="x", pady=(2, 10))

        tk.Label(form_frame, text="Stock Quantity:", bg="#FAF6F0", fg="#5D4037", font=("Segoe UI", 9)).pack(anchor="w")
        self.stock_ent = tk.Entry(form_frame, font=("Segoe UI", 10), width=32)
        self.stock_ent.pack(fill="x", pady=(2, 16))

        if initial_data:
            self.name_ent.insert(0, str(initial_data.get("name", "")))
            self.cat_ent.insert(0, str(initial_data.get("category", "")))
            self.price_ent.insert(0, str(initial_data.get("price", "0.00")).replace("₹", "").strip())
            self.stock_ent.insert(0, str(initial_data.get("stock", "0")))

        # Buttons
        btn_frame = tk.Frame(self, bg="#FAF6F0")
        btn_frame.pack(fill="x", padx=20, pady=15)

        tk.Button(
            btn_frame, text="Cancel", command=self.destroy, 
            bg="#BDC3C7", fg="#2C3E50", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6
        ).pack(side="left")

        tk.Button(
            btn_frame, text="Save Item", command=self.validate_and_save, 
            bg="#3E2723", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6
        ).pack(side="right")

    def validate_and_save(self):
        name = self.name_ent.get().strip()
        category = self.cat_ent.get().strip()
        price_str = self.price_ent.get().strip()
        stock_str = self.stock_ent.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Item name cannot be empty.", parent=self)
            return

        try:
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid numeric price.", parent=self)
            return

        try:
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid whole number for stock quantity.", parent=self)
            return

        data = {
            "name": name,
            "category": category if category else "General",
            "price": price,
            "stock": stock
        }

        if self.on_save:
            self.on_save(data)
        self.destroy()