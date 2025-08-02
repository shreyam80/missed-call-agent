# missed-call-agent
# AI Order Assistant — Missed Call SMS Ordering Demo

This project is a **smart SMS-based order-taking assistant** for small restaurants. It simulates what happens when a customer calls, the restaurant misses the call, and the AI follows up via text to take the order conversationally — without needing an app, website, or human in the loop.

---
## Why It Matters
Missed calls = missed revenue. This AI assistant shows how natural language and automation can help small restaurants capture more orders without requiring an app or hiring extra staff.
This project serves as a template adaptable to any small business use case (restaurant, private practice, salon, etc)

## Features

- **Missed Call Detection** (simulated via a button in this demo)
- **Conversational LLM Agent** powered by GPT-4o and LangChain
- **Memory-Enabled Flow** that tracks order progress across messages
- **Order Finalization Logic** that ensures accidental "yes" messages aren't treated as confirmation
- **Excel-based Order Storage** with downloadable `.xlsx` output
- **Store Hours Logic** — doesn't respond if the restaurant is closed
- **FAQ Support** — AI can answer common customer questions about the menu, hours, dietary needs, and more

---

## LLM Behavior Highlights

- Keeps track of missing information (name, order, pickup time)
- Politely prompts for anything missing
- Waits for **explicit confirmation** before finalizing an order
- Only finalizes orders when a structured block like this is present:

Full Name: [name]
Ordered Items: [items]
Pickup Time: [time]



- Prevents accidental order saves if the customer says "yes" too early

---

## Tech Stack

| Component         | Description                                 |
|------------------|---------------------------------------------|
|  GPT-4o via OpenAI API | LLM for conversational logic |
| LangChain        | Prompt templating + memory + chaining      |
|  Pandas + Excel  | Saving orders in `.xlsx` format             |
|  Streamlit       | UI for simulation (can be swapped with Twilio) |
|  Dotenv          | Securely loads OpenAI API key               |

---

## Try It Locally

1. **Clone the repo**
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
```
3. Add your OpenAI key to a .env file:
4. Run it!

## Next Steps (Coming Soon)
- Twilio Integration: Replace UI input with real incoming SMS
- Menu Parsing: Auto-detect real menu items, modifiers, and allergens
- Dynamic Hours & Menu: Load FAQ dynamically from a backend
- Edit & Cancel Orders: Add logic for users to change/cancel orders post-confirmation
- Automated Tests: Add unit tests for logic and parsing
