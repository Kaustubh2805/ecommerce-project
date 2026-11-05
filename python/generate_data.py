"""
Generate a realistic synthetic e-commerce dataset, schema-compatible with the
well-known "Superstore" dataset but normalized into proper relational tables:
    dim_customers, dim_products, fact_orders, fact_order_items, fact_returns

Run: python3 generate_data.py
Outputs CSVs into ../data/
"""
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Reference lists
# ----------------------------------------------------------------------------
FIRST_NAMES = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "William","Elizabeth","David","Barbara","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Christopher","Nancy","Daniel","Lisa",
    "Matthew","Margaret","Anthony","Betty","Mark","Sandra","Donald","Ashley",
    "Steven","Kimberly","Paul","Emily","Andrew","Donna","Joshua","Michelle",
    "Kenneth","Dorothy","Kevin","Carol","Brian","Amanda","George","Melissa",
    "Edward","Deborah","Ronald","Stephanie","Timothy","Rebecca","Jason","Sharon",
    "Jeffrey","Laura","Ryan","Cynthia","Jacob","Kathleen","Gary","Amy","Nicholas","Angela"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas",
    "Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris",
    "Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young","Allen","King",
    "Wright","Scott","Torres","Nguyen","Hill","Flores","Green","Adams","Nelson","Baker"]

REGIONS = {
    "East":  ["New York","Boston","Philadelphia","Newark","Providence"],
    "West":  ["Los Angeles","San Francisco","Seattle","San Diego","Portland"],
    "Central":["Chicago","Dallas","Houston","Minneapolis","Kansas City"],
    "South": ["Miami","Atlanta","Charlotte","Nashville","New Orleans"],
}
STATE_BY_REGION = {"East":"New York","West":"California","Central":"Illinois","South":"Georgia"}

SEGMENTS = ["Consumer","Corporate","Home Office"]
SEGMENT_WEIGHTS = [0.55, 0.28, 0.17]

SHIP_MODES = ["Standard Class","Second Class","First Class","Same Day"]
SHIP_MODE_WEIGHTS = [0.60, 0.20, 0.15, 0.05]
SHIP_LEAD_DAYS = {"Standard Class":(4,7),"Second Class":(2,4),"First Class":(1,2),"Same Day":(0,1)}

CATEGORY_TREE = {
    "Furniture": {
        "sub": ["Chairs","Tables","Bookcases","Furnishings"],
        "price_range": (40, 900), "margin": (0.05, 0.18),
    },
    "Office Supplies": {
        "sub": ["Binders","Paper","Storage","Art","Labels","Fasteners","Envelopes","Supplies"],
        "price_range": (2, 150), "margin": (0.10, 0.30),
    },
    "Technology": {
        "sub": ["Phones","Machines","Accessories","Copiers"],
        "price_range": (30, 2200), "margin": (0.08, 0.25),
    },
}

PRODUCT_ADJ = ["Premium","Deluxe","Standard","Basic","Pro","Executive","Compact","Heavy-Duty","Eco","Classic"]
PRODUCT_NOUN = {
    "Chairs": ["Office Chair","Mesh Chair","Task Chair","Recliner"],
    "Tables": ["Conference Table","Computer Desk","Side Table","Meeting Table"],
    "Bookcases": ["Bookcase","Shelving Unit","Storage Cabinet"],
    "Furnishings": ["Desk Lamp","Wall Clock","Office Rug"],
    "Binders": ["Binder","Ring Binder","View Binder"],
    "Paper": ["Copy Paper","Notebook Paper","Cardstock"],
    "Storage": ["Storage Box","File Cart","Filing Tray"],
    "Art": ["Marker Set","Sketch Pad","Paint Set"],
    "Labels": ["Label Roll","Address Labels","Sticker Sheet"],
    "Fasteners": ["Stapler","Paper Clips","Binder Clips"],
    "Envelopes": ["Envelope Pack","Mailer Box"],
    "Supplies": ["Scissors","Tape Dispenser","Desk Organizer"],
    "Phones": ["Smartphone","Cordless Phone","Phone Case"],
    "Machines": ["Label Maker","Laminator","Calculator"],
    "Accessories": ["USB Hub","Laptop Stand","Wireless Mouse","Keyboard"],
    "Copiers": ["Desktop Copier","All-in-One Printer"],
}

N_CUSTOMERS = 800
N_PRODUCTS = 220
N_ORDERS = 6500
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def seasonal_weight(d):
    # boost Nov-Dec (holiday), slight July dip
    m = d.month
    if m in (11, 12): return 2.2
    if m == 7: return 0.8
    if m in (1,): return 0.85
    return 1.0

# ----------------------------------------------------------------------------
# 1. dim_customers
# ----------------------------------------------------------------------------
customers = []
for i in range(1, N_CUSTOMERS + 1):
    fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
    region = random.choice(list(REGIONS.keys()))
    city = random.choice(REGIONS[region])
    segment = np.random.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
    signup = random_date(START_DATE - timedelta(days=180), END_DATE - timedelta(days=1))
    customers.append({
        "customer_id": f"CUST-{i:05d}",
        "customer_name": f"{fn} {ln}",
        "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
        "segment": segment,
        "region": region,
        "city": city,
        "state": STATE_BY_REGION[region],
        "signup_date": signup.strftime("%Y-%m-%d"),
    })
df_customers = pd.DataFrame(customers)

# ----------------------------------------------------------------------------
# 2. dim_products
# ----------------------------------------------------------------------------
products = []
pid = 1
for category, meta in CATEGORY_TREE.items():
    per_sub = max(1, N_PRODUCTS // (len(CATEGORY_TREE) * len(meta["sub"])))
    for sub in meta["sub"]:
        for _ in range(per_sub):
            adj = random.choice(PRODUCT_ADJ)
            noun = random.choice(PRODUCT_NOUN[sub])
            price = round(random.uniform(*meta["price_range"]), 2)
            margin = round(random.uniform(*meta["margin"]), 3)
            cost = round(price * (1 - margin), 2)
            products.append({
                "product_id": f"PROD-{pid:05d}",
                "product_name": f"{adj} {noun}",
                "category": category,
                "sub_category": sub,
                "unit_price": price,
                "unit_cost": cost,
            })
            pid += 1
df_products = pd.DataFrame(products)

# ----------------------------------------------------------------------------
# 3. fact_orders + fact_order_items
# ----------------------------------------------------------------------------
# Give customers unequal purchase propensity (power-law) for realistic RFM spread
cust_weights = np.random.pareto(2.2, size=N_CUSTOMERS) + 0.2
cust_weights = cust_weights / cust_weights.sum()
cust_ids = df_customers["customer_id"].values

# Build a day-weighted date pool for seasonality
all_days = pd.date_range(START_DATE, END_DATE, freq="D")
day_weights = np.array([seasonal_weight(d) for d in all_days])
day_weights = day_weights / day_weights.sum()

orders, order_items, returns = [], [], []
order_item_id = 1

for oid in range(1, N_ORDERS + 1):
    cust = np.random.choice(cust_ids, p=cust_weights)
    order_date = np.random.choice(all_days, p=day_weights)
    order_date = pd.Timestamp(order_date).to_pydatetime()
    signup = datetime.strptime(
        df_customers.loc[df_customers.customer_id == cust, "signup_date"].values[0], "%Y-%m-%d")
    if order_date < signup:
        order_date = signup + timedelta(days=random.randint(0, 30))

    ship_mode = np.random.choice(SHIP_MODES, p=SHIP_MODE_WEIGHTS)
    lo, hi = SHIP_LEAD_DAYS[ship_mode]
    ship_date = order_date + timedelta(days=random.randint(lo, hi))

    order_id = f"ORD-{oid:06d}"
    n_items = np.random.choice([1,2,3,4,5], p=[0.45,0.28,0.15,0.08,0.04])
    chosen_products = df_products.sample(n=n_items, replace=False)

    order_total = 0.0
    for _, prod in chosen_products.iterrows():
        qty = np.random.choice([1,2,3,4,5,6], p=[0.42,0.25,0.15,0.09,0.06,0.03])
        discount = np.random.choice([0,0.1,0.15,0.2,0.3], p=[0.55,0.20,0.12,0.09,0.04])
        gross = round(prod.unit_price * qty, 2)
        sales = round(gross * (1 - discount), 2)
        cost = round(prod.unit_cost * qty, 2)
        profit = round(sales - cost, 2)
        order_items.append({
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": prod.product_id,
            "quantity": int(qty),
            "unit_price": prod.unit_price,
            "discount": discount,
            "sales": sales,
            "profit": profit,
        })
        order_total += sales
        order_item_id += 1

    orders.append({
        "order_id": order_id,
        "customer_id": cust,
        "order_date": order_date.strftime("%Y-%m-%d"),
        "ship_date": ship_date.strftime("%Y-%m-%d"),
        "ship_mode": ship_mode,
        "order_total": round(order_total, 2),
    })

    # ~5% return rate at order level
    if random.random() < 0.05:
        returns.append({
            "order_id": order_id,
            "return_date": (ship_date + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            "return_reason": random.choice(
                ["Defective","Wrong Item","No Longer Needed","Better Price Found","Damaged in Shipping"]),
        })

df_orders = pd.DataFrame(orders)
df_order_items = pd.DataFrame(order_items)
df_returns = pd.DataFrame(returns)

# ----------------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------------
df_customers.to_csv(f"{OUT_DIR}/dim_customers.csv", index=False)
df_products.to_csv(f"{OUT_DIR}/dim_products.csv", index=False)
df_orders.to_csv(f"{OUT_DIR}/fact_orders.csv", index=False)
df_order_items.to_csv(f"{OUT_DIR}/fact_order_items.csv", index=False)
df_returns.to_csv(f"{OUT_DIR}/fact_returns.csv", index=False)

print("customers:", df_customers.shape)
print("products:", df_products.shape)
print("orders:", df_orders.shape)
print("order_items:", df_order_items.shape)
print("returns:", df_returns.shape)
print("total sales:", round(df_order_items.sales.sum(), 2))
print("total profit:", round(df_order_items.profit.sum(), 2))
