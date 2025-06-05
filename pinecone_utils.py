# pinecone_utils.py

import os
import numpy as np
import duckdb
import pandas as pd
import openai
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# 1) Load environment variables
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY     = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME")

if not OPENAI_API_KEY or not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
    raise ValueError("Make sure OPENAI_API_KEY, PINECONE_API_KEY, and PINECONE_ENVIRONMENT are set in .env")

# ─────────────────────────────────────────────────────────────────────────────
# 2) Create a Pinecone client instance
# ─────────────────────────────────────────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# 1) Pull just the “name” fields out of list_indexes()
existing_indexes = [ idx_info["name"] for idx_info in pc.list_indexes() ]

if PINECONE_INDEX_NAME not in existing_indexes:
    parts = PINECONE_ENVIRONMENT.split("-")
    if len(parts) == 2:
        region, cloud = parts[0], parts[1]
    else:
        region, cloud = parts[0], "gcp"

    spec = ServerlessSpec(cloud=cloud, region=region)
    print(f"Creating index '{PINECONE_INDEX_NAME}' (cloud={cloud}, region={region})…")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=spec
    )
else:
    print(f"Index '{PINECONE_INDEX_NAME}' already exists; skipping creation.")

# 2) Now grab the index handle
index = pc.Index(PINECONE_INDEX_NAME)

# ─────────────────────────────────────────────────────────────────────────────
# 3) Helper to get an OpenAI embedding for a given text (updated for openai>=1.0.0)
# ─────────────────────────────────────────────────────────────────────────────
def get_embedding(text: str, model: str = "text-embedding-ada-002") -> np.ndarray:
    openai.api_key = OPENAI_API_KEY
    resp = openai.embeddings.create(model=model, input=[text])
    return np.array(resp.data[0].embedding)

# ─────────────────────────────────────────────────────────────────────────────
# 4) Ingest customer records as embeddings:
#
#    - For each customer, build a text string that includes:
#        “<first_name> <last_name> orders_cancelled=<num_orders_Cancelled>
#         orders_returned=<num_orders_Returned> web_sessions=<num_web_sessions>”
#    - Store as Pinecone vectors with IDs like "cust_<user_id>"
# ─────────────────────────────────────────────────────────────────────────────
def ingest_customer_texts(duckdb_path: str):
    """
    Reads detailed columns from the `customers` table in DuckDB, replaces any NA
    with None, then converts None → "" in metadata so Pinecone accepts it.
    Computes embeddings on all customer attributes and upserts into Pinecone under IDs like "cust_<user_id>".
    """
    import pandas as pd

    con = duckdb.connect(duckdb_path)
    df_cust = con.execute("""
        SELECT
          user_id,
          customer_first_name,
          customer_last_name,
          customer_country,
          customer_acquisition_channel,
          total_amount_spent,
          total_items_purchased,
          first_order_completed_at,
          last_order_completed_at,
          num_orders AS num_orders_total,
          num_orders_Shipped,
          num_orders_Complete,
          num_orders_Processing,
          num_orders_Cancelled,
          num_orders_Returned,
          num_web_sessions
        FROM customers
    """).fetch_df()
    con.close()

    batch_size = 100
    to_upsert = []

    for _, row in df_cust.iterrows():
        uid = int(row["user_id"])
        # Safely extract each field, converting NA/NaN to None
        first_name = row["customer_first_name"] if pd.notna(row["customer_first_name"]) else None
        last_name = row["customer_last_name"] if pd.notna(row["customer_last_name"]) else None
        country = row["customer_country"] if pd.notna(row["customer_country"]) else None
        channel = row["customer_acquisition_channel"] if pd.notna(row["customer_acquisition_channel"]) else None
        total_spent = float(row["total_amount_spent"]) if pd.notna(row["total_amount_spent"]) else None
        total_items = int(row["total_items_purchased"]) if pd.notna(row["total_items_purchased"]) else None
        first_order = str(row["first_order_completed_at"]) if pd.notna(row["first_order_completed_at"]) else None
        last_order = str(row["last_order_completed_at"]) if pd.notna(row["last_order_completed_at"]) else None
        num_total = int(row["num_orders_total"]) if pd.notna(row["num_orders_total"]) else None
        num_shipped = int(row["num_orders_Shipped"]) if pd.notna(row["num_orders_Shipped"]) else None
        num_complete = int(row["num_orders_Complete"]) if pd.notna(row["num_orders_Complete"]) else None
        num_processing = int(row["num_orders_Processing"]) if pd.notna(row["num_orders_Processing"]) else None
        num_cancelled = int(row["num_orders_Cancelled"]) if pd.notna(row["num_orders_Cancelled"]) else None
        num_returned = int(row["num_orders_Returned"]) if pd.notna(row["num_orders_Returned"]) else None
        web_sessions = int(row["num_web_sessions"]) if pd.notna(row["num_web_sessions"]) else None

        # Build a single text string for embedding that includes all fields (skipping None)
        parts = []
        if first_name and last_name:
            parts.append(f"{first_name} {last_name}")
        if country:
            parts.append(f"{country}")
        if channel:
            parts.append(f"acquired_via={channel}")
        if total_spent is not None:
            parts.append(f"spent_total=${total_spent:.2f}")
        if total_items is not None:
            parts.append(f"items_purchased={total_items}")
        if first_order:
            parts.append(f"first_order={first_order}")
        if last_order:
            parts.append(f"last_order={last_order}")
        if num_total is not None:
            parts.append(f"orders_total={num_total}")
        if num_shipped is not None:
            parts.append(f"shipped={num_shipped}")
        if num_complete is not None:
            parts.append(f"complete={num_complete}")
        if num_processing is not None:
            parts.append(f"processing={num_processing}")
        if num_cancelled is not None:
            parts.append(f"cancelled={num_cancelled}")
        if num_returned is not None:
            parts.append(f"returned={num_returned}")
        if web_sessions is not None:
            parts.append(f"web_sessions={web_sessions}")

        text = " ".join(parts)
        vec = get_embedding(text)

        # Build metadata dict, converting None → "" so Pinecone accepts it
        meta = {
            "source": "customer",
            "user_id": uid,
            "first_name": first_name or "",
            "last_name": last_name or "",
            "country": country or "",
            "acquisition_channel": channel or "",
            "total_amount_spent": total_spent if total_spent is not None else 0.0,
            "total_items_purchased": total_items if total_items is not None else 0,
            "first_order_completed_at": first_order or "",
            "last_order_completed_at": last_order or "",
            "num_orders_total": num_total if num_total is not None else 0,
            "num_orders_Shipped": num_shipped if num_shipped is not None else 0,
            "num_orders_Complete": num_complete if num_complete is not None else 0,
            "num_orders_Processing": num_processing if num_processing is not None else 0,
            "num_orders_Cancelled": num_cancelled if num_cancelled is not None else 0,
            "num_orders_Returned": num_returned if num_returned is not None else 0,
            "num_web_sessions": web_sessions if web_sessions is not None else 0,
        }

        to_upsert.append((f"cust_{uid}", vec.tolist(), meta))
        if len(to_upsert) >= batch_size:
            index.upsert(vectors=to_upsert)
            to_upsert = []

    if to_upsert:
        index.upsert(vectors=to_upsert)

    print(f"✅ Embedded {len(df_cust)} customers into Pinecone index `{PINECONE_INDEX_NAME}`")

# ─────────────────────────────────────────────────────────────────────────────
# 5) Ingest product records as embeddings:
#
#    - For each product, build a text string: “<product_name> category=<product_category>”
#    - Store as Pinecone vectors with IDs like "prod_<product_id>"
# ─────────────────────────────────────────────────────────────────────────────
def ingest_product_texts(duckdb_path: str):
    """
    Reads detailed columns from the `products` table in DuckDB, replaces any NULL/NaN
    with safe defaults, computes embeddings based on a concatenation of all product attributes,
    and upserts into Pinecone under IDs like "prod_<product_id>".
    """
    import pandas as pd

    con = duckdb.connect(duckdb_path)
    df_prod = con.execute("""
        SELECT
          product_id,
          product_name,
          product_category,
          sales_amount,
          cost_of_goods_sold,
          (sales_amount - cost_of_goods_sold) AS profit
        FROM products
    """).fetch_df()
    con.close()

    batch_size = 100
    to_upsert = []

    for _, row in df_prod.iterrows():
        pid = int(row["product_id"])
        # Safely extract each field, converting NA/NaN to a default
        name = row["product_name"] if pd.notna(row["product_name"]) else ""
        category = row["product_category"] if pd.notna(row["product_category"]) else ""
        sales = float(row["sales_amount"]) if pd.notna(row["sales_amount"]) else 0.0
        cogs = float(row["cost_of_goods_sold"]) if pd.notna(row["cost_of_goods_sold"]) else 0.0
        profit = float(row["profit"]) if pd.notna(row["profit"]) else (sales - cogs)

        # Build a single text string for embedding that includes all fields
        text = (
            f"{name} "
            f"category={category} "
            f"sales=${sales:.2f} "
            f"cogs=${cogs:.2f} "
            f"profit=${profit:.2f}"
        )
        vec = get_embedding(text)

        # Build metadata dict, replacing any None with safe defaults
        meta = {
            "source": "product",
            "product_id": pid,
            "product_name": name,
            "product_category": category,
            "sales_amount": sales,
            "cost_of_goods_sold": cogs,
            "profit": profit,
        }

        to_upsert.append((f"prod_{pid}", vec.tolist(), meta))
        if len(to_upsert) >= batch_size:
            index.upsert(vectors=to_upsert)
            to_upsert = []

    if to_upsert:
        index.upsert(vectors=to_upsert)

    print(f"✅ Embedded {len(df_prod)} products into Pinecone index `{PINECONE_INDEX_NAME}`")

# ─────────────────────────────────────────────────────────────────────────────
# 5b) Ingest distribution center inventory records as embeddings
# ─────────────────────────────────────────────────────────────────────────────
def ingest_distribution_center_inventory(duckdb_path: str):
    """Embed rows from the distribution_center_inventory table."""
    import pandas as pd

    con = duckdb.connect(duckdb_path)
    df_dci = con.execute(
        """
            SELECT
              distribution_center_id,
              distribution_center_name,
              total_items,
              items_sold,
              items_in_stock,
              total_sales,
              total_inventory_cost
            FROM distribution_center_inventory
        """
    ).fetch_df()
    con.close()

    batch_size = 100
    to_upsert = []

    for _, row in df_dci.iterrows():
        dc_id = int(row["distribution_center_id"])
        name = row["distribution_center_name"] if pd.notna(row["distribution_center_name"]) else ""
        total_items = int(row["total_items"]) if pd.notna(row["total_items"]) else 0
        items_sold = int(row["items_sold"]) if pd.notna(row["items_sold"]) else 0
        items_in_stock = int(row["items_in_stock"]) if pd.notna(row["items_in_stock"]) else 0
        total_sales = float(row["total_sales"]) if pd.notna(row["total_sales"]) else 0.0
        inv_cost = float(row["total_inventory_cost"]) if pd.notna(row["total_inventory_cost"]) else 0.0

        text = (
            f"{name} items_in_stock={items_in_stock} "
            f"total_sales=${total_sales:.2f} inventory_cost=${inv_cost:.2f}"
        )
        vec = get_embedding(text)

        meta = {
            "source": "distribution_center_inventory",
            "distribution_center_id": dc_id,
            "distribution_center_name": name,
            "total_items": total_items,
            "items_sold": items_sold,
            "items_in_stock": items_in_stock,
            "total_sales": total_sales,
            "total_inventory_cost": inv_cost,
        }

        to_upsert.append((f"dc_{dc_id}", vec.tolist(), meta))
        if len(to_upsert) >= batch_size:
            index.upsert(vectors=to_upsert)
            to_upsert = []

    if to_upsert:
        index.upsert(vectors=to_upsert)

    print(f"✅ Embedded {len(df_dci)} distribution centers into Pinecone index `{PINECONE_INDEX_NAME}`")

# ─────────────────────────────────────────────────────────────────────────────
# 5c) Ingest monthly sales records as embeddings
# ─────────────────────────────────────────────────────────────────────────────
def ingest_monthly_sales(duckdb_path: str):
    """Embed rows from the monthly_sales table."""
    import pandas as pd

    con = duckdb.connect(duckdb_path)
    df_ms = con.execute(
        """
            SELECT month, num_orders, items_ordered, revenue
            FROM monthly_sales
        """
    ).fetch_df()
    con.close()

    batch_size = 100
    to_upsert = []

    for _, row in df_ms.iterrows():
        month_val = str(row["month"])
        num_orders = int(row["num_orders"]) if pd.notna(row["num_orders"]) else 0
        items_ordered = int(row["items_ordered"]) if pd.notna(row["items_ordered"]) else 0
        revenue = float(row["revenue"]) if pd.notna(row["revenue"]) else 0.0

        text = (
            f"month={month_val} orders={num_orders} "
            f"items={items_ordered} revenue=${revenue:.2f}"
        )
        vec = get_embedding(text)

        meta = {
            "source": "monthly_sales",
            "month": month_val,
            "num_orders": num_orders,
            "items_ordered": items_ordered,
            "revenue": revenue,
        }

        to_upsert.append((f"month_{month_val}", vec.tolist(), meta))
        if len(to_upsert) >= batch_size:
            index.upsert(vectors=to_upsert)
            to_upsert = []

    if to_upsert:
        index.upsert(vectors=to_upsert)

    print(f"✅ Embedded {len(df_ms)} monthly sales rows into Pinecone index `{PINECONE_INDEX_NAME}`")

# ─────────────────────────────────────────────────────────────────────────────
# 6) A simple semantic‐search example
# ─────────────────────────────────────────────────────────────────────────────
def semantic_search(query: str, top_k: int = 3):
    """
    Returns a list of top_k Pinecone matches for the user query.
    Each match: { "id": ..., "score": ..., "metadata": {...} }
    """
    emb = get_embedding(query)
    results = index.query(emb.tolist(), top_k=top_k, include_metadata=True)
    return results["matches"]

# ─────────────────────────────────────────────────────────────────────────────
# 7) If you run this script directly, only ingest customers & products
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Adjust this path if your DuckDB file lives elsewhere
    duckdb_path = os.path.join(os.path.dirname(__file__), "data/data.db")

    # 1) Embed all customers
    ingest_customer_texts(duckdb_path)

    # 2) Embed all products
    ingest_product_texts(duckdb_path)

    # 3) Embed distribution center inventory
    ingest_distribution_center_inventory(duckdb_path)

    # 4) Embed monthly sales
    ingest_monthly_sales(duckdb_path)

    # 5) Quick test of semantic search
    print("\nExample search for “top customers” →")
    matches = semantic_search("Which customers have high web_sessions?", top_k=3)
    for m in matches:
        print(f" • ID={m['id']}, score={m['score']:.3f}, metadata={m['metadata']}")