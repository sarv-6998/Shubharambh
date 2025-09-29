"""
Streamlit Zomato-style mini app (V3: Dark Theme, No Sidebar)

Features:
- Professional dark-themed frontend with button-based navigation.
- Page 1: A minimalist menu with colored blocks for each item.
- Page 2: A clear and editable shopping cart.
- Page 3: A checkout form to collect customer details.
- Page 4: An order confirmation screen with downloadable receipts.
- Modern "toast" notifications for user feedback.
- Saves orders to DB (SQLite or Postgres/Supabase).
"""

import streamlit as st
import pandas as pd
import os
import sqlite3
import uuid
from datetime import datetime
from fpdf import FPDF
import psycopg2
from psycopg2.extras import RealDictCursor
import itertools

# ---------------------- APP CONFIG ----------------------
st.set_page_config(page_title="Shubharambh Snacks", page_icon="🥨", layout="wide")

# ---------------------- DATA & CONSTANTS ----------------------
DELIVERY_CHARGE = 50
DB_MODE = os.getenv("DB_MODE", "SQLITE").upper()
POSTGRES_URL = os.getenv("POSTGRES_URL")

# --- UPDATED MENU (No images or descriptions) ---
MENU = [
    {"id": "item1", "name": "Besan Ladoo", "prices": {"250g": 150, "500g": 300, "1kg": 600}},
    {"id": "item2", "name": "Rava Ladoo", "prices": {"250g": 130, "500g": 260, "1kg": 520}},
    {"id": "item3", "name": "Motichur Ladoo", "prices": {"250g": 130, "500g": 260, "1kg": 520}},
    {"id": "item4", "name": "Sweet Shankarpali", "prices": {"250g": 120, "500g": 240, "1kg": 480}},
    {"id": "item5", "name": "Patal Pohe Chivda", "prices": {"250g": 115, "500g": 230, "1kg": 460}},
    {"id": "item6", "name": "Bhajani Chakli", "prices": {"250g": 150, "500g": 300, "1kg": 600}},
    {"id": "item7", "name": "Olya Naralachi Karanji", "prices": {"250g": 160, "500g": 320, "1kg": 640}},
    {"id": "item8", "name": "Pakatle Chirote", "prices": {"250g": 130, "500g": 260, "1kg": 520}},
    {"id": "item9", "name": "Namkeen Shankarpale", "prices": {"250g": 120, "500g": 240, "1kg": 480}},
    {"id": "item10", "name": "Bhajke Pohe Chiwda", "prices": {"250g": 120, "500g": 240, "1kg": 480}},
    {"id": "item11", "name": "Lasun/Tikhat Shev", "prices": {"250g": 115, "500g": 225, "1kg": 450}},
    {"id": "item12", "name": "Kadboli", "prices": {"250g": 130, "500g": 260, "1kg": 520}},
]
ITEM_COLORS = ["#0077b6", "#023e8a", "#fca311", "#e63946", "#fb8500", "#8ecae6", "#219ebc", "#ffb703", "#a8dadc",
               "#457b9d", "#1d3557", "#f4a261"]


# ---------------------- CUSTOM CSS (Dark Theme) ----------------------
def apply_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

            :root {
                --primary-color: #fca311; /* Bright Orange for accents */
                --secondary-color: #e0e0e0; /* Light grey for text */
                --background-color: #1e1e1e; /* Dark background */
                --text-color: #ffffff; /* White text */
                --card-bg-color: #2a2a2a; /* Slightly lighter card background */
            }

            body, .stApp {
                font-family: 'Poppins', sans-serif;
                background-color: var(--background-color);
                color: var(--text-color);
            }

            .stButton>button {
                border-radius: 20px;
                border: 2px solid var(--primary-color);
                color: var(--primary-color);
                background-color: transparent;
                transition: all 0.3s ease-in-out;
                padding: 8px 20px;
                font-weight: 600;
            }
            .stButton>button:hover {
                background-color: var(--primary-color);
                color: #000000;
            }
            .stButton>button:focus {
                box-shadow: 0 0 0 0.2rem rgba(252, 163, 17, 0.5) !important;
            }

            /* Sidebar styles */
            [data-testid="stSidebar"] {
                display: none;
            }

            /* Card styles */
            .card {
                background-color: var(--card-bg-color);
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
                margin-bottom: 20px;
                height: 100%;
                text-align: center;
            }

            .menu-item-block {
                border-radius: 10px;
                padding: 40px 20px;
                text-align: center;
                margin-bottom: 20px;
            }

            .menu-item-block h3 {
                color: white;
                font-weight: 600;
                margin: 0;
                font-size: 1.5rem;
            }

            h1, h2, h3, h4, h5, h6 {
                color: var(--text-color);
            }

            /* Make radio buttons look better on dark theme */
            .stRadio [role="radiogroup"] {
                justify-content: center;
            }

        </style>
    """, unsafe_allow_html=True)


apply_custom_css()


# ---------------------- DB HELPERS (remains unchanged) ----------------------
@st.cache_resource
def init_db():
    conn = None
    if DB_MODE == "SQLITE":
        conn = sqlite3.connect("orders.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY, created_at TEXT, customer_name TEXT,
                phone TEXT, address TEXT, delivery_type TEXT, items TEXT,
                subtotal REAL, delivery_charge REAL, total REAL
            )
            """
        )
        conn.commit()
    elif DB_MODE == "POSTGRES":
        if not POSTGRES_URL:
            st.error("POSTGRES_URL is not set. Cannot connect to the database.")
            return None
        try:
            conn = psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY, created_at TEXT, customer_name TEXT,
                        phone TEXT, address TEXT, delivery_type TEXT, items TEXT,
                        subtotal REAL, delivery_charge REAL, total REAL
                    )
                    """
                )
            conn.commit()
        except Exception as e:
            st.error(f"Failed to connect to Postgres: {e}")
            return None
    return conn


conn = init_db()


def save_order(order):
    if not conn:
        st.error("Database connection is not available. Cannot save order.")
        return False
    try:
        order_tuple = (
            order['order_id'], order['created_at'], order['customer_name'],
            order['phone'], order['address'], order['delivery_type'],
            order['items_str'], order['subtotal'], order['delivery_charge'], order['total']
        )
        if DB_MODE == "SQLITE":
            cur = conn.cursor()
            cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", order_tuple)
        elif DB_MODE == "POSTGRES":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", order_tuple)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to save order: {e}")
        return False


# ---------------------- RECEIPT HELPERS (remains unchanged) ----------------------
def build_receipt_text(order):
    lines = [f"**RECEIPT - Order ID:** {order['order_id']}", f"**Date:** {order['created_at']}", "\n---\n",
             "**Customer:**", f"  - **Name:** {order['customer_name']}", f"  - **Phone:** {order['phone']}",
             f"  - **Address:** {order['address']}", "\n---\n", "**Items:**"]
    for it in st.session_state.final_order_items:
        lines.append(f"  - {it['name']} ({it['size']}) | Qty: {it['qty']} | Sub: Rs {it['subtotal']:.2f}")
    lines.extend(["\n---\n", f"**Subtotal:** Rs {order['subtotal']:.2f}",
                  f"**Delivery charge:** Rs {order['delivery_charge']:.2f}", f"**Total:** Rs {order['total']:.2f}",
                  "\n---\n", "**Thank you for your order!**"])
    return "\n".join(lines)


def build_receipt_pdf_bytes(order):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    plain_text = build_receipt_text(order).replace("**", "").replace("\n---\n", "\n-------------------------\n")
    for line in plain_text.splitlines():
        pdf.cell(0, 8, line, ln=True)
    return pdf.output(dest="S").encode("latin-1")


# ---------------------- SESSION STATE INITIALIZATION ----------------------
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'final_order_details' not in st.session_state:
    st.session_state.final_order_details = None
if 'final_order_items' not in st.session_state:
    st.session_state.final_order_items = []
if 'page' not in st.session_state:
    st.session_state.page = 'menu'


# ---------------------- UI PAGES ----------------------
def page_menu():
    st.title("🥨 Shubharambh Sweets & Snacks")
    st.markdown("### Authentic homemade treats, made with love.")

    if st.session_state.cart:
        total_items = sum(item['qty'] for item in st.session_state.cart.values())
        if st.button(f"View Cart ({total_items} items) 🛒"):
            st.session_state.page = 'cart'
            st.rerun()

    num_columns = 3

    color_cycle = itertools.cycle(ITEM_COLORS)

    for i in range(0, len(MENU), num_columns):
        cols = st.columns(num_columns)
        for j in range(num_columns):
            if i + j < len(MENU):
                item = MENU[i + j]
                with cols[j]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    item_color = next(color_cycle)
                    st.markdown(f"""
                        <div class="menu-item-block" style="background-color: {item_color};">
                            <h3>{item["name"]}</h3>
                        </div>
                    """, unsafe_allow_html=True)

                    size = st.radio("Size", list(item["prices"].keys()), key=f"size_{item['id']}", horizontal=True)
                    price = item["prices"][size]
                    st.markdown(f"**Price:** <span style='color: var(--primary-color);'>Rs {price:.2f}</span>",
                                unsafe_allow_html=True)

                    if st.button("Add to Cart", key=f"btn_{item['id']}"):
                        key = f"{item['id']}__{size}"
                        if key in st.session_state.cart:
                            st.session_state.cart[key]["qty"] += 1
                        else:
                            st.session_state.cart[key] = {"item_id": item["id"], "name": item["name"], "size": size,
                                                          "unit_price": price, "qty": 1}
                        st.toast(f"Added {item['name']} ({size}) to cart!", icon="🛒")
                        st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)


def page_cart():
    st.title("🛒 Your Shopping Cart")
    if not st.session_state.cart:
        st.info("Your cart is empty.")

    if st.button("⬅️ Back to Menu"):
        st.session_state.page = 'menu'
        st.rerun()

    if not st.session_state.cart:
        return

    cart_items = [{"key": k, "Item": v["name"], "Size": v["size"], "Price": v["unit_price"], "Quantity": v["qty"],
                   "Subtotal": v["unit_price"] * v["qty"]} for k, v in st.session_state.cart.items()]
    df_cart = pd.DataFrame(cart_items)

    st.markdown("### Review Your Items")
    edited_df = st.data_editor(df_cart,
                               column_config={"key": None, "Price": st.column_config.NumberColumn(format="Rs %.2f"),
                                              "Subtotal": st.column_config.NumberColumn(format="Rs %.2f")},
                               disabled=["Item", "Size", "Price", "Subtotal"], hide_index=True)

    for i, row in edited_df.iterrows():
        key = df_cart.loc[i, "key"]
        new_qty = int(row["Quantity"])
        if new_qty <= 0:
            del st.session_state.cart[key]
            st.rerun()
        else:
            st.session_state.cart[key]['qty'] = new_qty

    subtotal = sum(item['Subtotal'] for item in cart_items)
    st.markdown("---")
    st.metric("Subtotal", f"Rs {subtotal:.2f}")

    if st.button("Proceed to Checkout ➡"):
        st.session_state.page = 'checkout'
        st.rerun()


def page_checkout():
    st.title("📝 Customer Details")

    if st.button("⬅️ Back to Cart"):
        st.session_state.page = 'cart'
        st.rerun()

    if not st.session_state.cart:
        st.warning("Your cart is empty. Please add items before checking out.")
        return

    subtotal = sum(v['unit_price'] * v['qty'] for v in st.session_state.cart.values())

    # --- FIX: Moved radio button and total calculation outside the form ---
    delivery_type = st.radio("Delivery Type", ["Home Delivery", "Takeaway"], horizontal=True)
    delivery_charge = DELIVERY_CHARGE if delivery_type == "Home Delivery" else 0
    total = subtotal + delivery_charge

    st.markdown("---")
    st.markdown(f"**Subtotal:** Rs {subtotal:.2f}<br>**Delivery Charge:** Rs {delivery_charge:.2f}",
                unsafe_allow_html=True)
    st.markdown(f"### Total Amount: Rs {total:.2f}")
    st.markdown("---")
    # --- END FIX ---

    with st.form("checkout_form"):
        st.markdown("Please fill in your details to complete the order.")
        name = st.text_input("Full Name *")
        phone = st.text_input("Phone Number *")
        address = st.text_area("Delivery Address *")
        agree = st.checkbox("I confirm the order details are correct.")

        submitted = st.form_submit_button("Place Order")

    if submitted:
        if not (name and phone and address and agree):
            st.error("Please fill all required fields and confirm the order.")
        else:
            order_id = str(uuid.uuid4())[:8]
            st.session_state.final_order_items = [
                {"name": v['name'], "size": v['size'], "qty": v['qty'], "subtotal": v['unit_price'] * v['qty']} for v in
                st.session_state.cart.values()]
            # Use the delivery_type from outside the form for the final order
            order_details = {"order_id": order_id, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "customer_name": name, "phone": phone, "address": address, "delivery_type": delivery_type,
                             "items_str": str(st.session_state.final_order_items), "subtotal": subtotal,
                             "delivery_charge": delivery_charge, "total": total}

            if save_order(order_details):
                st.session_state.final_order_details = order_details
                st.session_state.cart = {}
                st.session_state.page = 'confirmation'
                st.rerun()


def page_confirmation():
    st.title("✅ Order Confirmed!")
    if not st.session_state.final_order_details:
        st.warning("No order details found. Please place an order first.")
        if st.button("⬅️ Back to Menu"):
            st.session_state.page = 'menu'
            st.rerun()
        return

    order = st.session_state.final_order_details
    receipt_text = build_receipt_text(order)
    pdf_bytes = build_receipt_pdf_bytes(order)

    st.success(f"Thank you, {order['customer_name']}! Your order `{order['order_id']}` has been placed successfully.")
    st.balloons()

    st.markdown("### Order Summary")
    st.markdown(receipt_text, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(label="📄 Download Receipt (TXT)", data=receipt_text,
                           file_name=f"receipt_{order['order_id']}.txt")
    with col2:
        st.download_button(label="🧾 Download Receipt (PDF)", data=pdf_bytes,
                           file_name=f"receipt_{order['order_id']}.pdf", mime="application/pdf")

    if st.button("Place Another Order"):
        st.session_state.final_order_details = None
        st.session_state.final_order_items = []
        st.session_state.page = 'menu'
        st.rerun()


# ---------------------- MAIN ROUTER ----------------------
if st.session_state.page == 'menu':
    page_menu()
elif st.session_state.page == 'cart':
    page_cart()
elif st.session_state.page == 'checkout':
    page_checkout()
elif st.session_state.page == 'confirmation':
    page_confirmation()

