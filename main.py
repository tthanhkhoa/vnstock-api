"""
VNStock API Server - Render.com v7
- Dynamic period: ?period=year|quarter&n=1|2|3...
- Default: year, n=1 (năm gần nhất)
"""
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
SOURCES = ['VCI', 'TCBS', 'MSN']

def get_val(row, targets):
    for col in row.index:
        col_str = col[1] if isinstance(col, tuple) else str(col)
        col_norm = col_str.lower().replace(' ','').replace('_','').replace('/','').replace('(','').replace(')','')
        for t in targets:
            t_norm = t.lower().replace(' ','').replace('_','').replace('/','').replace('(','').replace(')','')
            if t_norm == col_norm or col_norm.startswith(t_norm):
                v = row[col]
                try:
                    f = float(v)
                    return None if str(v) in ('nan','None','') else f
                except:
                    return None
    return None

def get_period_label(row):
    year, length = None, None
    for col in row.index:
        col_str = col[1] if isinstance(col, tuple) else str(col)
        if 'yearreport' in col_str.lower().replace(' ',''):
            try: year = int(float(row[col]))
            except: pass
        if 'lengthreport' in col_str.lower().replace(' ',''):
            try: length = int(float(row[col]))
            except: pass
    if year and length:
        return f"Q{length}/{year}" if length < 12 else f"Năm {year}"
    return str(year) if year else None

def parse_row(r, src):
    pe   = get_val(r, ['P/E'])
    pb   = get_val(r, ['P/B'])
    roe  = get_val(r, ['ROE(%)','ROE%','ROE'])
    bvps = get_val(r, ['BVPS(VND)','BVPS'])

    if roe is not None:
        roe = round(roe * 100, 2) if roe < 1 else round(roe, 2)

    return {
        'source': src,
        'period': get_period_label(r),
        'pe':   round(pe,   2) if pe   is not None else None,
        'pb':   round(pb,   2) if pb   is not None else None,
        'roe':  roe,
        'bvps': round(bvps, 0) if bvps is not None else None,
    }

def fetch_one(ticker, period_type='year', n=1):
    try:
        from vnstock import Vnstock
    except Exception as e:
        return {'ticker': ticker, 'error': f'import error: {e}'}

    last_err = ''
    for src in SOURCES:
        try:
            stock = Vnstock().stock(symbol=ticker, source=src)

            ratio = stock.finance.ratio(period=period_type, lang='en', dropna=True)
            if ratio is None or ratio.empty:
                # fallback period
                alt = 'quarter' if period_type == 'year' else 'year'
                ratio = stock.finance.ratio(period=alt, lang='en', dropna=True)
            if ratio is None or ratio.empty:
                last_err = f'{src}: empty'; continue

            # Lấy n kỳ gần nhất
            rows = ratio.tail(n)

            # Giá thị trường (real-time)
            price = None
            try:
                pb_data = stock.trading.price_board(symbols_list=[ticker])
                for col in pb_data.columns:
                    col_str = col[1] if isinstance(col, tuple) else str(col)
                    if any(k in col_str.lower() for k in ['close','match','price','gia']):
                        price = float(pb_data.iloc[0][col])
                        break
            except:
                pass

            if n == 1:
                # Trả về object đơn
                result = parse_row(rows.iloc[-1], src)
                result['ticker'] = ticker
                result['price']  = round(price, 0) if price else None
                result['error']  = None
                return result
            else:
                # Trả về list các kỳ
                periods = [parse_row(rows.iloc[i], src) for i in range(len(rows))]
                return {
                    'ticker':  ticker,
                    'source':  src,
                    'price':   round(price, 0) if price else None,
                    'periods': periods,
                    'error':   None
                }

        except Exception as e:
            last_err = f'{src}: {e}'; continue

    return {'ticker': ticker, 'source': None, 'error': last_err}


def parse_params():
    """Đọc ?period=year|quarter&n=1 từ query string."""
    period_type = request.args.get('period', 'year').lower()
    if period_type not in ('year', 'quarter'):
        period_type = 'year'
    try:
        n = max(1, min(int(request.args.get('n', 1)), 10))
    except:
        n = 1
    return period_type, n


@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'endpoints': {
            '/health': 'kiểm tra server',
            '/stock?ticker=ACB': 'mặc định: năm gần nhất',
            '/stock?ticker=ACB&period=quarter&n=4': '4 quý gần nhất',
            '/stock?ticker=ACB&period=year&n=3': '3 năm gần nhất',
            '/stocks?tickers=ACB,FPT&period=year&n=1': 'nhiều mã',
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/stock')
def get_stock():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({'error': 'Missing ticker param'}), 400
    period_type, n = parse_params()
    return jsonify(fetch_one(ticker, period_type, n))

@app.route('/stocks')
def get_stocks():
    raw = request.args.get('tickers', '')
    tickers = [t.strip().upper() for t in raw.split(',') if t.strip()]
    if not tickers:
        return jsonify({'error': 'Missing tickers param'}), 400
    period_type, n = parse_params()
    return jsonify({
        'data':  [fetch_one(t, period_type, n) for t in tickers],
        'count': len(tickers),
        'period_type': period_type,
        'n': n
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
