import os
import json
import requests
import urllib.parse
from chart_maker import create_visuals
from email_sender import dispatch_email

FUNDS = {
    "Motilal Oswal Active Momentum": "motilal-oswal-active-momentum-fund-direct-growth",
    "SBI Focused Equity": "sbi-focused-equity-fund-direct-growth",
    "Quant Momentum": "quant-momentum-fund-direct-growth",
    "Kotak Active Momentum": "kotak-active-momentum-fund-direct-growth",
    "UTI Nifty200 Momentum 30": "uti-nifty200-momentum-30-index-fund-direct-growth"
}

DATA_FILE = "last_known_portfolio.json"

def fetch_fund_holdings(fund_slug):
    base_url = f"https://groww.in/v1/api/data/mf/web/v3/scheme/search/{fund_slug}"
    encoded_url = urllib.parse.quote(base_url, safe='')
    
    # We load up multiple proxy bypass routes
    proxies = [
        f"https://api.codetabs.com/v1/proxy?quest={encoded_url}",
        f"https://corsproxy.io/?{encoded_url}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    # The script will try each proxy one by one until one succeeds
    for proxy_url in proxies:
        try:
            response = requests.get(proxy_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                holdings_list = data.get("holdings", [])
                
                # If we successfully parsed the holdings, return them!
                if holdings_list:
                    return {item.get("company_name", "").strip(): float(item.get("corpus_per", 0.0)) for item in holdings_list if item.get("company_name", "").strip()}
            
        except Exception as e:
            # If this proxy fails, silently catch the error and try the next one in the list
            continue
            
    # If the loop finishes and all proxies failed
    print(f"Error: All proxies blocked/failed for {fund_slug}")
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