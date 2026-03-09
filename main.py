"""
VNStock API Server - Render.com v6
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
                    # Trả về None nếu là 0 hoặc nan — 0 thường là missing data
                    return None if (str(v) in ('nan','None','') or f == 0.0) else f
                except:
                    return None
    return None

def fetch_one(ticker):
    try:
        from vnstock import Vnstock
    except Exception as e:
        return {'ticker': ticker, 'source': None,
                'error': f'import error: {e}',
                'price': None, 'pe': None, 'pb': None, 'roe': None, 'bvps': None}

    last_err = ''
    for src in SOURCES:
        try:
            stock = Vnstock().stock(symbol=ticker, source=src)

            # Thử yearly nếu quarterly không có data
            ratio = None
            for period in ['quarter', 'year']:
                r = stock.finance.ratio(period=period, lang='en', dropna=True)
                if r is not None and not r.empty:
                    # Kiểm tra có data thực không (không phải toàn 0)
                    ratio = r
                    break

            if ratio is None or ratio.empty:
                last_err = f'{src}: empty ratio'; continue

            row = ratio.iloc[-1]

            pe   = get_val(row, ['P/E'])
            pb   = get_val(row, ['P/B'])
            roe  = get_val(row, ['ROE(%)','ROE%','ROE'])
            bvps = get_val(row, ['BVPS(VND)','BVPS'])

            # Nếu vẫn thiếu → thử lấy từ các dòng gần đây hơn
            if pe is None and pb is None:
                for i in range(2, min(6, len(ratio))):
                    row2 = ratio.iloc[-i]
                    pe2   = get_val(row2, ['P/E'])
                    pb2   = get_val(row2, ['P/B'])
                    roe2  = get_val(row2, ['ROE(%)','ROE%','ROE'])
                    bvps2 = get_val(row2, ['BVPS(VND)','BVPS'])
                    if pe2 or pb2:
                        pe, pb, roe, bvps = pe2, pb2, roe2, bvps2
                        break

            # Nếu source này không có đủ chỉ số → thử source kế tiếp
            if pe is None and pb is None and roe is None:
                last_err = f'{src}: all ratios null/zero'
                continue

            if roe is not None:
                roe = round(roe, 2)

            price = None
            try:
                pb_data = stock.trading.price_board(symbols_list=[ticker])
                for col in pb_data.columns:
                    col_str = col[1] if isinstance(col, tuple) else str(col)
                    if any(k in col_str.lower() for k in ['close','match','price','gia']):
                        v = float(pb_data.iloc[0][col])
                        if v > 0:
                            price = v
                            break
            except:
                pass

            return {
                'ticker': ticker, 'source': src,
                'price':  round(price, 0) if price  else None,
                'pe':     round(pe,    2) if pe      is not None else None,
                'pb':     round(pb,    2) if pb      is not None else None,
                'roe':    roe,
                'bvps':   round(bvps,  0) if bvps   is not None else None,
                'error':  None
            }
        except Exception as e:
            last_err = f'{src}: {e}'; continue

    return {'ticker': ticker, 'source': None, 'error': last_err,
            'price': None, 'pe': None, 'pb': None, 'roe': None, 'bvps': None}


@app.route('/')
def index():
    return jsonify({'status': 'ok',
                    'endpoints': ['/health', '/stock?ticker=ACB', '/stocks?tickers=ACB,FPT,HPG', '/debug?ticker=ACB']})

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

@app.route('/debug')
def debug():
    """Xem raw ratio data để kiểm tra tên cột và giá trị thực."""
    ticker = request.args.get('ticker', 'ACB').strip().upper()
    src    = request.args.get('source', 'VCI').strip().upper()
    period = request.args.get('period', 'quarter')
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=ticker, source=src)
        ratio = stock.finance.ratio(period=period, lang='en', dropna=True)
        if ratio is None or ratio.empty:
            return jsonify({'error': 'empty', 'ticker': ticker, 'source': src})

        # Trả về 3 dòng gần nhất + tên cột
        rows = ratio.tail(3).to_dict(orient='records')
        # Convert tuple keys thành string
        rows_clean = []
        for r in rows:
            rows_clean.append({str(k): v for k, v in r.items()})

        return jsonify({
            'ticker': ticker, 'source': src, 'period': period,
            'columns': [str(c) for c in ratio.columns.tolist()],
            'latest_3_rows': rows_clean
        })
    except Exception as e:
        return jsonify({'error': str(e), 'ticker': ticker, 'source': src})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
