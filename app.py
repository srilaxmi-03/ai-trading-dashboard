from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)

portfolio = []

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100/(1+rs))


@app.route("/", methods=["GET","POST"])
def home():

    stock = "AAPL"

    if request.method == "POST":
        stock = request.form["stock"].upper()

    try:

        df = yf.download(stock, period="6mo", interval="1d", progress=False)

        if df.empty:
            return render_template("index.html", error="Stock not found")

        df["Return"] = df["Close"].pct_change()
        df["Target"] = (df["Return"] > 0).astype(int)
        df["RSI"] = calculate_rsi(df["Close"])

        df = df.dropna()

        X = df[["Open","High","Low","Close"]]
        y = df["Target"]

        model = RandomForestClassifier()
        model.fit(X,y)

        prediction = model.predict(X.iloc[-1:])
        signal = "BUY 📈" if prediction[0] == 1 else "SELL 📉"

        price = round(df["Close"].iloc[-1].item(),2)
        rsi = round(df["RSI"].iloc[-1].item(),2)

        closes = df["Close"].tail(30).values.flatten().tolist()
        dates = df.index[-30:].strftime("%Y-%m-%d").tolist()

        trending_symbols = ["AAPL","TSLA","NVDA","MSFT","GOOGL"]
        trending = []

        for s in trending_symbols:
            d = yf.download(s, period="1d", progress=False)
            if not d.empty:
                p = round(d["Close"].iloc[-1].item(),2)
                trending.append({"symbol":s,"price":p})

        crypto_symbols = ["BTC-USD","ETH-USD","SOL-USD"]
        crypto = []

        for c in crypto_symbols:
            d = yf.download(c, period="1d", progress=False)
            if not d.empty:
                p = round(d["Close"].iloc[-1].item(),2)
                crypto.append({"symbol":c,"price":p})

        total_value = 0

        for item in portfolio:

            d = yf.download(item["symbol"], period="1d", progress=False)

            if not d.empty:
                current_price = d["Close"].iloc[-1].item()
                value = current_price * item["shares"]
                total_value += value

        return render_template(
            "index.html",
            stock=stock,
            price=price,
            signal=signal,
            rsi=rsi,
            closes=closes,
            dates=dates,
            trending=trending,
            crypto=crypto,
            portfolio=portfolio,
            total_value=round(total_value,2)
        )

    except Exception as e:
        return render_template("index.html", error=str(e))


@app.route("/add", methods=["POST"])
def add_stock():

    symbol = request.form["symbol"].upper()
    shares = int(request.form["shares"])

    portfolio.append({
        "symbol":symbol,
        "shares":shares
    })

    return home()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)