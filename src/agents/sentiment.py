import json
import pandas as pd
import numpy as np
from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    insider_trades = data["insider_trades"]
    
    # Initialize sentiment metrics
    sentiment_metrics = {}
    
    # 1. Insider Trading Analysis
    if insider_trades:
        # Convert transaction values to numeric
        transaction_shares = pd.Series([t['shares'] for t in insider_trades]).dropna()
        transaction_values = pd.Series([t['value'] for t in insider_trades]).dropna()
        
        # Calculate metrics
        sentiment_metrics["insider_metrics"] = {
            "total_transactions": len(insider_trades),
            "avg_transaction_size": float(transaction_shares.mean()) if not transaction_shares.empty else 0,
            "total_value": float(transaction_values.sum()) if not transaction_values.empty else 0,
            "buy_ratio": len([t for t in insider_trades if t["transaction_type"] == "buy"]) / len(insider_trades) if insider_trades else 0
        }
        
        # Determine insider sentiment signal
        buy_ratio = sentiment_metrics["insider_metrics"]["buy_ratio"]
        avg_size = sentiment_metrics["insider_metrics"]["avg_transaction_size"]
        total_value = sentiment_metrics["insider_metrics"]["total_value"]
        
        if buy_ratio > 0.7 and total_value > 1000000:  # Strong buying
            insider_signal = "bullish"
            insider_confidence = min(1.0, buy_ratio)
        elif buy_ratio < 0.3 and total_value > 1000000:  # Strong selling
            insider_signal = "bearish"
            insider_confidence = min(1.0, 1 - buy_ratio)
        else:
            insider_signal = "neutral"
            insider_confidence = 0.5
    else:
        # No insider trading data
        sentiment_metrics["insider_metrics"] = {
            "total_transactions": 0,
            "avg_transaction_size": 0,
            "total_value": 0,
            "buy_ratio": 0
        }
        insider_signal = "neutral"
        insider_confidence = 0.5
    
    # Format the final output
    final_signal = insider_signal  # For now, just use insider signal
    final_confidence = insider_confidence
    
    if show_reasoning:
        print("\n==========    Sentiment Agent     ==========")
        print(json.dumps({
            "signal": final_signal,
            "confidence": f"{final_confidence*100:.0f}%",
            "metrics": sentiment_metrics
        }, indent=2))
        print("================================================\n")
    
    return {
        "messages": state["messages"],
        "data": {
            **data,
            "sentiment_signal": final_signal,
            "sentiment_confidence": final_confidence
        }
    }
