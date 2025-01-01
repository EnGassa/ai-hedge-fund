import json
from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

def risk_management_agent(state: AgentState):
    """Calculates risk metrics and sets position limits."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    
    # Get signals from other agents
    fundamentals_signal = data.get("fundamentals_signal", "neutral")
    fundamentals_confidence = data.get("fundamentals_confidence", 0.5)
    technical_signal = data.get("technical_signal", "neutral")
    technical_confidence = data.get("technical_confidence", 0.5)
    sentiment_signal = data.get("sentiment_signal", "neutral")
    sentiment_confidence = data.get("sentiment_confidence", 0.5)
    valuation_signal = data.get("valuation_signal", "neutral")
    valuation_confidence = data.get("valuation_confidence", 0.5)
    
    # Calculate risk metrics
    metrics = data["financial_metrics"][0]
    
    # 1. Market Risk
    beta = metrics["beta"]
    market_cap = metrics["market_cap"]
    
    # 2. Financial Risk
    debt_to_equity = metrics["debt_to_equity"]
    current_ratio = metrics["current_ratio"]
    
    # Calculate risk scores (0-1, higher is riskier)
    market_risk = min(1.0, max(0.0, beta / 2))  # Beta > 2 is very risky
    size_risk = 1.0 - min(1.0, market_cap / 1e12)  # Market cap < 1T is riskier
    leverage_risk = min(1.0, debt_to_equity / 2)  # D/E > 2 is very risky
    liquidity_risk = max(0.0, 1.0 - current_ratio / 2)  # Current ratio < 2 is risky
    
    # Combine risk scores
    total_risk_score = (
        market_risk * 0.3 +
        size_risk * 0.2 +
        leverage_risk * 0.3 +
        liquidity_risk * 0.2
    )
    
    # Determine position size based on risk score and signals
    base_position = 1.0 - total_risk_score  # Lower risk = larger position
    
    # Adjust based on signal agreement
    signals = [
        (fundamentals_signal, fundamentals_confidence),
        (technical_signal, technical_confidence),
        (sentiment_signal, sentiment_confidence),
        (valuation_signal, valuation_confidence)
    ]
    
    bullish_weight = sum(conf for sig, conf in signals if sig == "bullish")
    bearish_weight = sum(conf for sig, conf in signals if sig == "bearish")
    
    # Scale position size based on signal agreement
    if bullish_weight > bearish_weight:
        position_size = base_position * min(1.0, bullish_weight)
        signal = "bullish"
    elif bearish_weight > bullish_weight:
        position_size = base_position * min(1.0, bearish_weight)
        signal = "bearish"
    else:
        position_size = 0
        signal = "neutral"
    
    # Cap maximum position size
    position_size = min(0.8, position_size)  # Never use more than 80% of capital
    
    if show_reasoning:
        print("\n==========    Risk Manager    ==========")
        print(json.dumps({
            "signal": signal,
            "position_size": f"{position_size*100:.1f}%",
            "risk_metrics": {
                "total_risk_score": f"{total_risk_score*100:.1f}%",
                "market_risk": f"{market_risk*100:.1f}%",
                "size_risk": f"{size_risk*100:.1f}%",
                "leverage_risk": f"{leverage_risk*100:.1f}%",
                "liquidity_risk": f"{liquidity_risk*100:.1f}%"
            },
            "signal_agreement": {
                "bullish_weight": f"{bullish_weight*100:.1f}%",
                "bearish_weight": f"{bearish_weight*100:.1f}%"
            }
        }, indent=2))
        print("================================================\n")
    
    return {
        "messages": state["messages"],
        "data": {
            **data,
            "risk_signal": signal,
            "position_size": position_size
        }
    }

