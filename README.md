# Pharmacy Management System

Custom Odoo addon for pharmacy operations: medicine catalog, purchases, POS sales, expenses, dashboard analytics, stock movement audit, receipts, and period reports.

## Main Capabilities

- Modern pharmacy dashboard with KPIs, sales analytics, recent orders, low stock, expiry watch, best sellers, and quick actions.
- POS order screen with fast medicine search, category filtering, cart management, discounts, tax, payment summary, and recent customers.
- Purchase confirmation that increases stock and creates stock movement records.
- Sale confirmation that decreases stock and creates stock movement records.
- Medicine catalog with generic name, manufacturer, internal code, pricing, reorder level, stock, and expiry date.
- PDF/XLSX period reports and printable sale receipt.
- Owner and employee access groups.

## Installation

Add the parent directory of this addon to `addons_path`, then install `pharmacy_management_system` from Odoo Apps or with:

```bash
./odoo-bin -c odoo.conf -d pharmacy_odoo -i pharmacy_management_system --stop-after-init
```

Update after code changes:

```bash
./odoo-bin -c odoo.conf -d pharmacy_odoo -u pharmacy_management_system --stop-after-init
```

## Configuration

In Odoo Settings, configure:

- Default POS tax rate
- Optional HuggingFace API token and model for the AI assistant

## Notes

This module keeps stock management intentionally lightweight for portfolio/demo usage while adding a stock movement audit trail. For large production deployments, consider integrating medicine products with Odoo Inventory lots/batches, accounting, purchase, and stock valuation.
