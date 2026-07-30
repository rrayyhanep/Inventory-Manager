# 🪑 Furniture ERP & Invoice Suite

A sleek, modern, fully-featured desktop ERP and Invoice management suite built with **Python**, **Tkinter**, and **ReportLab**. Designed specifically for small-to-medium furniture enterprises and custom workshops to effortlessly manage inventory catalogs, customer client directories, business profiles, and generate professional PDF invoices.

---

## ✨ Key Features

- **📦 Inventory & Catalog Management**: 
  - Centralized catalog with dynamic categories, pricing control, and stock tracking.
  - Interactive item addition, editing, and deletion with real-time updates.
- **🧾 Professional Invoice Generator**:
  - Live auto-calculation of totals, custom discounts, and shipping fees.
  - Instant auto-completion for customer names and catalog lookup items.
  - Direct export to **ReportLab-powered professional PDF invoices** complete with custom company branding and logos.
- **🏢 Company Profile & Client Directory**:
  - Customizable company details (Name, Tagline, Phone, Email, Website, Address, and Logo upload).
  - Built-in client database directory with full add, edit, and delete workflows.
- **🎨 Modern UI/UX Architecture**:
  - Clean, touch/click-friendly custom `clam` theme aesthetic featuring a warm earthy palette (`#3E2723` deep brown, `#ECE4DA` warm cream).
  - Modular frame-switching layout ensuring smooth navigation between pages.

---

## 🛠️ Project Structure

```text
├── App.py             # Main application entry point & window controller
├── Invoice.py         # Invoice generator workspace & ReportLab PDF engine
├── Inventory.py       # Inventory catalog management interface & dialogs
├── Company.py         # Company profile settings & client directory manager
├── database.py        # JSON-based persistent storage layer & data handlers
└── assets/            # Directory for company logos and cached outputs
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have **Python 3.8+** installed on your system along with the following required libraries:

```bash
pip install pillow reportlab
```

### Installation & Running

1. Clone or download the repository to your local machine.
2. Navigate to the project directory.
3. Launch the ERP suite by running `App.py`:

```bash
python App.py
```

---

## 💻 Tech Stack

* **GUI Framework**: Python `tkinter` & `ttk` (Custom styled)
* **Image Processing**: Python Imaging Library (`Pillow`)
* **PDF Generation**: `ReportLab`
* **Data Storage**: Lightweight local `JSON` databases

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).