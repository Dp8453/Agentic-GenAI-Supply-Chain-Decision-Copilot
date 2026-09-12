# Inventory Reorder & Safety Stock Policy

**Document Status**: Synthetic / Demonstration Project Policy  
**Document Type**: Procurement Policy  
**Effective Date**: January 1, 2024  
**Version**: 1.1  

---

## 1. Reorder Point Triggers
A replenishment purchase order is automatically triggered whenever an item's Inventory Position (Current Stock + Incoming POs - Reserved Stock) drops to or below its calculated Reorder Point (ROP).

---

## 2. Safety Stock Policy
Safety Stock buffers are evaluated at a 95% service level ($Z = 1.645$). Safety stock levels must incorporate both historical daily demand volatility ($\sigma_D$) and vendor lead-time variability ($\sigma_L$).
- Safety stock must remain unallocated for routine sales fulfillment under normal operating conditions.
