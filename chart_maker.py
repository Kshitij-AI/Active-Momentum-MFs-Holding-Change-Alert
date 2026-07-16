import matplotlib
matplotlib.use('Agg') # Required for cloud servers without monitors
import matplotlib.pyplot as plt

def create_visuals(current_data, changes_detected, activity_log):
    # ==========================================
    # CHART 1: Complete Holdings per Fund
    # ==========================================
    num_funds = len(current_data)
    
    # Calculate a dynamic height so the chart stretches cleanly based on stock count
    max_stocks = max([len(h) for h in current_data.values()] + [1])
    # Give each stock about 0.3 inches of vertical space
    fig_height = max(10, max_stocks * 0.3 * num_funds) 
    
    fig, axes = plt.subplots(num_funds, 1, figsize=(12, fig_height))
    fig.suptitle("Complete Portfolio Holdings Breakdown", fontsize=16, fontweight='bold', y=0.99)
    
    if num_funds == 1:
        axes = [axes]
        
    for idx, (fund_name, holdings) in enumerate(current_data.items()):
        # REMOVED [:5] - Now sorts and shows ALL stocks
        sorted_holdings = sorted(holdings.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_holdings:
            stocks = [x[0][:25] for x in sorted_holdings] # Truncate names slightly for fit
            percentages = [x[1] for x in sorted_holdings]
            
            axes[idx].barh(stocks, percentages, color='#3498db')
            axes[idx].set_title(fund_name, fontsize=13, fontweight='bold')
            axes[idx].invert_yaxis() # Largest holding at the top
            
            # Print the percentage next to each bar
            for i, v in enumerate(percentages):
                axes[idx].text(v + 0.1, i, f"{v}%", va='center', fontsize=8)
        else:
            axes[idx].text(0.5, 0.5, "No Data Available", ha='center', va='center')
    
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig("holdings_chart.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ==========================================
    # CHART 2: Smart Analytics (Shared Conviction)
    # ==========================================
    if changes_detected and activity_log:
        stock_counts = {}
        for fund, actions in activity_log.items():
            for stock, action in actions.items():
                stock_counts[stock] = stock_counts.get(stock, 0) + (1 if "Increased" in action or "Added" in action else -1)
        significant_changes = {k: v for k, v in stock_counts.items() if v != 0}
        
        if significant_changes:
            # Dynamic height for activity chart
            plt.figure(figsize=(10, max(6, len(significant_changes) * 0.3)))
            sorted_changes = sorted(significant_changes.items(), key=lambda x: x[1])
            stocks = [x[0][:25] for x in sorted_changes]
            scores = [x[1] for x in sorted_changes]
            bar_colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in scores]
            
            # Changed to horizontal bars to support many stocks cleanly
            plt.barh(stocks, scores, color=bar_colors)
            plt.title("Multi-Fund Network Activity (Net Buying vs Net Selling)", fontsize=14, fontweight='bold')
            plt.xlabel("Net Fund Action Score")
            plt.tight_layout()
        else:
            plt.figure(figsize=(10, 5))
            plt.text(0.5, 0.5, "Minor internal balancing observed.", ha='center', va='center', fontsize=12)
            plt.axis('off')
    else:
        all_stocks = {}
        for fund, holdings in current_data.items():
            for stock in holdings.keys():
                all_stocks[stock] = all_stocks.get(stock, 0) + 1
        shared_stocks = {k: v for k, v in all_stocks.items() if v > 1}
        
        if shared_stocks:
            # REMOVED [:10] - Shows ALL shared stocks now
            sorted_shared = sorted(shared_stocks.items(), key=lambda x: x[1], reverse=True)
            
            # Dynamic height based on amount of overlapping stocks
            plt.figure(figsize=(10, max(6, len(sorted_shared) * 0.3)))
            
            stocks = [x[0][:25] for x in sorted_shared]
            counts = [x[1] for x in sorted_shared]
            
            # Changed to horizontal bars
            plt.barh(stocks, counts, color='#9b59b6')
            plt.title("High Conviction Overlap (Owned by 2+ funds)", fontsize=14, fontweight='bold')
            plt.xlabel("Number of Funds Owning It")
            plt.xticks(range(2, max(counts) + 2))
            plt.gca().invert_yaxis() # Most shared at the top
            plt.tight_layout()
        else:
            plt.figure(figsize=(10, 5))
            plt.text(0.5, 0.5, "No overlapping stock ownership.", ha='center', va='center', fontsize=12)
            plt.axis('off')
            
    plt.savefig("analytics_chart.png", dpi=150, bbox_inches='tight')
    plt.close()