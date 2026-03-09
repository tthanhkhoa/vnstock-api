"""
VNStock API Server - Render.com
"""
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
SOURCES = ['TCBS', 'MSN', 'VCI']

def find_val(row, keywords):
    for col in row.index:
        if any(k.lower() in str(col).lower() for k in keywords):
            v = row[col]
            try:
                f = float(v)
                return None if str(v) == 'nan' else f
            except:
                return None
    return None

def fetch_one(ticker):
    try:
        from vnstock import Vnstock
    except Exception as e:
        return {'ticker': ticker, 'source': None,
                'error': f'import error: {e}',
                'price': None, 'pe': None, 'pb': None,
                'roe': None, 'bvps': None}

    last_err = ''
    for src in SOURCES:
        try:
            stock = Vnstock().stock(symbol=ticker, source=src)
            ratio = stock.finance.ratio(period='quarter', lang='en', dropna=True)
            if ratio is None or ratio.empty:
                last_err = f'{src}: empty ratio'
                continue

            r = ratio.iloc[-1]
            pe   = find_val(r, ['p/e','pe','pricetoearning','price_earning'])
            pb   = find_val(r, ['p/b','pb','pricetobook','price_book'])
            roe  = find_val(r, ['roe','returnonequity'])
            bvps = find_val(r, ['bvps','bookvalue','book_value','nav'])

            if roe is not None:
                roe = round(roe * 100, 2) if roe < 1 else round(roe, 2)

            price = None
            try:
                pb_data = stock.trading.price_board(symbols_list=[ticker])
                for col in pb_data.columns:
                    if any(k in str(col).lower() for k in ['close','match','price','gia']):
                        price = float(pb_data.iloc[0][col])
                        break
            except:
                pass

            return {
                'ticker': ticker, 'source': src,
                'price':  round(price, 0) if price else None,
                'pe':     round(pe,    2) if pe   is not None else None,
                'pb':     round(pb,    2) if pb   is not None else None,
                'roe':    roe,
                'bvps':   round(bvps,  0) if bvps is not None else None,
                'error':  None
            }
        except Exception as e:
            last_err = f'{src}: {e}'
            continue

    return {'ticker': ticker, 'source': None, 'error': last_err,
            'price': None, 'pe': None, 'pb': None, 'roe': None, 'bvps': None}


@app.route('/')
def index():
    return jsonify({'status': 'ok',
                    'usage': '/stock?ticker=ACB  or  /stocks?tickers=ACB,FPT,HPG'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/stock')
def get_stock():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({'error': 'Missing ticker param'}), 400
    return jsonify(fetch_one(ticker))

@app.route('/stocks')
def get_stocks():
    raw = request.args.get('tickers', '')
    tickers = [t.strip().upper() for t in raw.split(',') if t.strip()]
    if not tickers:
        return jsonify({'error': 'Missing tickers param'}), 400
    return jsonify({'data': [fetch_one(t) for t in tickers], 'count': len(tickers)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
