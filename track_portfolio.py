import os
import json
import requests
from chart_maker import create_visuals
from email_sender import dispatch_email

# We use the exact fund names here so Kuvera's search API can find them dynamically
FUNDS = {
    "Motilal Oswal Active Momentum": "Motilal Oswal Active Momentum Fund Direct Growth",
    "SBI Focused Equity": "SBI Focused Equity Fund Direct Growth",
    "Quant Momentum": "Quant Momentum Fund Direct Growth",
    "Kotak Active Momentum": "Kotak Active Momentum Fund Direct Growth",
    "UTI Nifty200 Momentum 30": "UTI Nifty200 Momentum 30 Index Fund Direct Growth"
}

DATA_FILE = "last_known_portfolio.json"

def fetch_fund_holdings(fund_search_query):
    # Standard header — Kuvera doesn't require complex browser masking
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        # STEP 1: Search Kuvera for the exact internal fund code
        search_url = f"https://api.kuvera.in/api/v3/search.json?v=1&q={fund_search_query}"
        search_response = requests.get(search_url, headers=headers, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if not search_data:
            print(f"Could not find Kuvera code for: {fund_search_query}")
            return None
            
        # Extract the code from the top search result (e.g., 'SBIFG3-GR')
        fund_code = search_data[0].get("code")
        
        # STEP 2: Fetch the actual portfolio using that specific code
        fund_url = f"https://api.kuvera.in/api/v3/funds/{fund_code}.json"
        fund_response = requests.get(fund_url, headers=headers, timeout=10)
        fund_response.raise_for_status()
        fund_data = fund_response.json()
        
        # Kuvera stores the holdings inside a 'portfolio' array
        holdings_list = fund_data[0].get("portfolio", [])
        
        simplified = {}
        for item in holdings_list:
            # Checking multiple keys just to be safe with Kuvera's schema
            company = item.get("stock_name", item.get("company", item.get("name", ""))).strip()
            percentage = item.get("weight", item.get("percentage", 0.0))
            if company:
                simplified[company] = float(percentage)
                
        return simplified
        
    except Exception as e:
        print(f"Error fetching {fund_search_query}: {e}")
        return None

def run_check():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            previous_data = json.load(f)
    else:
        previous_data = {}

    current_data = {}
    status_summary = ""
    activity_log = {}
    changes_detected = False
    
    for fund_name, search_query in FUNDS.items():
        holdings = fetch_fund_holdings(search_query)
        if not holdings:
            status_summary += f"• {fund_name}: Fetch failed. Using cached data.\n"
            current_data[fund_name] = previous_data.get(fund_name, {})
            continue
            
        current_data[fund_name] = holdings
        prev_holdings = previous_data.get(fund_name, {})
        
        fund_activity = {}
        for stock, pct in holdings.items():
            if stock not in prev_holdings:
                fund_activity[stock] = f"🟢 Added ({pct}%)"
            elif pct > prev_holdings.get(stock, 0) + 0.05: 
                fund_activity[stock] = f"🔺 Increased ({prev_holdings.get(stock, 0)}% ➔ {pct}%)"
                
        for stock, pct in prev_holdings.items():
            if stock not in holdings:
                fund_activity[stock] = "🔴 Exited"
            elif holdings[stock] < pct - 0.05:
                fund_activity[stock] = f"🔻 Decreased ({pct}% ➔ {holdings[stock]}%)"
        
        if fund_activity:
            changes_detected = True
            activity_log[fund_name] = fund_activity
            status_summary += f"• {fund_name}: Changes detected!\n"
        else:
            status_summary += f"• {fund_name}: No changes.\n"

    activity_html = ""
    if changes_detected:
        activity_html += '<div style="margin-top:20px; padding:15px; border:1px solid #ffcc00; background:#fffdf0; border-radius:4px;">'
        activity_html += '<h3 style="color:#d35400; margin-top:0;">🚨 Shifts Logged</h3>'
        for fund_name, actions in activity_log.items():
            activity_html += f"<strong>{fund_name}:</strong><ul>"
            for stock, act in actions.items():
                activity_html += f"<li>{stock}: {act}</li>"
            activity_html += "</ul>"
        activity_html += '</div>'

    # if changes_detected:
    #     print("Changes detected! Generating visuals and sending email.")
    #     create_visuals(current_data, changes_detected, activity_log)
    #     dispatch_email(status_summary, activity_html)

    create_visuals(current_data, changes_detected, activity_log)

    print("\n--- TEST SUMMARY ---")
    print(status_summary)

    with open(DATA_FILE, 'w') as f:
        json.dump(current_data, f, indent=4)

if __name__ == "__main__":
    run_check()

def run_check():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            previous_data = json.load(f)
    else:
        previous_data = {}

    current_data = {}
    status_summary = ""
    activity_log = {}
    changes_detected = False
    
    for fund_name, fund_slug in FUNDS.items():
        holdings = fetch_fund_holdings(fund_slug)
        if holdings is None:
            status_summary += f"• {fund_name}: Fetch failed. Using cached data.\n"
            current_data[fund_name] = previous_data.get(fund_name, {})
            continue
            
        current_data[fund_name] = holdings
        prev_holdings = previous_data.get(fund_name, {})
        
        fund_activity = {}
        for stock, pct in holdings.items():
            if stock not in prev_holdings:
                fund_activity[stock] = f"🟢 Added ({pct}%)"
            elif pct > prev_holdings.get(stock, 0) + 0.05: 
                fund_activity[stock] = f"🔺 Increased ({prev_holdings.get(stock, 0)}% ➔ {pct}%)"
                
        for stock, pct in prev_holdings.items():
            if stock not in holdings:
                fund_activity[stock] = "🔴 Exited"
            elif holdings[stock] < pct - 0.05:
                fund_activity[stock] = f"🔻 Decreased ({pct}% ➔ {holdings[stock]}%)"
        
        if fund_activity:
            changes_detected = True
            activity_log[fund_name] = fund_activity
            status_summary += f"• {fund_name}: Changes detected!\n"
        else:
            status_summary += f"• {fund_name}: No changes.\n"

    activity_html = ""
    if changes_detected:
        activity_html += '<div style="margin-top:20px; padding:15px; border:1px solid #ffcc00; background:#fffdf0; border-radius:4px;">'
        activity_html += '<h3 style="color:#d35400; margin-top:0;">🚨 Shifts Logged</h3>'
        for fund_name, actions in activity_log.items():
            activity_html += f"<strong>{fund_name}:</strong><ul>"
            for stock, act in actions.items():
                activity_html += f"<li>{stock}: {act}</li>"
            activity_html += "</ul>"
        activity_html += '</div>'

    create_visuals(current_data, changes_detected, activity_log)
    # dispatch_email(status_summary, activity_html)

    print("\n--- TEST SUMMARY ---")
    print(status_summary)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(current_data, f, indent=4)

if __name__ == "__main__":
    run_check()