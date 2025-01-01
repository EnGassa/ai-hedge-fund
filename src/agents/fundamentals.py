from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

import json

##### Fundamental Agent #####
def fundamentals_agent(state: AgentState):
    """Analyzes fundamental data and generates trading signals."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    metrics = data["financial_metrics"][0]

    # Initialize signals list for different fundamental aspects
    signals = []
    reasoning = {}
    
    # 1. Profitability Analysis
    profitability_score = 0
    if metrics["return_on_equity"] > 0.15:  # Strong ROE above 15%
        profitability_score += 1
    if metrics["net_margin"] > 0.20:  # Healthy profit margins
        profitability_score += 1
    if metrics["operating_margin"] > 0.15:  # Strong operating efficiency
        profitability_score += 1
        
    signals.append('bullish' if profitability_score >= 2 else 'bearish' if profitability_score == 0 else 'neutral')
    reasoning["profitability_signal"] = {
        "signal": signals[0],
        "details": f"ROE: {metrics['return_on_equity']:.2%}, Net Margin: {metrics['net_margin']:.2%}, Op Margin: {metrics['operating_margin']:.2%}"
    }
    
    # 2. Growth Analysis
    growth_score = 0
    if metrics["revenue_growth"] > 0.10:  # 10% revenue growth
        growth_score += 1
    if metrics["earnings_growth"] > 0.10:  # 10% earnings growth
        growth_score += 1
    if metrics["book_value_growth"] > 0.10:  # 10% book value growth
        growth_score += 1
        
    signals.append('bullish' if growth_score >= 2 else 'bearish' if growth_score == 0 else 'neutral')
    reasoning["growth_signal"] = {
        "signal": signals[1],
        "details": f"Revenue Growth: {metrics['revenue_growth']:.2%}, Earnings Growth: {metrics['earnings_growth']:.2%}, Book Value Growth: {metrics['book_value_growth']:.2%}"
    }
    
    # 3. Financial Health Analysis
    health_score = 0
    if metrics["debt_to_equity"] < 1.0:  # Conservative debt level
        health_score += 1
    if metrics["current_ratio"] > 1.5:  # Strong liquidity
        health_score += 1
    if metrics["quick_ratio"] > 1.0:  # Strong quick ratio
        health_score += 1
        
    signals.append('bullish' if health_score >= 2 else 'bearish' if health_score == 0 else 'neutral')
    reasoning["health_signal"] = {
        "signal": signals[2],
        "details": f"D/E: {metrics['debt_to_equity']:.2f}, Current Ratio: {metrics['current_ratio']:.2f}, Quick Ratio: {metrics['quick_ratio']:.2f}"
    }
    
    # 4. Cash Flow Analysis
    cash_flow_score = 0
    if metrics["free_cash_flow_per_share"] > metrics["earnings_per_share"] * 0.8:  # Strong FCF conversion
        cash_flow_score += 1
    if metrics["free_cash_flow_per_share"] > 0:  # Positive FCF
        cash_flow_score += 1
        
    signals.append('bullish' if cash_flow_score == 2 else 'bearish' if cash_flow_score == 0 else 'neutral')
    reasoning["cash_flow_signal"] = {
        "signal": signals[3],
        "details": f"FCF/Share: ${metrics['free_cash_flow_per_share']:.2f}, EPS: ${metrics['earnings_per_share']:.2f}"
    }
    
    # 5. Valuation Analysis
    valuation_score = 0
    pe_ratio = metrics["price_to_earnings"]
    pb_ratio = metrics["price_to_book"]
    ps_ratio = metrics["price_to_sales"]
    
    # Industry-specific thresholds (simplified)
    if pe_ratio > 0 and pe_ratio < 30:  # Reasonable P/E
        valuation_score += 1
    if pb_ratio < 5:  # Reasonable P/B
        valuation_score += 1
    if ps_ratio < 10:  # Reasonable P/S
        valuation_score += 1
        
    signals.append('bullish' if valuation_score >= 2 else 'bearish' if valuation_score == 0 else 'neutral')
    reasoning["valuation_signal"] = {
        "signal": signals[4],
        "details": f"P/E: {pe_ratio:.2f}, P/B: {pb_ratio:.2f}, P/S: {ps_ratio:.2f}"
    }
    
    # Aggregate signals
    bullish_count = len([s for s in signals if s == 'bullish'])
    bearish_count = len([s for s in signals if s == 'bearish'])
    
    # Final signal
    if bullish_count > bearish_count and bullish_count >= 3:
        final_signal = 'bullish'
        confidence = min(1.0, (bullish_count - bearish_count) / len(signals))
    elif bearish_count > bullish_count and bearish_count >= 3:
        final_signal = 'bearish'
        confidence = min(1.0, (bearish_count - bullish_count) / len(signals))
    else:
        final_signal = 'neutral'
        confidence = 0.5
    
    if show_reasoning:
        print("\n==========    Fundamentals Agent    ==========")
        print(json.dumps({
            "signal": final_signal,
            "confidence": f"{confidence*100:.0f}%",
            "reasoning": reasoning
        }, indent=2))
        print("================================================\n")
    
    return {
        "messages": state["messages"],
        "data": {
            **data,
            "fundamentals_signal": final_signal,
            "fundamentals_confidence": confidence
        }
    }