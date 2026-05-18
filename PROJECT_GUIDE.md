# PROJECT_GUIDE.md

# Pharmacy Management System — Complete Project Guide

## Overview

This document explains the complete architecture, logic, and implementation of the **Pharmacy Management System** built with Odoo.

It is written for:

* beginners learning Odoo
* developers maintaining this project
* developers building similar ERP systems
* contributors extending this module

---

# Project Architecture

This project follows Odoo’s modular architecture.

Structure:

```text
pharmacy_management_system/
├── controllers/
├── models/
├── views/
├── security/
├── reports/
├── static/
├── data/
└── __manifest__.py
```

Each folder has a specific responsibility.

---

# Odoo Module Lifecycle

When Odoo starts:

1. Reads `__manifest__.py`
2. Loads dependencies
3. Loads security
4. Loads models
5. Loads XML views
6. Loads reports
7. Loads static assets
8. Registers controllers
9. Makes frontend actions available

Flow:

```text
Manifest
   ↓
Models
   ↓
Security
   ↓
Views
   ↓
Actions
   ↓
Frontend JS
   ↓
User Interaction
```

---

# Manifest File

File:

```text
__manifest__.py
```

Purpose:

Registers module metadata.

Example responsibilities:

* module name
* version
* dependencies
* XML loading
* asset loading

Example:

```python
'depends': ['base', 'web', 'base_setup']
```

Meaning:

Project depends on:

* base Odoo
* frontend web framework
* settings module

Assets:

```python
'assets': {
    'web.assets_backend': [
        js,
        css,
        xml
    ]
}
```

This loads frontend dashboard assets.

---

# Models

Folder:

```text
models/
```

Purpose:

Contains business logic and database tables.

Each Odoo model becomes a PostgreSQL table.

Example:

```python
class Medicine(models.Model):
    _name = 'pharmacy.medicine'
```

Creates:

```text
pharmacy_medicine
```

database table.

---

# Main Models

## Medicine

File:

```text
models/medicine.py
```

Purpose:

Stores medicine records.

Fields:

```python
name
category_id
description
sale_price
stock
expiry_date
```

Example:

```python
name = fields.Char()
```

stores medicine name.

---

## Category

File:

```text
models/category.py
```

Purpose:

Medicine classification.

Example:

```text
Pain Killer
Antibiotic
Vitamin
```

---

## Supplier

File:

```text
models/supplier.py
```

Purpose:

Stores supplier records.

Fields:

```python
name
phone
email
address
```

---

## Expense

File:

```text
models/expense.py
```

Purpose:

Tracks operational expenses.

Examples:

* rent
* salary
* electricity
* lunch

---

## Sale

File:

```text
models/sale.py
```

Purpose:

Stores sale orders.

Fields:

```python
customer_name
sale_date
discount
state
cashier_id
```

---

## Sale Line

File:

```text
models/sale_order_line.py
```

Purpose:

Stores medicine lines inside sale.

Example:

Sale:

```text
Customer: Ali
```

Lines:

```text
Paracetamol x 2
Panadol x 3
```

---

## Purchase

File:

```text
models/purchase.py
```

Purpose:

Purchase from supplier.

---

## Purchase Line

File:

```text
models/purchase_line.py
```

Purpose:

Stores purchased medicine rows.

---

## Dashboard

File:

```text
models/dashboard.py
```

Purpose:

Provides dashboard statistics.

Examples:

* medicine count
* sales count
* expense total
* expiry medicines

---

## AI Assistant

File:

```text
models/ai_assistant.py
```

Purpose:

Handles AI logic.

Responsibilities:

* HuggingFace API call
* database context
* medicine detection
* workflow guidance

---

# Model Relationships

This project uses relational database design.

---

## Many2one

Example:

```python
category_id = fields.Many2one('pharmacy.category')
```

Meaning:

Many medicines belong to one category.

Example:

```text
Paracetamol → Pain Killer
Panadol → Pain Killer
```

---

## One2many

Example:

```python
medicine_ids = fields.One2many('pharmacy.sale.line', 'sale_id')
```

Meaning:

One sale contains many sale lines.

Example:

```text
Sale #1
   Paracetamol
   Panadol
   Vitamin C
```

---

# Relationship Diagram

```text
Category
   ↑
Medicine
   ↑
SaleLine
   ↑
Sale

Supplier
   ↑
Purchase
   ↑
PurchaseLine
   ↑
Medicine
```

---

# Computed Fields

Example:

```python
total_amount = fields.Float(compute='_compute_total_amount')
```

Meaning:

Value automatically calculated.

Example:

```python
2 x 100 = 200
```

Odoo computes automatically.

---

# XML Views

Folder:

```text
views/
```

Purpose:

Frontend UI definition.

---

## List View

Example:

```xml
<list>
    <field name="name"/>
</list>
```

Purpose:

Table view.

---

## Form View

Example:

```xml
<form>
```

Purpose:

Single record editing.

---

## Kanban View

Example:

```xml
<kanban>
```

Purpose:

Card-style UI.

---

## Search View

Example:

```xml
<search>
```

Purpose:

Filtering.

---

# Actions

Example:

```xml
<record model="ir.actions.act_window">
```

Purpose:

Open model screens.

Example:

```xml
action_pharmacy_medicine
```

opens:

```text
Medicines
```

---

# Menus

File:

```text
views/menu_views.xml
```

Purpose:

Sidebar navigation.

Example:

```xml
<menuitem name="Medicines"/>
```

---

# Security

Folder:

```text
security/
```

Files:

```text
security.xml
ir.model.access.csv
```

---

## security.xml

Defines groups:

```text
Owner
Employee
```

---

## ir.model.access.csv

Defines permissions.

Format:

```csv
read,write,create,unlink
```

Example:

```text
1,1,1,1
```

Full access.

Example:

```text
1,0,0,0
```

Read only.

---

# Controllers

Folder:

```text
controllers/
```

Purpose:

Handle HTTP routes.

---

## AI Controller

File:

```text
controllers/ai_assistant.py
```

Route:

```python
/pharmacy/ai/chat
```

Frontend sends:

```text
question
```

Backend returns:

```text
AI response
```

---

## Report Controller

File:

```text
controllers/pharmacy_report.py
```

Purpose:

* PDF receipt
* Excel export

---

# Frontend Architecture

Folder:

```text
static/src/
```

Contains:

```text
js
css
xml
```

---

# OWL JavaScript

Files:

```text
pharmacy_dashboard.js
pharmacy_orders.js
```

Purpose:

Interactive frontend logic.

---

# Dashboard JS

Main logic:

```javascript
registry.category("actions").add()
```

Registers custom frontend action.

---

## State Management

Example:

```javascript
useState()
```

Stores:

* dashboard data
* popup state
* AI chat state

---

## RPC Calls

Example:

```javascript
rpc("/pharmacy/ai/chat")
```

Frontend sends backend request.

---

## Action Service

Example:

```javascript
this.action.doAction()
```

Opens views.

---

# XML Templates

Files:

```text
pharmacy_dashboard.xml
pharmacy_orders.xml
```

Purpose:

Frontend UI rendering.

Examples:

* dashboard layout
* AI popup
* order screen

---

# CSS

File:

```text
pharmacy_management.css
```

Purpose:

Project styling.

Controls:

* dashboard cards
* popup
* charts
* buttons

---

# AI Assistant Integration

Architecture:

```text
Frontend Popup
   ↓
JS RPC Call
   ↓
Controller Route
   ↓
AI Service Model
   ↓
HuggingFace API
   ↓
Response
   ↓
Frontend Display
```

---

# HuggingFace Integration

Backend:

```python
urllib.request.Request()
```

API:

```text
https://router.huggingface.co/v1/chat/completions
```

Headers:

```python
Authorization: Bearer TOKEN
```

Payload:

```python
model
messages
temperature
max_tokens
```

---

# Database Context Injection

AI searches project database.

Example:

User asks:

```text
What is Paracetamol?
```

System:

1. searches medicine table
2. finds Paracetamol
3. sends stock/price/expiry
4. AI uses real project data

---

# AI Workflow Knowledge

AI knows:

* medicines menu
* purchases menu
* suppliers menu
* sales screen
* dashboard reports

---

# Reports

---

## PDF Receipt

Flow:

```text
Sale
   ↓
QWeb Template
   ↓
PDF
```

---

## Excel Export

Flow:

```text
Wizard
   ↓
xlsxwriter
   ↓
download
```

---

# Dashboard Logic

Backend:

```python
get_dashboard_data()
```

Returns:

* cards
* sales graph
* expiry medicines

Frontend:

renders chart.

---

# Business Logic

---

## Sale Confirmation

When sale confirmed:

```text
stock decreases
```

---

## Purchase Confirmation

When purchase confirmed:

```text
stock increases
```

---

# Common Errors

---

## JS map() error

Cause:

bad doAction config.

Fix:

use XML action IDs.

---

## Group foreign key error

Cause:

changing security groups after installation.

Fix:

clean DB or stable security XML.

---

## AI token error

Cause:

missing HuggingFace token.

Fix:

Settings → General Settings.

---

## AI no medicine detection

Cause:

bad DB search logic.

Fix:

keyword medicine matching.

---

# Development Commands

Run:

```bash
python odoo-bin -c odoo.conf
```

Upgrade:

```bash
python odoo-bin -c odoo.conf -u pharmacy_management_system
```

Debug:

```bash
python odoo-bin -c odoo.conf --dev=all
```

---

# Production Best Practices

Use:

* PostgreSQL backups
* nginx
* gunicorn
* HTTPS
* environment variables
* logging
* monitoring

---

# Learning Outcome

By studying this project, developer learns:

* Odoo module development
* ORM
* relational models
* XML views
* frontend OWL
* controllers
* reports
* security
* AI integration
* HuggingFace API
* ERP architecture

---

# Final Architecture Summary

```text
User
 ↓
Frontend XML + JS
 ↓
RPC / Controller
 ↓
Odoo Models
 ↓
PostgreSQL
 ↓
AI API (HuggingFace)
 ↓
Response
```
