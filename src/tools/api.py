import os
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def get_financial_metrics(
    ticker: str,
    report_period: str,
    period: str = 'ttm',
    limit: int = 1
) -> List[Dict[str, Any]]:
    """Fetch financial metrics using yfinance."""
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Get financial statements for additional calculations
    financials = stock.financials
    cash_flow = stock.cashflow
    shares_outstanding = info.get("sharesOutstanding", 0)
    
    # Calculate per share metrics
    if shares_outstanding > 0:
        try:
            net_income = float(financials.iloc[0].get("Net Income", 0))
            free_cash_flow = float(cash_flow.iloc[0].get("Free Cash Flow", 0))
            earnings_per_share = net_income / shares_outstanding
            free_cash_flow_per_share = free_cash_flow / shares_outstanding
        except (IndexError, TypeError):
            earnings_per_share = info.get("trailingEps", 0)
            free_cash_flow_per_share = 0
    else:
        earnings_per_share = info.get("trailingEps", 0)
        free_cash_flow_per_share = 0
    
    # Calculate metrics that match the original API's format
    metrics = {
        "return_on_equity": info.get("returnOnEquity", 0),
        "net_margin": info.get("profitMargins", 0),
        "operating_margin": info.get("operatingMargins", 0),
        "revenue_growth": info.get("revenueGrowth", 0),
        "earnings_growth": info.get("earningsGrowth", 0),
        "book_value_growth": info.get("bookValue", 0) / info.get("priceToBook", 1) if info.get("priceToBook", 0) > 0 else 0,
        "debt_to_equity": info.get("debtToEquity", 0),
        "current_ratio": info.get("currentRatio", 0),
        "quick_ratio": info.get("quickRatio", 0),
        "price_to_earnings": info.get("trailingPE", 0),
        "price_to_book": info.get("priceToBook", 0),
        "price_to_sales": info.get("priceToSalesTrailing12Months", 0),
        "dividend_yield": info.get("dividendYield", 0) if info.get("dividendYield") else 0,
        "payout_ratio": info.get("payoutRatio", 0) if info.get("payoutRatio") else 0,
        "beta": info.get("beta", 0),
        "market_cap": info.get("marketCap", 0),
        "earnings_per_share": earnings_per_share,
        "free_cash_flow_per_share": free_cash_flow_per_share,
        "shares_outstanding": shares_outstanding
    }
    
    return [metrics]  # Return as list to match original format

def search_line_items(
    ticker: str,
    line_items: List[str],
    period: str = 'ttm',
    limit: int = 1
) -> List[Dict[str, Any]]:
    """Fetch financial statements using yfinance."""
    stock = yf.Ticker(ticker)
    
    # Get financials
    financials = stock.financials
    cash_flow = stock.cashflow
    balance_sheet = stock.balance_sheet
    
    results = []
    # Get data for the last 'limit' periods
    for i in range(min(limit, len(financials.index))):
        result = {}
        if "free_cash_flow" in line_items and i < len(cash_flow.index):
            result["free_cash_flow"] = float(cash_flow.iloc[i].get("Free Cash Flow", 0))
        if "net_income" in line_items and i < len(financials.index):
            result["net_income"] = float(financials.iloc[i].get("Net Income", 0))
        if "depreciation_and_amortization" in line_items and i < len(cash_flow.index):
            result["depreciation_and_amortization"] = float(cash_flow.iloc[i].get("Depreciation", 0))
        if "capital_expenditure" in line_items and i < len(cash_flow.index):
            result["capital_expenditure"] = float(cash_flow.iloc[i].get("Capital Expenditure", 0))
        if "working_capital" in line_items and i < len(balance_sheet.index):
            current_assets = float(balance_sheet.iloc[i].get("Total Current Assets", 0))
            current_liabilities = float(balance_sheet.iloc[i].get("Total Current Liabilities", 0))
            result["working_capital"] = current_assets - current_liabilities
        
        results.append(result)
    
    # If we don't have enough historical data, pad with copies of the last result
    while len(results) < limit:
        results.append(results[-1] if results else {})
    
    return results

def get_insider_trades(
    ticker: str,
    end_date: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch insider trades using yfinance."""
    stock = yf.Ticker(ticker)
    insider_trades = stock.insider_purchases
    
    if insider_trades is None or insider_trades.empty:
        return []
    
    # Convert to list of dicts and format to match original API
    trades = []
    for _, trade in insider_trades.head(limit).iterrows():
        # Handle date which might be string or datetime
        trade_date = trade.get("Date", "")
        if hasattr(trade_date, "strftime"):
            date_str = trade_date.strftime("%Y-%m-%d")
        else:
            # If it's already a string, use it as is
            date_str = str(trade_date)
            
        trades.append({
            "date": date_str,
            "insider_name": trade.get("Insider", ""),
            "shares": float(trade.get("Shares", 0)),
            "value": float(trade.get("Value", 0)),
            "transaction_type": "buy"  # All insider purchases are buys
        })
    
    return trades

def get_market_cap(ticker: str) -> float:
    """Fetch market cap using yfinance."""
    stock = yf.Ticker(ticker)
    return stock.info.get("marketCap", 0)

def get_prices(
    ticker: str,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Fetch price data using yfinance."""
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date, interval="1d")
    
    # Convert to list of dicts and format to match original API
    prices = []
    for date, row in df.iterrows():
        prices.append({
            "time": date.strftime("%Y-%m-%d"),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"])
        })
    
    return prices

def prices_to_df(prices: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame(prices)
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df

def get_price_data(
    ticker: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """Helper function to get price data as DataFrame directly."""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)
