from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fuzzywuzzy import process  # For typo tolerance
import json
import os

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

service_account_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

client = gspread.authorize(creds)

# Load your actual sheet
sheet = client.open("menu").worksheet("pizza menu")
data = sheet.get_all_records()

# ✅ Root route to prevent 404 on Render
@app.route('/')
def home():
    return "✅ Pizza order checker is live and working! Use POST /check_order."

# 🍕 Order checking logic
@app.route('/check_order', methods=['POST'])
def check_order():
    order = request.json.get("order", "").lower()

    name = ""
    size = ""
    crust = ""
    item_type = ""

    words = order.split()

    for i in range(len(words)):
        if words[i].isnumeric():
            continue
        name = words[i]
        size = words[i+1] if i+1 < len(words) else ""
        crust = " ".join(words[i+2:-1]) if i+2 < len(words)-1 else ""
        item_type = words[-1]
        break

    all_names = list(set(row['Name'] for row in data))
    matched_name, score = process.extractOne(name, all_names)

    if score < 70:
        return f"Sorry! We do not have '{name.title()}' pizza in our menu. But instead we have '{matched_name}' pizza. Would you like to try that?"

    matched_items = [row for row in data if row['Name'].lower() == matched_name.lower()]
    matched_sizes = [row for row in matched_items if row['Size'].lower() == size.lower()]
    if not matched_sizes:
        available_sizes = list(set(row['Size'] for row in matched_items))
        return f"Sorry! '{matched_name}' is not available in '{size.title()}'. Available sizes are: {', '.join(available_sizes)}."

    matched_crusts = [row for row in matched_sizes if row['Crust'].lower() == crust.lower()]
    if not matched_crusts:
        available_crusts = list(set(row['Crust'] for row in matched_sizes))
        return f"Sorry! '{matched_name}' in '{size.title()}' is not available with '{crust.title()}'. Available crusts are: {', '.join(available_crusts)}."

    return f"Yes! '{matched_name}' is available in '{size.title()}' with '{crust.title()}' crust."

# 🔥 Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
