import streamlit as st
from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI  # ✅ use langchain_community (per warning)
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage  # ✅ use correct message types
from datetime import datetime
import pandas as pd
import re


def is_confirmation(text):
    return bool(re.search(r"\b(Yes|yes|confirm|Confirm|finalize|sure|go ahead|y|Y)\b", text.strip().lower()))


def extract_order_details(text):
    match = re.search(
        r"Full Name:\s*(.+?)\s*Ordered Items:\s*(.+?)\s*Pickup Time:\s*(.+?)\s*---",
        text,
        re.DOTALL
    )
    if match:
        return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
    return None, None, None


ORDERS_FILE = "orders.xlsx"

def append_order_to_excel(name, items, time):
    new_order = {
        "Customer Name": name,
        "Order Items": items,
        "Pickup Time": time,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        if os.path.exists(ORDERS_FILE):
            df = pd.read_excel(ORDERS_FILE, engine="openpyxl")
            df = pd.concat([df, pd.DataFrame([new_order])], ignore_index=True)
        else:
            df = pd.DataFrame([new_order])

        df.to_excel(ORDERS_FILE, index=False, engine="openpyxl")  # ✅ set engine
    except Exception as e:
        st.error(f"❌ Error writing to Excel: {e}")


# Example: store hours config (you can expand to Sunday–Saturday)
BUSINESS_HOURS = {
    "Monday": ("11:00", "21:00"),
    "Tuesday": ("11:00", "21:00"),
    "Wednesday": ("11:00", "21:00"),
    "Thursday": ("11:00", "21:00"),
    "Friday": ("11:00", "22:00"),
    "Saturday": ("00:00", "22:00"),
    "Sunday": ("00:00", "20:00")
}

FAQ_TEXT = """
Frequently Asked Questions (FAQ):

1. What are your hours?
   - We are open Monday to Friday from 11:00 AM to 9:00 PM, Saturday from 12:00 PM to 10:00 PM, and Sunday from 12:00 PM to 8:00 PM.

2. What drinks do you offer?
   - Thai Iced Tea, Thai Iced Coffee, Coconut Water, Lemongrass Tea, Mango Smoothie, Jasmine Tea.

3. Is the Pad Thai vegetarian?
   - By default, it comes with shrimp. You may request tofu or chicken instead.

4. Do you offer gluten-free options?
   - Yes, we can customize dishes to be gluten-free upon request.

5. Do you have vegan options?
   - Yes! Vegan options include Tofu Pad Thai, Vegetable Spring Rolls, and Green Curry with tofu.
"""


def is_store_open():
    now = datetime.now()
    weekday = now.strftime("%A")
    open_time, close_time = BUSINESS_HOURS.get(weekday, (None, None))

    if not open_time or not close_time:
        return False

    current_time = now.strftime("%H:%M")
    return open_time <= current_time <= close_time

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# Custom system prompt
prompt = PromptTemplate.from_template(f"""
You are an AI assistant helping a small Thai restaurant manage orders via SMS.

In addition to taking orders, you can also answer customer questions based on the following FAQ:

{FAQ_TEXT}

Your job is to:
1. Extract the customer's full name.
2. Extract the order items.
3. Extract the desired pickup time.
4. Answer any customer questions using the FAQ above.

Keep track of what information you have, and politely ask for any missing pieces.
Once all 3 pieces are received, ask if the customer wants to confirm the order.

Only after they say "Yes" or something similar, finalize the order and output it in the following format **exactly** (so we can save it):

---
Full Name: [name]  
Ordered Items: [items]  
Pickup Time: [time]  
---

Then generate a friendly confirmation message.

Conversation history:
{{history}}

Customer: {{input}}
AI:
""")


# Initialize memory once
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)

# Setup the conversational chain
conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    memory=st.session_state.memory,
    verbose=False
)

# Streamlit UI
st.title("📲 AI Order Assistant — Missed Call Demo")

if st.button("📞 Simulate Missed Call"):
    st.session_state.memory.clear()
    st.success("Missed call detected. Auto-reply text sent!")
    if is_store_open():
        auto_reply = """
        > **Outgoing Auto-Reply:**  
        Hi, thank you for calling Thai Restaurant. Unfortunately, we missed your call.  
        If you're trying to place an order, please reply with your **full name**, **your order**,  
        and what **time you'd like to pick up** the food. If not, feel free to call us back!
        """
    else:
        # Add readable hours display
        today = datetime.now().strftime("%A")
        open_time, close_time = BUSINESS_HOURS[today]
        auto_reply = f"""
        > **Outgoing Auto-Reply:**  
        Hi, thank you for calling Thai Restaurant. We're currently **closed**.  
        Our hours today are **{open_time} to {close_time}**.  
        Please give us a call when we are open tomorrow!
        """

    st.markdown(auto_reply)

# User SMS simulation
user_sms = st.text_input("👤 Customer SMS:", placeholder="e.g., 1 Thai iced tea with tapioca pearls, 75% sweetness")

if user_sms:
    if is_store_open():
        if "order_finalized" not in st.session_state:
            st.session_state.order_finalized = False

        # Get last AI message (to detect if it's confirmation-ready)
        last_ai_message = [
            m.content for m in st.session_state.memory.chat_memory.messages
            if isinstance(m, AIMessage)
        ][-1] if any(isinstance(m, AIMessage) for m in st.session_state.memory.chat_memory.messages) else ""

        # Is LLM awaiting confirmation based on final order block?
        waiting_for_confirmation = (
            re.search(r"---\s*Full Name:.*?Ordered Items:.*?Pickup Time:.*?---", last_ai_message, re.DOTALL) is not None
        )

        # Check if user confirms AND we're in confirmation-ready state
        if is_confirmation(user_sms) and not st.session_state.order_finalized and waiting_for_confirmation:
            st.session_state.order_finalized = True

            name, items, pickup_time = extract_order_details(last_ai_message)
            if all([name, items, pickup_time]):
                st.write("Saving to Excel:", name, items, pickup_time)
                append_order_to_excel(name, items, pickup_time)
                reply = f"✅ Your order has been saved, {name}! Looking forward to seeing you at {pickup_time}."
            else:
                reply = "⚠️ I couldn't parse your order details. Please confirm again after repeating your order."

        elif st.session_state.order_finalized:
            reply = "🛑 Your order has already been finalized. Please call the restaurant to make any changes."

        else:
            reply = conversation.run(user_sms)

        st.success("🤖 Agent Reply:")
        st.markdown(f"> {reply}")

    else:
        today = datetime.now().strftime("%A")
        open_time, close_time = BUSINESS_HOURS[today]
        st.warning(f"""
        🤖 We're currently **closed** (hours today: **{open_time}–{close_time}**).  
        Please try again when we’re open — your message was not processed.
        """)


    # Show chat history in text-chain style
with st.expander("📱 Chat History (SMS-style)"):
    chat_html = ""
    for msg in st.session_state.memory.chat_memory.messages:
        if isinstance(msg, HumanMessage):
            chat_html += f"""
            <div style="text-align: right; background-color: #00008B; padding: 8px 12px; border-radius: 12px; margin: 4px; max-width: 70%; display: inline-block;">
                <b>🧑 Customer:</b><br>{msg.content}
            </div>
            """
        elif isinstance(msg, AIMessage):
            chat_html += f"""
            <div style="text-align: left; background-color: #A9A9A9; padding: 8px 12px; border-radius: 12px; margin: 4px; margin-left: 30%; max-width: 70%; display: inline-block;">
                <b>🤖 AI:</b><br>{msg.content}
            </div>
            """

    st.markdown(f"""
    <div style="max-height: 300px; overflow-y: auto;">{chat_html}</div>
    """, unsafe_allow_html=True)
import io

with st.expander("📋 View Saved Orders"):
    if os.path.exists(ORDERS_FILE):
        df = pd.read_excel(ORDERS_FILE, engine="openpyxl")  # ✅ required if writing with openpyxl

        st.dataframe(df)

        # Write Excel file to a buffer
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)

        st.download_button(
            "⬇️ Download Excel File",
            data=excel_buffer,
            file_name="orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No orders have been placed yet.")
