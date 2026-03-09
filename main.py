"""
VNStock API Server - Render.com
"""
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
SOURCES = ['VCI', 'TCBS', 'MSN']

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

            # Debug: log tên cột thực tế (chỉ lần đầu)
            col_list = list(r.index)

            def get_val(keys):
                for col in r.index:
                    col_lower = str(col).lower().replace(' ', '').replace('_', '').replace('/','')
                    for k in keys:
                        k_norm = k.lower().replace(' ', '').replace('_', '').replace('/','')
                        if k_norm == col_lower or k_norm in col_lower:
                            v = r[col]
                            try:
                                f = float(v)
                                return None if str(v) in ('nan','None') else f
                            except:
                                return None
                return None

            pe   = get_val(['pe', 'p/e', 'priceearning', 'pricetoearning', 'earningratio'])
            pb   = get_val(['pb', 'p/b', 'pricebook', 'pricetobook', 'bookratio'])
            roe  = get_val(['roe', 'returnonequity', 'returnequity'])
            bvps = get_val(['bvps', 'bookvaluepershare', 'bookvalue', 'navpershare'])

            if roe is not None and roe < 1:
                roe = round(roe * 100, 2)
            elif roe is not None:
                roe = round(roe, 2)

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
                'error':  None,
                '_debug_cols': col_list  # tạm thời để debug
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
