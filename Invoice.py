# Invoice.py
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import database

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable, Image as RLImage
    )
    from reportlab.graphics.shapes import Drawing, Rect
    from PIL import Image
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

_S = platform.system()
FF = "Helvetica Neue" if _S == "Darwin" else "Segoe UI" if _S == "Windows" else "Ubuntu"

PRIMARY     = "#3E2723"
PRIMARY_LT  = "#5D4037"
ACCENT      = "#C8956C"
ACCENT_LT   = "#E8D5C0"
BG          = "#ECE4DA"
CARD        = "#FFFFFF"
TEXT        = "#2C1810"
TEXT_MUTED  = "#7D6B5D"
BORDER      = "#D5C9BB"
ENTRY_BG    = "#FDFCFA"
SUCCESS     = "#2D6A4F"
DANGER      = "#9B2226"
TABLE_HEAD  = "#3E2723"
TABLE_ALT   = "#FAF7F4"
HOVER_BG    = "#F3EBE1"
STATUS_MAP  = {"Draft": "#FDCB6E", "Sent": "#74B9FF",
               "Paid": "#00B894", "Overdue": "#FF6B6B", "Cancelled": "#B2BEC3"}

ICON_INVOICE  = "🧾"
ICON_BILLTO   = "👤"
ICON_ADDITEM  = "➕"
ICON_ITEMS    = "📄"
ICON_SUMMARY  = "🧮"

F_BRAND  = (FF, 14, "bold")
F_HEAD   = (FF, 10, "bold")
F_LABEL  = (FF, 9)
F_ENTRY  = (FF, 10)
F_SMALL  = (FF, 8)
F_BTN    = (FF, 10, "bold")
F_TOTAL  = (FF, 13, "bold")
F_STATUS = (FF, 9, "bold")

PAD_X      = 8
PAD_Y      = 4
PAD_OUTER  = 12
ENT_PAD_R  = 8
ENT_IPADY  = 3

DEFAULT_NOTES = (
    "Thank you for choosing Example Furniture!\n"
    "All furniture comes with a 2-year warranty against manufacturing defects.\n"
    "Delivery: 7-14 business days (in-stock) / 4-6 weeks (custom orders).\n\n"
    "Payment: Bank transfer, credit card, or financing options available."
)

def fmt(amount):
    return f"₹{amount:,.2f}"

class ACCombobox(ttk.Combobox):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._full = list(kw.get("values", []))
        self.bind("<KeyRelease>", self._filter)
        self.bind("<FocusOut>", lambda e: self.configure(values=self._full))

    def set_full_values(self, v):
        self._full = list(v)
        self["values"] = self._full

    def _filter(self, _=None):
        t = self.get().strip().lower()
        self["values"] = [x for x in self._full if t in x.lower()] if t else self._full


class InvoiceFrame(tk.Frame):
    def _card(self, parent, icon, title, **gk):
        outer = tk.Frame(parent, bg=BORDER, highlightthickness=0)
        gk.setdefault("sticky", "nsew")
        outer.grid(**gk)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        tk.Frame(outer, bg=ACCENT, height=2).grid(row=0, column=0, sticky="ew")
        inner = tk.Frame(outer, bg=CARD)
        inner.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))

        head = tk.Frame(inner, bg=CARD)
        head.grid(row=0, column=0, columnspan=21, sticky="w", padx=PAD_OUTER, pady=(8, 4))
        tk.Label(head, text=icon, bg=CARD, fg=ACCENT, font=(FF, 11)).pack(side="left", padx=(0, 6))
        tk.Label(head, text=title, bg=CARD, fg=PRIMARY, font=F_HEAD, anchor="w").pack(side="left")
        return inner

    def _lbl(self, parent, text, row, col=0):
        l = tk.Label(parent, text=text, bg=CARD, fg=TEXT_MUTED, font=F_LABEL, anchor="e", width=11)
        l.grid(row=row, column=col, sticky="e", padx=(0, PAD_X), pady=PAD_Y)
        return l

    def _ent(self, parent, var, row, col=1, **kw):
        border = tk.Frame(parent, bg=BORDER)
        border.grid(row=row, column=col, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, **kw)
        e = tk.Entry(border, textvariable=var, font=F_ENTRY, bg=ENTRY_BG, fg=TEXT, relief="flat", bd=2, insertbackground=TEXT)
        e.pack(fill="both", expand=True, ipady=ENT_IPADY)
        e.bind("<FocusIn>", lambda _, f=border: f.configure(bg=ACCENT))
        e.bind("<FocusOut>", lambda _, f=border: f.configure(bg=BORDER))
        return e

    def _btn(self, parent, text, cmd, style="primary", **gk):
        palette = {
            "primary": (ACCENT, PRIMARY_LT, TEXT),
            "success": (SUCCESS, "#1B4332", CARD),
            "danger":  (DANGER, "#641220", CARD),
            "ghost":   (CARD, HOVER_BG, TEXT),
        }
        bg_c, abg_c, fg_c = palette.get(style, palette["primary"])
        b = tk.Button(parent, text=text, command=cmd, font=F_BTN, bg=bg_c, fg=fg_c, activebackground=abg_c, activeforeground=fg_c, relief="flat", bd=0, padx=16, pady=6, cursor="hand2")
        b.bind("<Enter>", lambda _, btn=b, c=abg_c: btn.configure(bg=c))
        b.bind("<Leave>", lambda _, btn=b, c=bg_c: btn.configure(bg=c))
        gk.setdefault("sticky", "e")
        b.grid(**gk)
        return b

    def __init__(self, parent, topbar_status_label, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(bg=BG)
        self.topbar_status = topbar_status_label
        
        self.items = []
        self.invoice_counter = database.load_counter()
        self.catalog = database.get_catalog()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = tk.Frame(self, bg=BG)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)

        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._build_main(container)
        self._refresh_table()
        self._recalc()

    def _build_main(self, m):
        top = tk.Frame(m, bg=BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)
        self._build_inv_details(top)
        self._build_customer(top)

        self._build_item_entry(m)

        mid = tk.Frame(m, bg=BG)
        mid.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=65)
        mid.grid_columnconfigure(1, weight=35, minsize=340)
        self._build_items_table(mid)
        self._build_summary(mid)

        self._build_buttons(m)

    def _build_inv_details(self, parent):
        c = self._card(parent, ICON_INVOICE, "INVOICE DETAILS", row=0, column=0, sticky="nsew", padx=(0, 4))
        c.grid_columnconfigure(1, weight=1)
        c.grid_columnconfigure(3, weight=1)

        self.inv_no_var = tk.StringVar(value=f"EF-{self.invoice_counter:05d}")
        self._lbl(c, "Invoice No:", 1, 0)
        self._ent(c, self.inv_no_var, 1, 1)

        self.inv_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self._lbl(c, "Date:", 1, 2)
        self._ent(c, self.inv_date_var, 1, 3)

        self.due_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
        self._lbl(c, "Due Date:", 2, 0)
        self._ent(c, self.due_date_var, 2, 1)

        self.sales_var = tk.StringVar()
        self._lbl(c, "Salesperson:", 2, 2)
        self._ent(c, self.sales_var, 2, 3)

        self.terms_var = tk.StringVar(value="Net 30")
        self._lbl(c, "Terms:", 3, 0)
        cb = ttk.Combobox(c, textvariable=self.terms_var, values=["Due on Receipt", "Net 15", "Net 30", "Net 60", "50% Adv, 50% Delivery"], state="readonly")
        cb.grid(row=3, column=1, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, ipady=ENT_IPADY)

        self.status_var = tk.StringVar(value="Draft")
        self._lbl(c, "Status:", 3, 2)
        scb = ttk.Combobox(c, textvariable=self.status_var, values=list(STATUS_MAP.keys()), state="readonly")
        scb.grid(row=3, column=3, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, ipady=ENT_IPADY)
        self.status_var.trace_add("write", self._sync_status)

    def _sync_status(self, *_):
        s = self.status_var.get()
        if self.topbar_status:
            self.topbar_status.configure(fg=STATUS_MAP.get(s, "#B2BEC3"), text=f"● {s.upper()}")

    def _build_customer(self, parent):
        c = self._card(parent, ICON_BILLTO, "BILL TO", row=0, column=1, sticky="nsew", padx=(4, 0))
        c.grid_columnconfigure(1, weight=1)
        c.grid_columnconfigure(3, weight=1)

        self.cust_name_var = tk.StringVar()
        self._lbl(c, "Name:", 1, 0)
        
        clients = database.get_clients()
        client_names = [cl["name"] for cl in clients]
        self.cust_cb = ACCombobox(c, textvariable=self.cust_name_var, values=client_names)
        self.cust_cb.grid(row=1, column=1, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, ipady=ENT_IPADY)
        self.cust_cb.bind("<<ComboboxSelected>>", self._on_select_client_db)

        self.cust_company_var = tk.StringVar()
        self._lbl(c, "Company:", 1, 2)
        self._ent(c, self.cust_company_var, 1, 3)

        self.cust_email_var = tk.StringVar()
        self._lbl(c, "Email:", 2, 0)
        self._ent(c, self.cust_email_var, 2, 1)

        self.cust_phone_var = tk.StringVar()
        self._lbl(c, "Phone:", 2, 2)
        self._ent(c, self.cust_phone_var, 2, 3)

        self.cust_addr_var = tk.StringVar()
        self._lbl(c, "Address:", 3, 0)
        self._ent(c, self.cust_addr_var, 3, 1, columnspan=3)

        self.cust_city_var = tk.StringVar()
        self._lbl(c, "City/ST/ZIP:", 4, 0)
        self._ent(c, self.cust_city_var, 4, 1, columnspan=3)

    def _on_select_client_db(self, _=None):
        name = self.cust_name_var.get()
        for cl in database.get_clients():
            if cl["name"] == name:
                self.cust_company_var.set(cl.get("company", ""))
                self.cust_email_var.set(cl.get("email", ""))
                self.cust_phone_var.set(cl.get("phone", ""))
                self.cust_addr_var.set(cl.get("address", ""))
                self.cust_city_var.set(cl.get("city", ""))
                break

    def _build_item_entry(self, parent):
        self.catalog = database.get_catalog()
        c = self._card(parent, ICON_ADDITEM, "ADD LINE ITEM", row=1, column=0, sticky="ew", pady=(6, 0))
        c.grid_columnconfigure(3, weight=1)

        self.cat_var = tk.StringVar()
        self._lbl(c, "Catalog:", 1, 0)
        
        self.cat_cb = ttk.Combobox(c, textvariable=self.cat_var, values=["(custom item)"] + list(self.catalog.keys()), state="readonly")
        if self.cat_cb["values"]:
            self.cat_cb.current(0)
        self.cat_cb.grid(row=1, column=1, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, ipady=ENT_IPADY)
        self.cat_cb.bind("<<ComboboxSelected>>", self._on_cat)

        self.prod_var = tk.StringVar()
        self.prod_cb = ACCombobox(c, textvariable=self.prod_var)
        self.prod_cb.grid(row=1, column=2, columnspan=2, sticky="ew", padx=(0, ENT_PAD_R), pady=PAD_Y, ipady=ENT_IPADY)
        self.prod_cb.bind("<<ComboboxSelected>>", self._on_prod)

        self._lbl(c, "Qty:", 1, 4)
        self.qty_var = tk.StringVar(value="1")
        self._ent(c, self.qty_var, 1, 5)

        self._lbl(c, "Price:", 1, 6)
        self.price_var = tk.StringVar(value="0.00")
        self._ent(c, self.price_var, 1, 7)

        self.desc_var = tk.StringVar()
        self._lbl(c, "Description:", 2, 0)
        self._ent(c, self.desc_var, 2, 1, columnspan=6)

        self._btn(c, "➕  Add", self._add_item, "primary", row=2, column=7)

    def _on_cat(self, _=None):
        cat = self.cat_var.get()
        self.catalog = database.get_catalog()
        if cat == "(custom item)":
            self.prod_cb.set_full_values([])
            self.prod_var.set("")
            return
        self.prod_cb.set_full_values([p[0] for p in self.catalog.get(cat, [])])
        self.prod_var.set("")

    def _on_prod(self, _=None):
        cat = self.cat_var.get()
        if cat == "(custom item)": return
        for n, p in self.catalog.get(cat, []):
            if n == self.prod_var.get():
                self.desc_var.set(n)
                self.price_var.set(f"{p:.2f}")
                return

    def _add_item(self):
        desc = self.desc_var.get().strip() or self.prod_var.get().strip()
        if not desc:
            messagebox.showwarning("Missing", "Enter a description.")
            return
        try:
            qty = int(self.qty_var.get())
            assert qty >= 1
        except (ValueError, AssertionError):
            messagebox.showwarning("Invalid", "Qty must be a positive integer.")
            return
        try:
            price = float(self.price_var.get())
            assert price >= 0
        except (ValueError, AssertionError):
            messagebox.showwarning("Invalid", "Price must be ≥ 0.")
            return
        self.items.append({"desc": desc, "qty": qty, "price": price, "total": qty * price})
        self._refresh_table()
        self._recalc()
        self.prod_var.set("")
        self.desc_var.set("")
        self.qty_var.set("1")
        self.price_var.set("0.00")

    def _build_items_table(self, parent):
        wrap = tk.Frame(parent, bg=BORDER)
        wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        head = tk.Frame(wrap, bg=CARD)
        head.grid(row=0, column=0, sticky="w", padx=PAD_OUTER, pady=(8, 4))
        tk.Label(head, text=ICON_ITEMS, bg=CARD, fg=ACCENT, font=(FF, 11)).pack(side="left", padx=(0, 6))
        tk.Label(head, text="INVOICE ITEMS", bg=CARD, fg=PRIMARY, font=F_HEAD, anchor="w").pack(side="left")

        inner = tk.Frame(wrap, bg=CARD)
        inner.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)

        cols = ("no", "desc", "qty", "uprice", "total", "act")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings", height=4)
        for col, heading, width, anchor in [("no", "#", 35, "center"), ("desc", "Description", 180, "w"), 
                                            ("qty", "Qty", 45, "center"), ("uprice", "Unit Price", 90, "e"), 
                                            ("total", "Total", 90, "e"), ("act", "", 35, "center")]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.tag_configure("alt", background=TABLE_ALT)

        self.empty_state = tk.Frame(inner, bg=CARD)
        tk.Label(self.empty_state, text="No items added yet.", bg=CARD, fg=TEXT, font=(FF, 10, "bold")).pack()

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        if not self.items:
            self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
            return
        self.empty_state.place_forget()
        for i, it in enumerate(self.items):
            self.tree.insert("", "end", iid=str(i), values=(
                i + 1, it["desc"], it["qty"], fmt(it["price"]), fmt(it["total"]), "✕"),
                tags=("alt",) if i % 2 else ())
        self.tree.bind("<Button-1>", self._tree_click)

    def _tree_click(self, e):
        if self.tree.identify("region", e.x, e.y) != "cell": return
        if self.tree.identify_column(e.x) == "#6":
            rid = self.tree.identify_row(e.y)
            if rid:
                self.items.pop(int(rid))
                self._refresh_table()
                self._recalc()

    def _sum_value_lbl(self, parent, row, fg=TEXT, font=F_ENTRY):
        l = tk.Label(parent, text="₹0.00", bg=CARD, fg=fg, font=font, anchor="e")
        l.grid(row=row, column=1, sticky="e", padx=(0, PAD_OUTER), pady=2)
        return l

    def _sum_entry(self, parent, var, row):
        bf = tk.Frame(parent, bg=BORDER)
        bf.grid(row=row, column=1, sticky="ew", padx=(0, PAD_OUTER), pady=2)
        ent = tk.Entry(bf, textvariable=var, font=F_ENTRY, bg=ENTRY_BG, fg=TEXT, relief="flat", bd=2, justify="right")
        ent.pack(fill="both", expand=True, ipady=2)
        ent.bind("<KeyRelease>", lambda _: self._recalc())
        return ent

    def _build_summary(self, parent):
        sc = self._card(parent, ICON_SUMMARY, "SUMMARY", row=0, column=1, sticky="new", padx=(6, 0))
        sc.grid_columnconfigure(1, weight=1)

        self.discount_pct_var = tk.StringVar(value="0")
        self.shipping_var = tk.StringVar(value="0.00")

        self._lbl(sc, "Subtotal:", 1, 0)
        self.subtotal_lbl = self._sum_value_lbl(sc, 1)

        self._lbl(sc, "Discount %:", 2, 0)
        self._sum_entry(sc, self.discount_pct_var, 2)

        self._lbl(sc, "Discount Amt:", 3, 0)
        self.discount_amt_lbl = self._sum_value_lbl(sc, 3)

        self._lbl(sc, "Shipping:", 4, 0)
        self._sum_entry(sc, self.shipping_var, 4)

        tk.Frame(sc, bg=ACCENT, height=1).grid(row=5, column=0, columnspan=2, sticky="ew", padx=PAD_OUTER, pady=4)
        tk.Label(sc, text="TOTAL", bg=CARD, fg=PRIMARY, font=F_TOTAL, anchor="e").grid(row=6, column=0, sticky="e", padx=(0, PAD_X), pady=2)
        self.total_lbl = tk.Label(sc, text="₹0.00", bg=CARD, fg=PRIMARY, font=F_TOTAL, anchor="e")
        self.total_lbl.grid(row=6, column=1, sticky="e", padx=(0, PAD_OUTER), pady=2)

    def _build_buttons(self, parent):
        bf = tk.Frame(parent, bg=BG)
        bf.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        bf.grid_columnconfigure(0, weight=1)
        
        self._btn(bf, "🗑  Clear All", self._clear_all, "danger", row=0, column=0, sticky="w")
        self._btn(bf, "📄  Preview PDF", self._preview, "ghost", row=0, column=1, sticky="e", padx=8)
        self._btn(bf, "💾  Save as PDF", self._save_pdf, "success", row=0, column=2, sticky="e")

    def _recalc(self, *_):
        sub = sum(i["total"] for i in self.items)
        self.subtotal_lbl.config(text=fmt(sub))
        try: dp = float(self.discount_pct_var.get() or 0)
        except ValueError: dp = 0
        da = sub * dp / 100
        self.discount_amt_lbl.config(text=f"-{fmt(da)}")

        taxable = sub - da

        try: ship = float(self.shipping_var.get() or 0)
        except ValueError: ship = 0
        self.total_lbl.config(text=fmt(taxable + ship))

    def _gather(self):
        sub = sum(i["total"] for i in self.items)
        try: dp = float(self.discount_pct_var.get() or 0)
        except ValueError: dp = 0
        da = sub * dp / 100
        taxable = sub - da
        try: ship = float(self.shipping_var.get() or 0)
        except ValueError: ship = 0
        return {
            "inv_no": self.inv_no_var.get().strip(),
            "inv_date": self.inv_date_var.get().strip(),
            "due_date": self.due_date_var.get().strip(),
            "sales": self.sales_var.get().strip(),
            "terms": self.terms_var.get(),
            "status": self.status_var.get(),
            "cust_name": self.cust_name_var.get().strip(),
            "cust_company": self.cust_company_var.get().strip(),
            "cust_email": self.cust_email_var.get().strip(),
            "cust_phone": self.cust_phone_var.get().strip(),
            "cust_addr": self.cust_addr_var.get().strip(),
            "cust_city": self.cust_city_var.get().strip(),
            "items": list(self.items),
            "subtotal": sub, "discount_pct": dp, "discount_amt": da,
            "shipping": ship,
            "grand_total": taxable + ship,
            "notes": DEFAULT_NOTES,
        }

    def _validate(self):
        if not self.items:
            messagebox.showwarning("Empty", "Add at least one item.")
            return False
        if not self.cust_name_var.get().strip():
            messagebox.showwarning("Missing", "Customer name required.")
            return False
        return True

    def _clear_all(self):
        if not messagebox.askyesno("Confirm", "Clear everything?"): return
        self.items.clear()
        self._refresh_table()
        self.inv_no_var.set(f"EF-{self.invoice_counter:05d}")
        self._recalc()

    def _build_pdf(self, path, d):
        comp = database.get_company_profile()
        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=36*mm, rightMargin=36*mm, topMargin=22*mm, bottomMargin=22*mm)
        ss = getSampleStyleSheet()
        story = []

        # Typography hierarchy & clean left alignments
        sB = ParagraphStyle("B", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=15, textColor=colors.HexColor(PRIMARY), spaceAfter=1, leading=18, alignment=0)
        sT = ParagraphStyle("T", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor(TEXT_MUTED), spaceAfter=3, alignment=0)
        sH = ParagraphStyle("H", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor(PRIMARY), spaceAfter=3)
        sN = ParagraphStyle("N", parent=ss["Normal"], fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor(TEXT), leading=12)
        sS = ParagraphStyle("S", parent=ss["Normal"], fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor(TEXT_MUTED), leading=10, alignment=0)
        sR = ParagraphStyle("R", parent=sN, alignment=2)
        sRB = ParagraphStyle("RB", parent=sN, alignment=2, fontName="Helvetica-Bold")
        sTL = ParagraphStyle("TL", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor(PRIMARY), alignment=2)
        
        # Handle Custom Logo sizing: Fixed fixed display dimension calculation in points (~65pt width x proportional height)
        logo_path = comp.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                px_w, px_h = pil_img.size
                target_w = 65
                target_h = max(20, min(50, int(target_w * (px_h / px_w))))
                logo_flowable = RLImage(logo_path, width=target_w, height=target_h)
            except Exception:
                logo_flowable = Paragraph("<b>[LOGO]</b>", sB)
        else:
            logo_flowable = Drawing(30, 30)
            logo_flowable.add(Rect(4, 2, 18, 3, fillColor=colors.HexColor(PRIMARY), strokeColor=None))
            logo_flowable.add(Rect(4, 5, 3, 16, fillColor=colors.HexColor(PRIMARY), strokeColor=None))
            logo_flowable.add(Rect(19, 5, 3, 16, fillColor=colors.HexColor(PRIMARY), strokeColor=None))
            logo_flowable.add(Rect(4, 18, 18, 3, fillColor=colors.HexColor(ACCENT), strokeColor=None))
            logo_flowable.add(Rect(7, 21, 12, 3, fillColor=colors.HexColor(PRIMARY), strokeColor=None))

        # Left-aligned company layout configuration block with logo
        ld = [
            [logo_flowable, Paragraph(comp.get("name", "COMPANY"), sB)],
            [None, Paragraph(comp.get("tagline", ""), sT)],
            [None, Paragraph(f"{comp.get('address', '')}<br/>Tel: {comp.get('phone', '')} &nbsp;|&nbsp; {comp.get('email', '')}", sS)]
        ]
              
        rd = [
            [Paragraph(f"<b>Invoice:</b> {d['inv_no']}", sR)],
            [Paragraph(f"<b>Date:</b> {d['inv_date']}", sR)],
            [Paragraph(f"<b>Status:</b> {d['status']}", sR)],
            [Paragraph(f"<b>Due:</b> {d['due_date']}", sR)],
            [Paragraph(f"<b>Terms:</b> {d['terms']}", sR)],
            [Paragraph(f"<b>Sales:</b> {d['sales'] or '—'}", sR)]
        ]
              
        lt = Table(ld, colWidths=[70, 150])
        lt.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        
        rt = Table(rd, colWidths=[176])
        rt.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        
        ht = Table([[lt, rt]], colWidths=[220, 176])
        ht.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(ht)
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(ACCENT)))
        story.append(Spacer(1, 10))

        # Bill To Section
        story.append(Paragraph("<b>BILL TO</b>", sH))
        bt = f"<b>{d['cust_name']}</b>"
        for field_key in ("cust_company", "cust_addr", "cust_city", "cust_email", "cust_phone"):
            if d.get(field_key): 
                bt += f"<br/>{d[field_key]}"
        story.append(Paragraph(bt, sN))
        story.append(Spacer(1, 10))

        # Table Styles with explicit column distribution matching total width (396 pt)
        sTH_C = ParagraphStyle("TH_C", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=1)
        sTH_L = ParagraphStyle("TH_L", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=0)
        sTH_R = ParagraphStyle("TH_R", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=2)
        sTC_C = ParagraphStyle("TC_C", fontName="Helvetica", fontSize=8, textColor=colors.HexColor(TEXT), alignment=1)
        sTC_L = ParagraphStyle("TC_L", fontName="Helvetica", fontSize=8, textColor=colors.HexColor(TEXT), alignment=0)
        sTC_R = ParagraphStyle("TC_R", fontName="Helvetica", fontSize=8, textColor=colors.HexColor(TEXT), alignment=2)

        td = [[Paragraph("#", sTH_C), Paragraph("Description", sTH_L), Paragraph("Qty", sTH_C), Paragraph("Unit Price (Rs.)", sTH_R), Paragraph("Total (Rs.)", sTH_R)]]
        
        for i, it in enumerate(d["items"]):
            u_price_str = f"Rs. {it['price']:,.2f}"
            tot_price_str = f"Rs. {it['total']:,.2f}"
            td.append([
                Paragraph(str(i + 1), sTC_C), 
                Paragraph(it["desc"], sTC_L), 
                Paragraph(str(it["qty"]), sTC_C), 
                Paragraph(u_price_str, sTC_R), 
                Paragraph(tot_price_str, sTC_R)
            ])
                       
        it2 = Table(td, colWidths=[20, 206, 25, 75, 70], repeatRows=1)
        it2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor(BORDER)),
            ("TOPPADDING", (0, 0), (-1, -1), 4), 
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(it2)
        story.append(Spacer(1, 10))

        # Summary Block Calculation Table (Tax and Tax percentages removed)
        sd = [[Paragraph("Subtotal", sR), Paragraph(f"Rs. {d['subtotal']:,.2f}", sRB)]]
        if d.get("discount_pct", 0) > 0: 
            sd.append([Paragraph("Discount", sR), Paragraph(f"-Rs. {d['discount_amt']:,.2f}", sRB)])
        if d.get("shipping", 0) > 0: 
            sd.append([Paragraph("Shipping", sR), Paragraph(f"Rs. {d['shipping']:,.2f}", sRB)])
        
        sd.append([Paragraph("<b>TOTAL</b>", sTL), Paragraph(f"<b>Rs. {d['grand_total']:,.2f}</b>", sTL)])
        
        st = Table(sd, colWidths=[95, 95])
        st.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor(PRIMARY)),
        ]))
        
        notes_para = Paragraph(f"<b>Notes & Terms</b><br/><font size=7 color='{TEXT_MUTED}'>{d.get('notes', DEFAULT_NOTES).replace(chr(10), '<br/>')}</font>", sN)
        
        bottom_table = Table([[notes_para, st]], colWidths=[206, 190])
        bottom_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        
        story.append(bottom_table)
        doc.build(story)
        
    def _preview(self):
        if not self._validate(): return
        if not REPORTLAB_AVAILABLE: messagebox.showerror("Error", "pip install reportlab"); return
        d = self._gather()
        tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_preview_{d['inv_no']}.pdf")
        try:
            self._build_pdf(tmp, d)
            import subprocess
            if _S == "Windows": os.startfile(tmp)
            elif _S == "Darwin": subprocess.call(["open", tmp])
            else: subprocess.call(["xdg-open", tmp])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_pdf(self):
        if not self._validate(): return
        if not REPORTLAB_AVAILABLE: messagebox.showerror("Error", "pip install reportlab"); return
        d = self._gather()
        fp = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"{d['inv_no']}.pdf")
        if not fp: return
        try:
            self._build_pdf(fp, d)
            self.invoice_counter += 1
            database.save_counter(self.invoice_counter)
            self.inv_no_var.set(f"EF-{self.invoice_counter:05d}")
            messagebox.showinfo("Saved", f"File: {fp}\nTotal: {fmt(d['grand_total'])}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")