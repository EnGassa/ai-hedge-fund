import json
from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

def portfolio_management_agent(state: AgentState):
    """Makes final trading decisions and generates orders."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    portfolio = data["portfolio"]
    
    # Get signals and metrics from other agents
    fundamentals_signal = data.get("fundamentals_signal", "neutral")
    fundamentals_confidence = data.get("fundamentals_confidence", 0.5)
    technical_signal = data.get("technical_signal", "neutral")
    technical_confidence = data.get("technical_confidence", 0.5)
    sentiment_signal = data.get("sentiment_signal", "neutral")
    sentiment_confidence = data.get("sentiment_confidence", 0.5)
    valuation_signal = data.get("valuation_signal", "neutral")
    valuation_confidence = data.get("valuation_confidence", 0.5)
    risk_signal = data.get("risk_signal", "neutral")
    position_size = data.get("position_size", 0)
    
    # Get current price
    current_price = data["prices"][-1]["close"]
    
    # Calculate target position value
    total_portfolio_value = portfolio["cash"] + (portfolio["stock"] * current_price)
    target_position_value = total_portfolio_value * position_size
    
    # Calculate target shares
    target_shares = int(target_position_value / current_price) if current_price > 0 else 0
    current_shares = portfolio["stock"]
    
    # Determine action and quantity
    if target_shares > current_shares:
        action = "buy"
        quantity = target_shares - current_shares
    elif target_shares < current_shares:
        action = "sell"
        quantity = current_shares - target_shares
    else:
        action = "hold"
        quantity = 0
    
    # Format the decision
    decision = {
        "action": action,
        "quantity": quantity,
        "reasoning": {
            "signals": {
                "fundamentals": {"signal": fundamentals_signal, "confidence": f"{fundamentals_confidence*100:.0f}%"},
                "technical": {"signal": technical_signal, "confidence": f"{technical_confidence*100:.0f}%"},
                "sentiment": {"signal": sentiment_signal, "confidence": f"{sentiment_confidence*100:.0f}%"},
                "valuation": {"signal": valuation_signal, "confidence": f"{valuation_confidence*100:.0f}%"},
                "risk": {"signal": risk_signal, "position_size": f"{position_size*100:.1f}%"}
            },
            "portfolio": {
                "current_shares": current_shares,
                "target_shares": target_shares,
                "current_price": current_price,
                "total_value": total_portfolio_value
            }
        }
    }
    
    if show_reasoning:
        print("\n==========  Portfolio Manager  ==========")
        print(json.dumps(decision, indent=2))
        print("================================================\n")
    
    return {
        "messages": state["messages"],
        "data": {
            **data,
            "final_decision": decision
        }
    }