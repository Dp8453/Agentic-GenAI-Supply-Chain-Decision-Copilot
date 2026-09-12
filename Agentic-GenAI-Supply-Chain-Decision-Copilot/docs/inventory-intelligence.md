# Inventory Intelligence & Deterministic Decision Engine — SupplyChain AI

## 1. Executive Summary & Core Philosophy

The **Inventory Intelligence & Risk Engine** provides fully deterministic, mathematically explainable risk scores, stockout projections, and procurement reorder recommendations.

### Core Philosophy: Zero LLM Calculation
- **LLM Responsibility**: Intent understanding, query planning, conversational synthesis, evidence presentation.
- **Python Deterministic Engine Responsibility**: Safety stock, reorder point, inventory position, stockout timeline simulation, risk scoring (0-100), MOQ rounding, and reorder action classification.

The LLM is **NEVER** permitted to invent or directly calculate numerical business results.

---

## 2. Mathematical Formulations

### 2.1 Inventory Position
$$\text{Inventory Position} = \text{Current Stock} + \text{Incoming Orders} - \text{Reserved Stock}$$

### 2.2 Safety Stock (SS)
Safety stock protects against both demand variability ($\sigma_D$) and supplier lead-time variability ($\sigma_L$):

$$SS = Z \times \sqrt{L \times \sigma_D^2 + D^2 \times \sigma_L^2}$$

- $Z = 1.645$ (Default 95% service level factor)
- $L$ = Average actual supplier lead time in days
- $\sigma_D$ = Standard deviation of daily demand
- $D$ = Average daily demand
- $\sigma_L$ = Standard deviation of supplier lead time

### 2.3 Reorder Point (ROP)
$$\text{ROP} = \lceil \text{Forecasted Demand During Lead Time} + SS \rceil$$

### 2.4 Days of Inventory Coverage
$$\text{Days of Inventory} = \frac{\text{Current Stock}}{\text{Average Daily Demand}}$$
*(Returns `None` if Average Daily Demand = 0 to prevent division-by-zero errors)*.

---

## 3. Stockout Trajectory Simulation & Projection

Using the Phase 3 ML multi-step demand forecast, the engine simulates daily inventory trajectories over the forecast horizon:

$$\text{Projected Stock}(t) = \text{Starting Stock} + \text{Incoming POs}(t) - \text{Forecast Demand}(t)$$

If $\text{Projected Stock}(t) \le 0$, the engine records the exact first date of projected stockout (`projected_stockout_date`).

---

## 4. Risk Scoring & Classification

| Risk Score Range | Risk Level | Meaning |
|---|---|---|
| **0 – 24** | `LOW` | Inventory position is healthy; stock exceeds reorder threshold. |
| **25 – 49** | `MEDIUM` | Inventory is adequate; minor lead time or demand variance to monitor. |
| **50 – 74** | `HIGH` | Inventory position is below reorder point or near safety stock. |
| **75 – 100** | `CRITICAL` | Projected stockout detected before replenishment arrival or safety stock breached. |

### Scoring Component Weights
- **Projected Stockout**: +35 points
- **Safety Stock Breach**: +30 points
- **Reorder Point Breach**: +20 points
- **Coverage Less Than Lead Time**: +15 points

---

## 5. Reorder Quantity & MOQ Rounding Logic

1. **Target Inventory**: $\text{Target} = \text{ROP} + SS$
2. **Calculated Deficit**: $\text{Deficit} = \text{Target} - \text{Inventory Position}$
3. **MOQ Increment Rounding**:
   - If $\text{Deficit} \le 0 \implies \text{Quantity} = 0$
   - If $0 < \text{Deficit} \le \text{MOQ} \implies \text{Quantity} = \text{MOQ}$
   - If $\text{Deficit} > \text{MOQ} \implies \text{Quantity} = \lceil \frac{\text{Deficit}}{\text{MOQ}} \rceil \times \text{MOQ}$

---

## 6. Action Classification Matrix

| Risk Level / Inventory Condition | Recommended Action |
|---|---|
| Risk = `CRITICAL` OR `projected_stockout` = True | `URGENT_REORDER` |
| Risk = `HIGH` OR `inventory_position` $\le$ `ROP` | `REORDER` |
| Risk = `MEDIUM` | `MONITOR` |
| Risk = `LOW` | `NO_ACTION` |
