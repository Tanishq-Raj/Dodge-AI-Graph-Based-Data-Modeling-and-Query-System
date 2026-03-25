from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import sqlite3
import json
import re
from openai import OpenAI

app = FastAPI(title="Dodge AI API")

# Connect to database
DB_PATH = "data.db"
try:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
except Exception as e:
    print(f"Error connecting to DB: {e}")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
# LLM Setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "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"),
    default_headers={
        "HTTP-Referer": "https://dodge-ai-graph.com",
        "X-Title": "Dodge AI"
    }
)

# =========================
# HELPER FUNCTIONS
# =========================
def get_schema():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema = ""
        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
            columns = df['name'].tolist()
            schema += f"{table_name}({', '.join(columns)})\n"
        return schema
    except Exception as e:
        return f"Error reading schema: {e}"

def get_columns(table_name: str) -> list[str]:
    """Get exact column names from a table for schema validation."""
    try:
        df = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
        return df['name'].tolist()
    except:
        return []

def clean_sql(sql_text):
    match = re.search(r"```sql(.*?)```", sql_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"(SELECT .*?;)", sql_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    lines = sql_text.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("#") or line.startswith("--") or line == "":
            continue
        clean_lines.append(line)
    return " ".join(clean_lines).strip()

def get_highlights(data: list) -> list[str]:
    """Exact node highlighting directly from matched SQL tuples."""
    nodes = set()
    fields_to_check = ['salesOrder', 'deliveryDocument', 'billingDocument', 'journalEntry', 'paymentDoc', 'clearingAccountingDocument']
    for r in data:
        for field in fields_to_check:
            if r.get(field):
                nodes.add(str(r[field]))
    return list(nodes)

# =======================================
# 🧠 LLM INTENT DETECTION (CORE AI)
# =======================================
INTENT_PROMPT = """You are an ERP query understanding engine for SAP Order-to-Cash data.

Extract the intent and entities from the user query.
Return ONLY valid JSON, nothing else.

Intents:
- trace_order: trace/flow of a specific document (order, delivery, billing, journal)
- show_orders: list sales orders
- show_deliveries: list deliveries
- show_billing: list billing/invoice documents
- show_products: list products
- show_customers: list customers/business partners
- show_journals: list journal entries
- orders_without_invoice: orders not billed / incomplete flows
- top_billed: top/highest billed products or materials
- billing_analysis: revenue, amount, billing stats
- customer_revenue: revenue per customer
- explain: explain a transaction or why something happened
- fraud_check: detect anomalies, fraud, suspicious transactions
- general: anything else

Entity fields to extract (if present):
- order_id: sales order number
- delivery_id: delivery document number
- billing_id: billing document number
- journal_id: journal entry / accounting document number
- product_id: material / product ID
- customer_id: business partner ID

Examples:
Query: "show all orders"
Output: {"intent":"show_orders","entities":{}}

Query: "trace order 740509"
Output: {"intent":"trace_order","entities":{"order_id":"740509"}}

Query: "trace billing doc 91150187"
Output: {"intent":"trace_order","entities":{"billing_id":"91150187"}}

Query: "top billed products"
Output: {"intent":"top_billed","entities":{}}

Query: "explain transaction 91150187"
Output: {"intent":"explain","entities":{"billing_id":"91150187"}}

Query: "find fraud"
Output: {"intent":"fraud_check","entities":{}}

Query: "orders without invoices"
Output: {"intent":"orders_without_invoice","entities":{}}

Query: "customer revenue"
Output: {"intent":"customer_revenue","entities":{}}

Query: "journal entries"
Output: {"intent":"show_journals","entities":{}}

Now process this query:
Query: "{query}"
"""

def detect_intent(query: str) -> dict:
    """Use LLM to detect intent and extract entities from user query."""
    try:
        res = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "You extract intent and entities from ERP queries. Return ONLY valid JSON."},
                {"role": "user", "content": INTENT_PROMPT.replace("{query}", query)}
            ],
            temperature=0,
            max_tokens=200
        )
        raw = res.choices[0].message.content.strip()
        # Clean any markdown wrapping
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        print(f"🧠 INTENT DETECTED: {result}")
        return result
    except Exception as e:
        print(f"❌ Intent detection failed: {e}")
        # Fallback: simple keyword detection
        q = query.lower()
        if "trace" in q or "flow" in q:
            import re
            match = re.search(r'\d+', q)
            doc_id = match.group(0) if match else None
            entities = {}
            if doc_id:
                entities["order_id"] = doc_id
            return {"intent": "trace_order", "entities": entities}
        if "fraud" in q or "anomal" in q: return {"intent": "fraud_check", "entities": {}}
        if "explain" in q: return {"intent": "explain", "entities": {}}
        if "top" in q or "highest" in q: return {"intent": "top_billed", "entities": {}}
        if "incomplete" in q or "not billed" in q: return {"intent": "orders_without_invoice", "entities": {}}
        if "journal" in q: return {"intent": "show_journals", "entities": {}}
        if "customer" in q and "revenue" in q: return {"intent": "customer_revenue", "entities": {}}
        if "order" in q: return {"intent": "show_orders", "entities": {}}
        if "delivery" in q: return {"intent": "show_deliveries", "entities": {}}
        if "billing" in q or "invoice" in q: return {"intent": "show_billing", "entities": {}}
        if "product" in q: return {"intent": "show_products", "entities": {}}
        if "customer" in q: return {"intent": "show_customers", "entities": {}}
        return {"intent": "general", "entities": {}}

# =======================================
# 📝 INTENT-BASED SQL GENERATION
# =======================================
def _get_doc_id(entities: dict) -> str:
    """Extract any document ID from entities."""
    for key in ['order_id', 'delivery_id', 'billing_id', 'journal_id']:
        if entities.get(key):
            return entities[key]
    return ""

def _build_trace_sql(doc_id: str = "") -> str:
    where = ""
    if doc_id:
        where = f"WHERE so.salesOrder='{doc_id}' OR odi.deliveryDocument='{doc_id}' OR bdi.billingDocument='{doc_id}' OR je.accountingDocument='{doc_id}'"
    return f"""
    SELECT
        so.salesOrder,
        MAX(odi.deliveryDocument) as deliveryDocument,
        MAX(bdi.billingDocument) as billingDocument,
        MAX(je.accountingDocument) as journalEntry,
        MAX(par.clearingAccountingDocument) as paymentDoc
    FROM sales_order_headers so
    LEFT JOIN outbound_delivery_items odi ON so.salesOrder = odi.referenceSDDocument
    LEFT JOIN billing_document_items bdi ON odi.deliveryDocument = bdi.referenceSdDocument
    LEFT JOIN journal_entry_items_accounts_receivable je ON bdi.billingDocument = je.referenceDocument
    LEFT JOIN payments_accounts_receivable par ON je.accountingDocument = par.accountingDocument
    {where}
    GROUP BY so.salesOrder
    LIMIT 50
    """

def generate_sql_from_intent(intent: str, entities: dict) -> str:
    """Generate deterministic SQL based on detected intent + entities."""
    doc_id = _get_doc_id(entities)

    if intent == "trace_order":
        return _build_trace_sql(doc_id)

    if intent == "explain":
        return _build_trace_sql(doc_id)

    if intent == "fraud_check":
        return _build_trace_sql()  # Scan all flows for anomalies

    if intent == "orders_without_invoice":
        return """
        SELECT DISTINCT so.salesOrder
        FROM sales_order_headers so
        LEFT JOIN outbound_delivery_items odi ON so.salesOrder = odi.referenceSDDocument
        LEFT JOIN billing_document_items bdi ON odi.deliveryDocument = bdi.referenceSdDocument
        WHERE bdi.billingDocument IS NULL
        """

    if intent == "top_billed":
        return """
        SELECT material, COUNT(*) as total_bills
        FROM billing_document_items
        GROUP BY material ORDER BY total_bills DESC LIMIT 5
        """

    if intent == "customer_revenue":
        return """
        SELECT bp.businessPartnerFullName as customer, SUM(bh.totalNetAmount) as revenue
        FROM billing_document_headers bh
        JOIN business_partners bp ON bh.soldToParty = bp.businessPartner
        GROUP BY bp.businessPartnerFullName ORDER BY revenue DESC LIMIT 10
        """

    if intent == "show_orders":
        return "SELECT salesOrder, soldToParty, totalNetAmount, overallDeliveryStatus, creationDate FROM sales_order_headers LIMIT 20"

    if intent == "show_deliveries":
        return "SELECT deliveryDocument, shippingPoint, overallGoodsMovementStatus, creationDate FROM outbound_delivery_headers LIMIT 20"

    if intent == "show_billing":
        return "SELECT billingDocument, billingDocumentType, totalNetAmount, transactionCurrency, billingDocumentDate FROM billing_document_headers LIMIT 20"

    if intent == "show_journals":
        return "SELECT accountingDocument, referenceDocument, amountInTransactionCurrency, transactionCurrency, postingDate FROM journal_entry_items_accounts_receivable LIMIT 20"

    if intent == "show_products":
        return "SELECT product, productGroup FROM products LIMIT 20"

    if intent == "show_customers":
        return "SELECT businessPartner, businessPartnerFullName FROM business_partners LIMIT 20"

    # GENERAL — Use LLM to generate SQL
    prompt = f"Generate ONLY a single SQL query for SQLite.\n\nSchema:\n{get_schema()}\n\nQuery: {entities.get('original_query', 'show data')}"
    try:
        res = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "system", "content": "Return ONLY SQL, no explanation."}, {"role": "user", "content": prompt}],
            temperature=0
        )
        return clean_sql(res.choices[0].message.content.strip())
    except Exception as e:
        print(f"LLM SQL gen error: {e}")
        return "SELECT 'Could not generate SQL' as error;"

# =======================================
# 💬 LLM SUMMARY GENERATION
# =======================================
def generate_llm_summary(query: str, result_data: list) -> str:
    """Use LLM to create a clean natural language summary of SQL results."""
    if not result_data or len(result_data) == 0:
        return "No data found for this query."
    try:
        # Limit data sent to LLM to avoid token overflow
        sample = result_data[:5]
        res = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an ERP data analyst. Summarize SQL results in 1-3 sentences for a business user. Be specific about numbers and IDs. Use **bold** for important values. Never show raw SQL or tables."},
                {"role": "user", "content": f"User asked: \"{query}\"\n\nResult data:\n{json.dumps(sample, indent=2, default=str)}\n\nTotal rows: {len(result_data)}\n\nSummarize clearly:"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        summary = res.choices[0].message.content.strip()
        print(f"💬 LLM SUMMARY: {summary}")
        return summary
    except Exception as e:
        print(f"❌ LLM Summary failed: {e}")
        return None  # Will fallback to rule-based

# =======================================
# 🎯 RESPONSE GENERATION (INTENT-BASED)
# =======================================
def generate_response_from_intent(intent: str, entities: dict, query: str, df) -> dict:
    """Generate structured response based on intent — uses LLM summary with rule-based fallback."""
    import pandas as pd

    if df is None or (isinstance(df, pd.DataFrame) and df.empty) or (isinstance(df, list) and len(df) == 0):
        return {"type": "table", "answer": "No data found for this query.", "data": []}

    if isinstance(df, list) and len(df) > 0 and "error" in df[0]:
        error_msg = df[0].get("error", "Unknown SQL error")
        return {"type": "error", "answer": f"⚠️ Query failed: {error_msg}", "data": []}

    if isinstance(df, list):
        df = pd.DataFrame(df)

    records = df.to_dict(orient="records")

    # Try LLM summary first
    llm_answer = generate_llm_summary(query, records)

    # TRACE
    if intent == "trace_order":
        fallback = "Showing complete document flow from Sales Order → Delivery → Billing → Journal Entry."
        return {"type": "flow", "answer": llm_answer or fallback, "data": records}

    # EXPLAIN
    if intent == "explain":
        if records:
            r = records[0]
            parts = []
            if r.get('salesOrder'): parts.append(f"Sales Order **{r['salesOrder']}**")
            if r.get('deliveryDocument'): parts.append(f"Delivery **{r['deliveryDocument']}**")
            if r.get('billingDocument'): parts.append(f"Billing Document **{r['billingDocument']}**")
            if r.get('journalEntry'): parts.append(f"Journal Entry **{r['journalEntry']}**")
            if r.get('paymentDoc'): parts.append(f"Payment **{r['paymentDoc']}**")
            fallback = f"This transaction flows through: {' → '.join(parts)}."
        else:
            fallback = "No transaction data found."
        return {"type": "explanation", "answer": llm_answer or fallback, "data": records}

    # FRAUD CHECK
    if intent == "fraud_check":
        flagged = []
        for r in records:
            if r.get('billingDocument') is None and r.get('salesOrder'):
                flagged.append({"salesOrder": r['salesOrder'], "issue": "⚠️ No billing document found"})
            if r.get('journalEntry') is None and r.get('billingDocument'):
                flagged.append({"billingDocument": r['billingDocument'], "issue": "⚠️ No journal entry posted"})
            if r.get('paymentDoc') is None and r.get('journalEntry'):
                flagged.append({"journalEntry": r['journalEntry'], "issue": "⚠️ Payment not cleared"})
        if len(flagged) == 0:
            return {"type": "fraud", "answer": "✅ No suspicious transactions detected. All flows are complete.", "data": []}
        return {"type": "fraud", "answer": f"🚨 Detected **{len(flagged)}** suspicious transactions with missing links.", "data": flagged}

    # AGGREGATION / TOP
    if intent == "top_billed":
        top = df.iloc[0]
        cols = df.columns
        fallback = f"Top result is **{top[cols[0]]}** with value **{top[cols[1]] if len(cols) > 1 else ''}**"
        return {"type": "bar", "answer": llm_answer or fallback, "data": records}

    if intent == "customer_revenue":
        return {"type": "bar", "answer": llm_answer or f"Showing revenue for {len(records)} customers.", "data": records}

    # DEFAULT TABLE
    fallback = f"Showing {len(df)} records based on your query."
    return {"type": "table", "answer": llm_answer or fallback, "data": df.head(20).to_dict(orient="records")}

def run_sql(sql: str):
    try:
        sql = sql.split(';')[0].strip() + ";"
        print(f"🔥 EXECUTING SQL: {sql}")
        df = pd.read_sql_query(sql, conn)
        print(f"✅ SQL SUCCESS: {len(df)} rows returned")
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"❌ SQL ERROR: {e}")
        print(f"❌ FAILED SQL: {sql}")
        return [{"error": str(e)}]

class QueryResponse(BaseModel):
    query: str
    sql: str
    result: list[dict]
    highlights: list[str]
    answer: str
    type: str
    intent: str

@app.get("/query", response_model=QueryResponse)
async def process_query(q: str):
    # Guardrail: out-of-scope queries
    if any(x in q.lower() for x in ["weather", "poem", "who is", "joke"]):
        return QueryResponse(
            query=q, sql="N/A", result=[], highlights=[],
            answer="This system only supports dataset queries.",
            type="table", intent="🚫 Out of Scope"
        )
    
    # 🧠 STEP 1: LLM Intent Detection
    intent_result = detect_intent(q)
    intent = intent_result.get("intent", "general")
    entities = intent_result.get("entities", {})
    entities["original_query"] = q  # Keep original for LLM SQL fallback
    
    print(f"\n{'='*50}")
    print(f"📝 USER QUERY: {q}")
    print(f"🧠 INTENT: {intent} | ENTITIES: {entities}")
    
    # 📝 STEP 2: Intent-Based SQL Generation
    sql = generate_sql_from_intent(intent, entities)
    print(f"🔧 GENERATED SQL: {sql}")
    print(f"{'='*50}")
    
    # ⚡ STEP 3: Execute SQL
    result_data = run_sql(sql)
    
    # 🔗 STEP 4: Conditional Graph Highlights
    # ONLY highlight for trace/explain intents — NOT every query
    GRAPH_INTENTS = {"trace_order", "explain"}
    if intent in GRAPH_INTENTS:
        highlights = get_highlights(result_data)
    else:
        highlights = []
    
    # 🎯 STEP 5: Generate Response
    has_error = isinstance(result_data, list) and len(result_data) > 0 and "error" in result_data[0]
    if has_error:
        df = result_data
    else:
        df = pd.DataFrame(result_data) if isinstance(result_data, list) else result_data
    
    resp_obj = generate_response_from_intent(intent, entities, q, df)
    resp_type = resp_obj.get("type", "table")
    
    # Map type to user-readable intent badge
    intent_map = {
        "bar": "📊 Aggregation",
        "flow": "🔗 Flow Trace",
        "line": "📈 Trend",
        "distribution": "🥧 Distribution",
        "table": "🔍 Lookup",
        "error": "⚠️ Error",
        "explanation": "🧠 Explanation",
        "fraud": "🚨 Fraud Check"
    }
    
    return QueryResponse(
        query=q,
        sql=sql,
        result=resp_obj.get("data", []),
        highlights=highlights,
        answer=resp_obj.get("answer", "Processing completed."),
        type=resp_type,
        intent=intent_map.get(resp_type, "🔍 Lookup")
    )

@app.get("/health")
def health_endpoint():
    return {"status": "ok"}

@app.get("/stats")
def stats_endpoint():
    try:
        orders = conn.execute("SELECT COUNT(*) FROM sales_order_headers").fetchone()[0]
        deliveries = conn.execute("SELECT COUNT(*) FROM outbound_delivery_headers").fetchone()[0]
        billing = conn.execute("SELECT COUNT(*) FROM billing_document_headers").fetchone()[0]
        journals = conn.execute("SELECT COUNT(*) FROM journal_entry_items_accounts_receivable").fetchone()[0]
        return {"orders": orders, "deliveries": deliveries, "billing": billing, "journals": journals}
    except Exception:
        return {"orders": 0, "deliveries": 0, "billing": 0, "journals": 0}

# ==============================
# NODE DETAILS API
# ==============================
@app.get("/node-details/{node_id}")
def node_details(node_id: str):
    """Fetch full details of any node by ID — auto-detects type."""
    try:
        # Try Sales Order
        df = pd.read_sql_query(f"SELECT * FROM sales_order_headers WHERE salesOrder='{node_id}'", conn)
        if len(df) > 0:
            return {"type": "SalesOrder", "data": df.iloc[0].to_dict()}
        
        # Try Delivery
        df = pd.read_sql_query(f"SELECT * FROM outbound_delivery_headers WHERE deliveryDocument='{node_id}'", conn)
        if len(df) > 0:
            return {"type": "Delivery", "data": df.iloc[0].to_dict()}

        # Try Billing Document
        df = pd.read_sql_query(f"SELECT * FROM billing_document_headers WHERE billingDocument='{node_id}'", conn)
        if len(df) > 0:
            return {"type": "BillingDoc", "data": df.iloc[0].to_dict()}

        # Try Journal Entry
        df = pd.read_sql_query(f"SELECT * FROM journal_entry_items_accounts_receivable WHERE accountingDocument='{node_id}' LIMIT 1", conn)
        if len(df) > 0:
            return {"type": "JournalEntry", "data": df.iloc[0].to_dict()}

        # Try Payment
        df = pd.read_sql_query(f"SELECT * FROM payments_accounts_receivable WHERE accountingDocument='{node_id}' LIMIT 1", conn)
        if len(df) > 0:
            return {"type": "Payment", "data": df.iloc[0].to_dict()}

        # Try Customer
        df = pd.read_sql_query(f"SELECT * FROM business_partners WHERE businessPartner='{node_id}'", conn)
        if len(df) > 0:
            return {"type": "Customer", "data": df.iloc[0].to_dict()}

        # Try Product
        clean_id = node_id.replace('prod_', '')
        df = pd.read_sql_query(f"SELECT * FROM products WHERE product='{clean_id}'", conn)
        if len(df) > 0:
            return {"type": "Product", "data": df.iloc[0].to_dict()}

        return {"type": "unknown", "data": {"id": node_id, "message": "Node not found in any table."}}
    except Exception as e:
        return {"type": "error", "data": {"error": str(e)}}

# ==============================
# FRAUD CHECK API
# ==============================
@app.get("/fraud-check")
def fraud_check_endpoint():
    """Run anomaly detection across the full O2C pipeline."""
    flagged = []
    try:
        # 1. Orders without delivery
        df = pd.read_sql_query("""
            SELECT so.salesOrder FROM sales_order_headers so
            LEFT JOIN outbound_delivery_items odi ON so.salesOrder = odi.referenceSDDocument
            WHERE odi.deliveryDocument IS NULL
        """, conn)
        for _, r in df.iterrows():
            flagged.append({"id": str(r['salesOrder']), "type": "SalesOrder", "issue": "⚠️ Order has no delivery"})

        # 2. Deliveries without billing
        df = pd.read_sql_query("""
            SELECT DISTINCT odi.deliveryDocument FROM outbound_delivery_items odi
            LEFT JOIN billing_document_items bdi ON odi.deliveryDocument = bdi.referenceSdDocument
            WHERE bdi.billingDocument IS NULL AND odi.deliveryDocument IS NOT NULL
        """, conn)
        for _, r in df.iterrows():
            flagged.append({"id": str(r['deliveryDocument']), "type": "Delivery", "issue": "⚠️ Delivery has no billing"})

        # 3. Large negative journal entries
        df = pd.read_sql_query("""
            SELECT accountingDocument, amountInTransactionCurrency, transactionCurrency
            FROM journal_entry_items_accounts_receivable
            WHERE amountInTransactionCurrency < -50000
        """, conn)
        for _, r in df.iterrows():
            flagged.append({"id": str(r['accountingDocument']), "type": "JournalEntry",
                "issue": f"🚨 Large negative amount: {r['amountInTransactionCurrency']} {r['transactionCurrency']}"})

        # 4. Cancelled billing documents
        df = pd.read_sql_query("""
            SELECT billingDocument FROM billing_document_headers
            WHERE billingDocumentIsCancelled = 1
        """, conn)
        for _, r in df.iterrows():
            flagged.append({"id": str(r['billingDocument']), "type": "BillingDoc", "issue": "❌ Billing document was cancelled"})

    except Exception as e:
        print(f"Fraud check error: {e}")

    return {
        "total": len(flagged),
        "flagged": flagged,
        "highlight_nodes": [f["id"] for f in flagged[:20]]
    }

@app.get("/graph")
def graph_endpoint():
    nodes = []
    edges = []
    try:
        # Customers
        df_cust = pd.read_sql_query("SELECT businessPartner as id, businessPartnerFullName as label FROM business_partners WHERE businessPartner IS NOT NULL", conn)
        for _, row in df_cust.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['label']), "type": "Customer", "entity": "Customer"}})

        # Sales Orders
        df_so = pd.read_sql_query("SELECT salesOrder as id, soldToParty FROM sales_order_headers", conn)
        for _, row in df_so.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['id']), "type": "SalesOrder", "entity": "Sales Order"}})
            if pd.notna(row['soldToParty']):
                edges.append({"data": {"source": str(row['soldToParty']), "target": str(row['id']), "rel": "PLACED_ORDER"}})

        # Products
        df_prod = pd.read_sql_query("SELECT product as id, productGroup FROM products", conn)
        for _, row in df_prod.iterrows():
            nodes.append({"data": {"id": f"prod_{row['id']}", "label": str(row['id']), "type": "Product", "entity": "Product"}})

        # SO Items
        df_soi = pd.read_sql_query("SELECT salesOrder, salesOrderItem as id, material FROM sales_order_items", conn)
        for _, row in df_soi.iterrows():
            item_id = f"{row['salesOrder']}-{row['id']}"
            nodes.append({"data": {"id": item_id, "label": str(row['id']), "type": "SOItem", "entity": "Sales Order Item"}})
            if pd.notna(row['salesOrder']):
                edges.append({"data": {"source": str(row['salesOrder']), "target": item_id, "rel": "HAS_ITEM"}})
            if pd.notna(row['material']):
                edges.append({"data": {"source": item_id, "target": f"prod_{row['material']}", "rel": "USES_MATERIAL"}})

        # Deliveries
        df_del = pd.read_sql_query("SELECT deliveryDocument as id FROM outbound_delivery_headers", conn)
        for _, row in df_del.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['id']), "type": "Delivery", "entity": "Delivery"}})
            
        df_del_edge = pd.read_sql_query("SELECT referenceSDDocument as so, deliveryDocument as del FROM outbound_delivery_items WHERE referenceSDDocument IS NOT NULL", conn)
        edge_set = set()
        for _, row in df_del_edge.iterrows():
            edge_id = f"{row['so']}-{row['del']}"
            if edge_id not in edge_set:
                edges.append({"data": {"source": str(row['so']), "target": str(row['del']), "rel": "HAS_DELIVERY"}})
                edge_set.add(edge_id)

        # Billing Docs
        df_bill = pd.read_sql_query("SELECT billingDocument as id FROM billing_document_headers", conn)
        for _, row in df_bill.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['id']), "type": "BillingDoc", "entity": "Billing Document"}})
            
        df_bill_edge = pd.read_sql_query("SELECT referenceSDDocument as del, billingDocument as bill FROM billing_document_items WHERE referenceSDDocument IS NOT NULL", conn)
        edge_set = set()
        for _, row in df_bill_edge.iterrows():
            edge_id = f"{row['del']}-{row['bill']}"
            if edge_id not in edge_set:
                edges.append({"data": {"source": str(row['del']), "target": str(row['bill']), "rel": "HAS_BILLING"}})
                edge_set.add(edge_id)

        # Journal Entries
        df_je = pd.read_sql_query("SELECT accountingDocument as id, referenceDocument FROM journal_entry_items_accounts_receivable", conn)
        for _, row in df_je.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['id']), "type": "JournalEntry", "entity": "Journal Entry"}})
            if pd.notna(row['referenceDocument']):
                edges.append({"data": {"source": str(row['referenceDocument']), "target": str(row['id']), "rel": "HAS_JOURNAL"}})

        # Payments
        df_pay = pd.read_sql_query("SELECT accountingDocument as id, clearingAccountingDocument FROM payments_accounts_receivable", conn)
        for _, row in df_pay.iterrows():
            nodes.append({"data": {"id": str(row['id']), "label": str(row['id']), "type": "Payment", "entity": "Payment"}})
            if pd.notna(row['clearingAccountingDocument']):
                edges.append({"data": {"source": str(row['clearingAccountingDocument']), "target": str(row['id']), "rel": "CLEARED_BY"}})
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Graph error", e)
    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
