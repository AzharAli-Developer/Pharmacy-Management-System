# Pharmacy Management System (Odoo + AI Assistant)

A complete **Pharmacy Management System** built with **Odoo**, featuring inventory management, medicine tracking, sales management, purchase management, supplier management, expense tracking, reporting, and an **AI-powered Pharmacy Assistant** using HuggingFace LLM integration.

This project is designed as a **custom Odoo addon module**. It does **not** include the full Odoo source code. Developers must first set up Odoo, then install this module.

---

# Features

## Core Pharmacy Features

* Pharmacy dashboard
* Medicine management
* Category management
* Supplier management
* Purchase management
* Sales / Order management
* Expense management
* Expired medicine tracking
* Expiry soon alerts
* Daily sales chart dashboard
* Sales PDF receipt
* Excel report export
* Period-based reports
* Role-based access control

---

## AI Assistant Features

Integrated AI assistant with HuggingFace LLM support.

Capabilities:

* Medicine usage information
* Pharmacy workflow guidance
* Medicine stock awareness
* Supplier information
* Expense information
* Sales data awareness
* General pharmacy questions
* Project workflow help

Example questions:

```text
What is Paracetamol used for?
How much stock is available for Panadol?
Show supplier information.
How do I create a purchase order?
What expenses were added recently?
```

---

# Technology Stack

## Backend

* Python
* Odoo
* PostgreSQL

## Frontend

* OWL (Odoo Web Library)
* JavaScript
* XML
* CSS

## AI Integration

* HuggingFace API
* Meta Llama Model

---

# Project Structure

```text
pharmacy_management_system/
│
├── controllers/
│   ├── __init__.py
│   ├── ai_assistant.py
│   └── pharmacy_report.py
│
├── data/
│   └── pharmacy_dashboard_data.xml
│
├── models/
│   ├── __init__.py
│   ├── ai_assistant.py
│   ├── category.py
│   ├── dashboard.py
│   ├── expense.py
│   ├── medicine.py
│   ├── purchase.py
│   ├── purchase_line.py
│   ├── sale.py
│   ├── sale_order_line.py
│   ├── supplier.py
│   ├── res_config_setting.py
│   └── period_report_wizard.py
│
├── reports/
│   ├── pharmacy_sale_receipt_report.xml
│   └── pharmacy_period_sales_report.xml
│
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
│
├── static/
│   └── src/
│       ├── css/
│       │   └── pharmacy_management.css
│       ├── js/
│       │   ├── pharmacy_dashboard.js
│       │   └── pharmacy_orders.js
│       └── xml/
│           ├── pharmacy_dashboard.xml
│           └── pharmacy_orders.xml
│
├── views/
│   ├── category_views.xml
│   ├── dashboard_views.xml
│   ├── expense_views.xml
│   ├── medicine_views.xml
│   ├── menu_views.xml
│   ├── purchase_views.xml
│   ├── sale_views.xml
│   ├── supplier_views.xml
│   └── res_config_settings_views.xml
│
└── __manifest__.py
```

---

# Prerequisites

Install the following before setup:

* Ubuntu / Linux
* Python 3.10+
* PostgreSQL
* Git
* pip
* virtualenv
* Odoo 18 (or compatible version)

---

# Step 1: Install PostgreSQL

Ubuntu:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Start PostgreSQL:

```bash
sudo service postgresql start
```

Create PostgreSQL user:

```bash
sudo -u postgres createuser -s $USER
```

Create database:

```bash
createdb pharmacy_db
```

---

# Step 2: Install Odoo

Clone Odoo source:

```bash
git clone https://github.com/odoo/odoo.git --depth 1 --branch 18.0
```

Go inside:

```bash
cd odoo
```

Create virtual environment:

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Install requirements:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

# Step 3: Clone This Repository

Clone custom module:

```bash
git clone YOUR_REPOSITORY_URL
```

Example:

```bash
git clone https://github.com/yourusername/pharmacy_management_system.git
```

---

# Step 4: Add Module to Odoo Addons

Create custom addons folder:

```bash
mkdir custom_addons
```

Copy project:

```bash
cp -r pharmacy_management_system custom_addons/
```

Final structure:

```text
odoo/
├── addons/
├── custom_addons/
│   └── pharmacy_management_system/
├── odoo-bin
└── ...
```

---

# Step 5: Configure Odoo

Create:

```bash
odoo.conf
```

Example:

```ini
[options]
admin_passwd = admin
db_host = False
db_port = False
db_user = YOUR_POSTGRES_USER
db_password = False
addons_path = addons,custom_addons
xmlrpc_port = 8069
```

Replace:

```text
YOUR_POSTGRES_USER
```

with your PostgreSQL username.

---

# Step 6: Install Project Dependencies

If project includes:

```bash
requirements.txt
```

Install:

```bash
pip install -r pharmacy_management_system/requirements.txt
```

---

# Step 7: Run Odoo

Start server:

```bash
python odoo-bin -c odoo.conf
```

OR with database:

```bash
python odoo-bin -c odoo.conf -d pharmacy_db
```

---

# Step 8: Install Module

Open browser:

```text
http://localhost:8069
```

Then:

* Create database
* Login
* Apps
* Update Apps List
* Search:

```text
Pharmacy Management
```

Install module.

---

# Step 9: Configure AI Assistant

Get HuggingFace API token:

```text
https://huggingface.co/settings/tokens
```

Create token.

Example:

```text
hf_xxxxxxxxxxxxxxxxxxxxx
```

Then in Odoo:

```text
Settings → General Settings → Pharmacy AI Assistant
```

Set:

## HuggingFace API Token

```text
hf_xxxxxxxxxxxxxxxxxxxxx
```

## HuggingFace Model

```text
meta-llama/Meta-Llama-3-8B-Instruct:novita
```

Save settings.

---

# AI Assistant Usage

Open dashboard.

Click:

```text
Ask AI Assistant
```

Ask:

```text
What is Paracetamol used for?
How much stock is available?
Show supplier information.
How do I create a sale?
```

---

# User Roles

## Owner

Full permissions:

* Create
* Read
* Update
* Delete

for:

* medicines
* categories
* suppliers
* purchases
* sales
* expenses
* dashboard
* reports

---

## Employee

Limited permissions:

Read-only access where configured.

---

# Reports

Available:

## PDF Receipt

Sale receipt:

```text
Sales → Print Bill
```

---

## Excel Reports

Dashboard:

```text
Previous Report → Download Excel
```

---

# Troubleshooting

## Module not showing

Update app list:

```bash
python odoo-bin -c odoo.conf -u base
```

Check:

```ini
addons_path
```

---

## Database connection error

Verify PostgreSQL:

```bash
sudo service postgresql status
```

Check config:

```ini
db_user
db_password
```

---

## AI assistant not responding

Check:

* HuggingFace token
* internet connection
* model name

Correct model:

```text
meta-llama/Meta-Llama-3-8B-Instruct:novita
```

---

## Permission errors

Check:

```text
security/security.xml
security/ir.model.access.csv
```

---

## Frontend JS not updating

Restart:

```bash
python odoo-bin -c odoo.conf -u pharmacy_management_system --dev=all
```

Hard refresh browser:

```text
Ctrl + Shift + R
```

---

# Development Mode

Run:

```bash
python odoo-bin -c odoo.conf -d pharmacy_db --dev=all
```

Useful for:

* JS debugging
* XML debugging
* CSS debugging
* OWL debugging

---

# Production Notes

Recommended:

* PostgreSQL backups
* environment variables for secrets
* HTTPS reverse proxy
* Gunicorn deployment
* Nginx reverse proxy
* production logging

---

# Future Improvements

Possible enhancements:

* barcode scanning
* customer management
* invoice generation
* purchase approval workflow
* analytics dashboard
* advanced AI medicine recommendations
* chatbot memory
* REST API integration

---

# Author

Azhar Ali

Full Stack Developer

---

# License

This project is for educational / development use.
Update licensing as needed.
