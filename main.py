"""
VNStock API Server - Render.com v7
- Dynamic period: ?period=year|quarter&n=1..10
- /docs endpoint với API documentation UI
"""
import os
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
SOURCES = ['VCI', 'TCBS', 'MSN']

# ── Access control ────────────────────────────────────────
# Thêm key vào đây để cấp quyền truy cập
API_KEYS = {
    'owner': 'vns2025secret',   # ✏️ key của bạn — đổi tuỳ ý
}

# vnstock license key để tăng rate limit
VNSTOCK_KEY = 'vnstock_72b5a8cf6d7cabe1e3242de34028ed1c'

# ── HTML DOCS ─────────────────────────────────────────────
DOCS_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VNStock API Docs</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f0f4f8; color: #1a202c; }

  /* Sidebar */
  .sidebar { position: fixed; left: 0; top: 0; width: 240px; height: 100vh;
             background: #1565C0; overflow-y: auto; z-index: 100; }
  .sidebar-logo { padding: 24px 20px 16px;
                  font-size: 20px; font-weight: 700; color: #fff;
                  border-bottom: 1px solid rgba(255,255,255,0.15); }
  .sidebar-logo span { font-size: 12px; display: block; opacity: 0.7; margin-top: 4px; font-weight: 400; }
  .sidebar-nav { padding: 12px 0; }
  .sidebar-nav a { display: block; padding: 10px 20px; color: rgba(255,255,255,0.8);
                   text-decoration: none; font-size: 13px; transition: all 0.2s; }
  .sidebar-nav a:hover, .sidebar-nav a.active { background: rgba(255,255,255,0.15);
                                                 color: #fff; padding-left: 28px; }
  .sidebar-nav .section-title { padding: 16px 20px 6px; font-size: 10px; text-transform: uppercase;
                                  letter-spacing: 1px; color: rgba(255,255,255,0.45); }

  /* Main */
  .main { margin-left: 240px; min-height: 100vh; }

  /* Hero */
  .hero { background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%);
          color: white; padding: 48px 48px 40px; }
  .hero h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
  .hero p { opacity: 0.85; font-size: 16px; }
  .hero .base-url { display: inline-block; margin-top: 20px; background: rgba(255,255,255,0.15);
                    border: 1px solid rgba(255,255,255,0.3); border-radius: 8px;
                    padding: 10px 18px; font-family: monospace; font-size: 14px; }
  .hero .base-url span { opacity: 0.7; }

  /* Content */
  .content { padding: 40px 48px; max-width: 960px; }

  /* Cards */
  .card { background: white; border-radius: 12px; margin-bottom: 24px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); overflow: hidden; }
  .card-header { padding: 20px 24px; border-bottom: 1px solid #e2e8f0; }
  .card-header h2 { font-size: 18px; color: #1a202c; font-weight: 600; }
  .card-header p { font-size: 14px; color: #718096; margin-top: 4px; }
  .card-body { padding: 24px; }

  /* Endpoint block */
  .endpoint { border: 1px solid #e2e8f0; border-radius: 10px;
              margin-bottom: 20px; overflow: hidden; }
  .endpoint-header { display: flex; align-items: center; gap: 14px;
                     padding: 14px 20px; background: #f7fafc;
                     border-bottom: 1px solid #e2e8f0; cursor: pointer; }
  .endpoint-header:hover { background: #edf2f7; }
  .method { font-size: 12px; font-weight: 700; padding: 4px 10px;
            border-radius: 5px; min-width: 52px; text-align: center; }
  .get  { background: #C6F6D5; color: #22543D; }
  .path { font-family: monospace; font-size: 15px; font-weight: 600; color: #2D3748; flex: 1; }
  .desc { font-size: 13px; color: #718096; }
  .endpoint-body { padding: 20px 24px; background: white; }

  /* Params table */
  .params-title { font-size: 12px; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.8px; color: #718096; margin-bottom: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #1565C0; color: white; text-align: left;
       padding: 10px 14px; font-weight: 600; font-size: 12px; }
  td { padding: 10px 14px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: #f7fafc; }
  .param-name { font-family: monospace; color: #C0392B; font-weight: 600; }
  .param-type { background: #EBF8FF; color: #2B6CB0; border-radius: 4px;
                padding: 2px 7px; font-size: 11px; font-family: monospace; }
  .required { background: #FFF5F5; color: #C53030; border-radius: 4px;
              padding: 2px 7px; font-size: 11px; font-weight: 600; }
  .optional { background: #F0FFF4; color: #276749; border-radius: 4px;
              padding: 2px 7px; font-size: 11px; font-weight: 600; }

  /* Code block */
  .code-block { background: #1a202c; border-radius: 8px; padding: 16px 20px;
                margin: 12px 0; overflow-x: auto; }
  .code-block pre { font-family: monospace; font-size: 13px; color: #e2e8f0;
                    white-space: pre; line-height: 1.6; }
  .code-block .comment { color: #68D391; }
  .code-block .key     { color: #90CDF4; }
  .code-block .str     { color: #FBD38D; }
  .code-block .num     { color: #FC8181; }
  .code-label { font-size: 11px; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.8px; color: #718096; margin-bottom: 6px; margin-top: 16px; }

  /* Field table */
  .field-table th { background: #2D3748; }

  /* Info box */
  .info-box { background: #EBF8FF; border-left: 4px solid #3182CE; border-radius: 6px;
              padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #2C5282; }
  .warn-box { background: #FFFBEB; border-left: 4px solid #D69E2E; border-radius: 6px;
              padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #744210; }

  /* Metrics table */
  .metrics th { background: #2D3748; }

  section { scroll-margin-top: 20px; }
</style>
</head>
<body>

<!-- Sidebar -->
<div class="sidebar">
  <div class="sidebar-logo">
    📈 VNStock API
    <span>v7.0 · Render.com</span>
  </div>
  <nav class="sidebar-nav">
    <div class="section-title">Bắt đầu</div>
    <a href="#overview">Tổng quan</a>
    <a href="#metrics">Chỉ số hỗ trợ</a>
    <a href="#params">Tham số chung</a>

    <div class="section-title">Endpoints</div>
    <a href="#ep-health">GET /health</a>
    <a href="#ep-stock">GET /stock</a>
    <a href="#ep-stocks">GET /stocks</a>

    <div class="section-title">Tham khảo</div>
    <a href="#response">Cấu trúc Response</a>
    <a href="#errors">Xử lý lỗi</a>
    <a href="#examples">Ví dụ thực tế</a>
  </nav>
</div>

<!-- Main -->
<div class="main">

  <!-- Hero -->
  <div class="hero">
    <h1>📈 VNStock API</h1>
    <p>REST API miễn phí cung cấp dữ liệu tài chính cổ phiếu Việt Nam — P/E, P/B, ROE, BVPS, Giá thị trường</p>
    <div class="base-url">
      <span>Base URL: </span>https://vnstock-api-djlt.onrender.com
    </div>
  </div>

  <div class="content">

    <!-- Overview -->
    <section id="overview">
      <div class="card">
        <div class="card-header">
          <h2>Tổng quan</h2>
          <p>Thông tin cơ bản về API</p>
        </div>
        <div class="card-body">
          <table>
            <tr><td style="width:160px;font-weight:600;color:#4A5568">Nguồn dữ liệu</td>
                <td>VCI (ưu tiên) → TCBS → MSN (fallback tự động)</td></tr>
            <tr><td style="font-weight:600;color:#4A5568">Xác thực</td>
                <td>Không cần API key</td></tr>
            <tr><td style="font-weight:600;color:#4A5568">Định dạng</td>
                <td>JSON · UTF-8</td></tr>
            <tr><td style="font-weight:600;color:#4A5568">Phương thức</td>
                <td>GET</td></tr>
            <tr><td style="font-weight:600;color:#4A5568">Giá thị trường</td>
                <td>Real-time (delay ~15 phút)</td></tr>
            <tr><td style="font-weight:600;color:#4A5568">Chỉ số tài chính</td>
                <td>Theo năm (mặc định) hoặc theo quý</td></tr>
          </table>
        </div>
      </div>
    </section>

    <!-- Metrics -->
    <section id="metrics">
      <div class="card">
        <div class="card-header">
          <h2>Chỉ số hỗ trợ</h2>
          <p>Các field trả về trong response</p>
        </div>
        <div class="card-body">
          <table class="metrics">
            <tr>
              <th style="width:120px">Field</th>
              <th style="width:200px">Tên đầy đủ</th>
              <th style="width:80px">Đơn vị</th>
              <th>Ý nghĩa & Ngưỡng tham chiếu</th>
            </tr>
            <tr>
              <td class="param-name">price</td>
              <td>Giá thị trường</td><td>VNĐ</td>
              <td>Giá đóng cửa gần nhất. Real-time delay ~15 phút</td>
            </tr>
            <tr>
              <td class="param-name">pe</td>
              <td>Price / Earnings</td><td>lần (x)</td>
              <td>Giá / Lợi nhuận mỗi CP. <strong style="color:#22543D">< 10x = rẻ</strong> · <strong style="color:#744210">> 25x = đắt</strong></td>
            </tr>
            <tr>
              <td class="param-name">pb</td>
              <td>Price / Book Value</td><td>lần (x)</td>
              <td>Giá / Giá trị sổ sách. <strong style="color:#22543D">< 1x = dưới giá trị sổ sách</strong> · <strong style="color:#744210">> 3x = định giá cao</strong></td>
            </tr>
            <tr>
              <td class="param-name">roe</td>
              <td>Return on Equity</td><td>%</td>
              <td>Lợi nhuận / Vốn chủ sở hữu. <strong style="color:#22543D">> 15% = tốt</strong> · <strong style="color:#744210">< 8% = thấp</strong></td>
            </tr>
            <tr>
              <td class="param-name">bvps</td>
              <td>Book Value Per Share</td><td>VNĐ</td>
              <td>Giá trị sổ sách / cổ phiếu = NAV/share. So sánh với price để tính P/B</td>
            </tr>
            <tr>
              <td class="param-name">period</td>
              <td>Kỳ báo cáo</td><td>—</td>
              <td>Năm hoặc quý của số liệu tài chính. VD: <code>Năm 2024</code>, <code>Q4/2024</code></td>
            </tr>
          </table>
        </div>
      </div>
    </section>

    <!-- Common Params -->
    <section id="params">
      <div class="card">
        <div class="card-header">
          <h2>Tham số chung</h2>
          <p>Áp dụng cho /stock và /stocks</p>
        </div>
        <div class="card-body">
          <table>
            <tr>
              <th style="width:110px">Tham số</th>
              <th style="width:90px">Kiểu</th>
              <th style="width:100px">Mặc định</th>
              <th style="width:90px">Bắt buộc</th>
              <th>Mô tả</th>
            </tr>
            <tr>
              <td class="param-name">ticker</td>
              <td><span class="param-type">string</span></td>
              <td>—</td><td><span class="required">Có</span></td>
              <td>Mã cổ phiếu viết hoa. Dùng cho <code>/stock</code>. VD: <code>ACB</code>, <code>FPT</code></td>
            </tr>
            <tr>
              <td class="param-name">tickers</td>
              <td><span class="param-type">string</span></td>
              <td>—</td><td><span class="required">Có</span></td>
              <td>Danh sách mã cách nhau bởi dấu phẩy. Dùng cho <code>/stocks</code>. VD: <code>ACB,FPT,HPG</code></td>
            </tr>
            <tr>
              <td class="param-name">period</td>
              <td><span class="param-type">string</span></td>
              <td><code>year</code></td><td><span class="optional">Không</span></td>
              <td>Loại kỳ báo cáo: <code>year</code> (theo năm) hoặc <code>quarter</code> (theo quý). Khuyến nghị dùng <code>year</code> để ROE/BVPS chính xác hơn</td>
            </tr>
            <tr>
              <td class="param-name">n</td>
              <td><span class="param-type">integer</span></td>
              <td><code>1</code></td><td><span class="optional">Không</span></td>
              <td>Số kỳ muốn lấy, từ 1 đến 10. Khi <code>n=1</code> trả về object đơn. Khi <code>n>1</code> trả về mảng <code>periods[]</code></td>
            </tr>
          </table>
        </div>
      </div>
    </section>

    <!-- Endpoints -->
    <section id="ep-health">
      <div class="card">
        <div class="card-header"><h2>Endpoints</h2><p>Tất cả endpoint hiện có</p></div>
        <div class="card-body">

          <!-- /health -->
          <div class="endpoint">
            <div class="endpoint-header">
              <span class="method get">GET</span>
              <span class="path">/health</span>
              <span class="desc">Kiểm tra server đang hoạt động</span>
            </div>
            <div class="endpoint-body">
              <div class="info-box">Dùng để ping giữ server alive (UptimeRobot mỗi 10 phút). Không có tham số.</div>
              <div class="code-label">Request</div>
              <div class="code-block"><pre>GET https://vnstock-api-djlt.onrender.com/health</pre></div>
              <div class="code-label">Response</div>
              <div class="code-block"><pre>{ <span class="key">"status"</span>: <span class="str">"ok"</span> }</pre></div>
            </div>
          </div>

          <!-- /stock -->
          <div class="endpoint" id="ep-stock">
            <div class="endpoint-header">
              <span class="method get">GET</span>
              <span class="path">/stock</span>
              <span class="desc">Lấy dữ liệu tài chính cho 1 mã cổ phiếu</span>
            </div>
            <div class="endpoint-body">
              <div class="params-title">Tham số</div>
              <table>
                <tr><th>Tham số</th><th>Bắt buộc</th><th>Mô tả</th></tr>
                <tr><td class="param-name">ticker</td><td><span class="required">Có</span></td><td>Mã cổ phiếu. VD: <code>ACB</code></td></tr>
                <tr><td class="param-name">period</td><td><span class="optional">Không</span></td><td><code>year</code> (mặc định) hoặc <code>quarter</code></td></tr>
                <tr><td class="param-name">n</td><td><span class="optional">Không</span></td><td>Số kỳ, 1–10. Mặc định: <code>1</code></td></tr>
              </table>

              <div class="code-label">Ví dụ Request</div>
              <div class="code-block"><pre><span class="comment"># Năm gần nhất (mặc định)</span>
GET /stock?ticker=ACB

<span class="comment"># 3 năm gần nhất</span>
GET /stock?ticker=ACB&period=year&n=3

<span class="comment"># 4 quý gần nhất</span>
GET /stock?ticker=ACB&period=quarter&n=4</pre></div>

              <div class="code-label">Response — n=1 (object đơn)</div>
              <div class="code-block"><pre>{
  <span class="key">"ticker"</span>:  <span class="str">"ACB"</span>,
  <span class="key">"source"</span>:  <span class="str">"VCI"</span>,
  <span class="key">"period"</span>:  <span class="str">"Năm 2024"</span>,
  <span class="key">"price"</span>:   <span class="num">23300</span>,
  <span class="key">"pe"</span>:      <span class="num">7.82</span>,
  <span class="key">"pb"</span>:      <span class="num">1.13</span>,
  <span class="key">"roe"</span>:     <span class="num">19.5</span>,
  <span class="key">"bvps"</span>:    <span class="num">20614</span>,
  <span class="key">"error"</span>:   <span class="str">null</span>
}</pre></div>

              <div class="code-label">Response — n=3 (có mảng periods)</div>
              <div class="code-block"><pre>{
  <span class="key">"ticker"</span>:  <span class="str">"ACB"</span>,
  <span class="key">"source"</span>:  <span class="str">"VCI"</span>,
  <span class="key">"price"</span>:   <span class="num">23300</span>,
  <span class="key">"periods"</span>: [
    { <span class="key">"period"</span>: <span class="str">"Năm 2022"</span>, <span class="key">"pe"</span>: <span class="num">8.1</span>, <span class="key">"pb"</span>: <span class="num">1.5</span>, <span class="key">"roe"</span>: <span class="num">22.1</span>, <span class="key">"bvps"</span>: <span class="num">17200</span> },
    { <span class="key">"period"</span>: <span class="str">"Năm 2023"</span>, <span class="key">"pe"</span>: <span class="num">7.4</span>, <span class="key">"pb"</span>: <span class="num">1.3</span>, <span class="key">"roe"</span>: <span class="num">20.8</span>, <span class="key">"bvps"</span>: <span class="num">18900</span> },
    { <span class="key">"period"</span>: <span class="str">"Năm 2024"</span>, <span class="key">"pe"</span>: <span class="num">7.8</span>, <span class="key">"pb"</span>: <span class="num">1.1</span>, <span class="key">"roe"</span>: <span class="num">19.5</span>, <span class="key">"bvps"</span>: <span class="num">20614</span> }
  ],
  <span class="key">"error"</span>: <span class="str">null</span>
}</pre></div>
            </div>
          </div>

          <!-- /stocks -->
          <div class="endpoint" id="ep-stocks">
            <div class="endpoint-header">
              <span class="method get">GET</span>
              <span class="path">/stocks</span>
              <span class="desc">Lấy dữ liệu tài chính cho nhiều mã cùng lúc</span>
            </div>
            <div class="endpoint-body">
              <div class="params-title">Tham số</div>
              <table>
                <tr><th>Tham số</th><th>Bắt buộc</th><th>Mô tả</th></tr>
                <tr><td class="param-name">tickers</td><td><span class="required">Có</span></td><td>Danh sách mã cách nhau bởi dấu phẩy. VD: <code>ACB,FPT,HPG</code></td></tr>
                <tr><td class="param-name">period</td><td><span class="optional">Không</span></td><td><code>year</code> (mặc định) hoặc <code>quarter</code></td></tr>
                <tr><td class="param-name">n</td><td><span class="optional">Không</span></td><td>Số kỳ, 1–10. Mặc định: <code>1</code></td></tr>
              </table>

              <div class="code-label">Ví dụ Request</div>
              <div class="code-block"><pre><span class="comment"># Nhiều mã, năm gần nhất</span>
GET /stocks?tickers=ACB,FPT,HPG

<span class="comment"># Nhiều mã, 3 năm</span>
GET /stocks?tickers=ACB,FPT&period=year&n=3</pre></div>

              <div class="code-label">Response</div>
              <div class="code-block"><pre>{
  <span class="key">"count"</span>:       <span class="num">3</span>,
  <span class="key">"period_type"</span>: <span class="str">"year"</span>,
  <span class="key">"n"</span>:           <span class="num">1</span>,
  <span class="key">"data"</span>: [
    { <span class="key">"ticker"</span>: <span class="str">"ACB"</span>, <span class="key">"price"</span>: <span class="num">23300</span>, <span class="key">"pe"</span>: <span class="num">7.82</span>, <span class="key">"pb"</span>: <span class="num">1.13</span>, <span class="key">"roe"</span>: <span class="num">19.5</span>, <span class="key">"bvps"</span>: <span class="num">20614</span>, <span class="key">"error"</span>: <span class="str">null</span> },
    { <span class="key">"ticker"</span>: <span class="str">"FPT"</span>, <span class="key">"price"</span>: <span class="num">81600</span>, <span class="key">"pe"</span>: <span class="num">21.3</span>, <span class="key">"pb"</span>: <span class="num">5.2</span>,  <span class="key">"roe"</span>: <span class="num">28.1</span>, <span class="key">"bvps"</span>: <span class="num">15680</span>, <span class="key">"error"</span>: <span class="str">null</span> },
    { <span class="key">"ticker"</span>: <span class="str">"HPG"</span>, <span class="key">"price"</span>: <span class="num">27250</span>, <span class="key">"pe"</span>: <span class="num">9.85</span>, <span class="key">"pb"</span>: <span class="num">1.37</span>, <span class="key">"roe"</span>: <span class="num">14.9</span>, <span class="key">"bvps"</span>: <span class="num">21555</span>, <span class="key">"error"</span>: <span class="str">null</span> }
  ]
}</pre></div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Response Structure -->
    <section id="response">
      <div class="card">
        <div class="card-header"><h2>Cấu trúc Response</h2><p>Mô tả chi tiết các field trả về</p></div>
        <div class="card-body">
          <table class="field-table">
            <tr><th style="width:120px">Field</th><th style="width:100px">Kiểu</th><th>Mô tả</th></tr>
            <tr><td class="param-name">ticker</td><td><span class="param-type">string</span></td><td>Mã cổ phiếu</td></tr>
            <tr><td class="param-name">source</td><td><span class="param-type">string</span></td><td>Nguồn dữ liệu thực tế đã dùng: <code>VCI</code>, <code>TCBS</code>, hoặc <code>MSN</code></td></tr>
            <tr><td class="param-name">period</td><td><span class="param-type">string</span></td><td>Kỳ báo cáo. VD: <code>Năm 2024</code>, <code>Q4/2024</code>. Chỉ có khi <code>n=1</code></td></tr>
            <tr><td class="param-name">price</td><td><span class="param-type">number</span></td><td>Giá thị trường (VNĐ). Real-time, delay ~15 phút</td></tr>
            <tr><td class="param-name">pe</td><td><span class="param-type">number</span></td><td>Chỉ số P/E. <code>null</code> nếu không có dữ liệu</td></tr>
            <tr><td class="param-name">pb</td><td><span class="param-type">number</span></td><td>Chỉ số P/B. <code>null</code> nếu không có dữ liệu</td></tr>
            <tr><td class="param-name">roe</td><td><span class="param-type">number</span></td><td>ROE theo % (VD: <code>19.5</code> = 19.5%). <code>null</code> nếu không có</td></tr>
            <tr><td class="param-name">bvps</td><td><span class="param-type">number</span></td><td>Giá trị sổ sách mỗi cổ phiếu (VNĐ)</td></tr>
            <tr><td class="param-name">periods</td><td><span class="param-type">array</span></td><td>Mảng dữ liệu nhiều kỳ. Chỉ có khi <code>n > 1</code>. Mỗi phần tử có đủ các field trên</td></tr>
            <tr><td class="param-name">error</td><td><span class="param-type">string|null</span></td><td><code>null</code> nếu thành công. Chuỗi mô tả lỗi nếu thất bại</td></tr>
          </table>
        </div>
      </div>
    </section>

    <!-- Errors -->
    <section id="errors">
      <div class="card">
        <div class="card-header"><h2>Xử lý lỗi</h2><p>Các trường hợp lỗi thường gặp</p></div>
        <div class="card-body">
          <table>
            <tr><th style="width:180px">Trường hợp</th><th style="width:120px">HTTP Status</th><th>Ý nghĩa & Cách xử lý</th></tr>
            <tr>
              <td>Thiếu tham số</td><td>400</td>
              <td>Không truyền <code>ticker</code> hoặc <code>tickers</code></td>
            </tr>
            <tr>
              <td>Mã không tồn tại</td><td>200</td>
              <td>Response trả về 200 nhưng field <code>error</code> có nội dung. Kiểm tra <code>error != null</code></td>
            </tr>
            <tr>
              <td>Nguồn bị chặn</td><td>200</td>
              <td>Tự động thử source tiếp theo (VCI → TCBS → MSN). Nếu tất cả fail thì <code>error</code> chứa lý do</td>
            </tr>
            <tr>
              <td>Server cold start</td><td>200</td>
              <td>Render free tắt sau 15 phút không dùng. Request đầu tiên chờ ~30 giây. Dùng UptimeRobot để tránh</td>
            </tr>
          </table>
          <div class="warn-box">⚠️ Luôn kiểm tra field <code>error</code> trong response dù HTTP status là 200. Mã không hợp lệ vẫn trả về 200 với <code>error != null</code>.</div>
        </div>
      </div>
    </section>

    <!-- Examples -->
    <section id="examples">
      <div class="card">
        <div class="card-header"><h2>Ví dụ thực tế</h2><p>Dùng trong Google Apps Script</p></div>
        <div class="card-body">
          <div class="code-label">Apps Script — Cập nhật Google Sheet</div>
          <div class="code-block"><pre><span class="comment">// Lấy 1 mã, năm gần nhất</span>
<span class="key">const</span> url = <span class="str">"https://vnstock-api-djlt.onrender.com/stocks?tickers=ACB,FPT,HPG"</span>;
<span class="key">const</span> resp = UrlFetchApp.fetch(url);
<span class="key">const</span> data = JSON.parse(resp.getContentText()).data;

data.forEach((d, i) => {
  sheet.getRange(i + 2, 1).setValue(d.ticker);
  sheet.getRange(i + 2, 2).setValue(d.price ?? <span class="str">"N/A"</span>);
  sheet.getRange(i + 2, 3).setValue(d.pe    ?? <span class="str">"N/A"</span>);
  sheet.getRange(i + 2, 4).setValue(d.pb    ?? <span class="str">"N/A"</span>);
  sheet.getRange(i + 2, 5).setValue(d.roe   ?? <span class="str">"N/A"</span>);
  sheet.getRange(i + 2, 6).setValue(d.bvps  ?? <span class="str">"N/A"</span>);
});</pre></div>

          <div class="code-label">Lấy 3 năm lịch sử</div>
          <div class="code-block"><pre>GET /stock?ticker=FPT&period=year&n=3

<span class="comment">// Xử lý response nhiều kỳ</span>
<span class="key">const</span> result = JSON.parse(resp.getContentText());
result.periods.forEach(p => {
  console.log(p.period, <span class="str">"→ P/E:"</span>, p.pe, <span class="str">"ROE:"</span>, p.roe);
});</pre></div>
        </div>
      </div>
    </section>

    <div style="text-align:center;padding:32px 0 48px;color:#A0AEC0;font-size:13px">
      VNStock API · Dữ liệu từ vnstock / VCI · Deploy trên Render.com
    </div>

  </div>
</div>
</body>
</html>
"""

# ── API logic ─────────────────────────────────────────────
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

def sort_ratio(ratio):
    """Sort DataFrame cũ→mới an toàn với MultiIndex columns."""
    try:
        # Flatten columns để tìm yearReport
        flat_cols = [col[1] if isinstance(col, tuple) else str(col) for col in ratio.columns]
        year_idx  = next((i for i, c in enumerate(flat_cols)
                          if 'yearreport' in c.lower().replace(' ','')), None)
        if year_idx is not None:
            year_values = ratio.iloc[:, year_idx].astype(float)
            ratio = ratio.iloc[year_values.argsort().values]  # sort by position
        else:
            ratio = ratio.iloc[::-1]
    except:
        ratio = ratio.iloc[::-1]
    return ratio

def fetch_one(ticker, period_type='year', n=1):
    try:
        from vnstock import Vnstock
    except Exception as e:
        return {'ticker': ticker, 'error': f'import error: {e}'}

    last_err = ''
    for src in SOURCES:
        try:
            stock = Vnstock(license_key=VNSTOCK_KEY).stock(symbol=ticker, source=src)
            ratio = stock.finance.ratio(period=period_type, lang='en', dropna=True)
            if ratio is None or ratio.empty:
                alt   = 'quarter' if period_type == 'year' else 'year'
                ratio = stock.finance.ratio(period=alt, lang='en', dropna=True)
            if ratio is None or ratio.empty:
                last_err = f'{src}: empty'; continue

            ratio = sort_ratio(ratio)
            rows  = ratio.tail(n)  # n hàng cuối = n kỳ mới nhất

            price = None
            try:
                pb_data = stock.trading.price_board(symbols_list=[ticker])
                for col in pb_data.columns:
                    col_str = col[1] if isinstance(col, tuple) else str(col)
                    if any(k in col_str.lower() for k in ['close','match','price','gia']):
                        price = float(pb_data.iloc[0][col]); break
            except: pass

            if n == 1:
                result = parse_row(rows.iloc[-1], src)
                result.update({'ticker': ticker, 'price': round(price,0) if price else None, 'error': None})
                return result
            else:
                return {
                    'ticker':  ticker, 'source': src,
                    'price':   round(price,0) if price else None,
                    'periods': [parse_row(rows.iloc[i], src) for i in range(len(rows))],
                    'error':   None
                }
        except Exception as e:
            last_err = f'{src}: {e}'; continue

    return {'ticker': ticker, 'source': None, 'error': last_err}

def parse_params():
    period_type = request.args.get('period', 'year').lower()
    if period_type not in ('year', 'quarter'): period_type = 'year'
    try: n = max(1, min(int(request.args.get('n', 1)), 10))
    except: n = 1
    return period_type, n

def check_key():
    key = request.args.get('key', '').strip()
    if key not in API_KEYS.values():
        return jsonify({'error': 'Unauthorized', 'message': 'Thiếu hoặc sai key. Thêm ?key=YOUR_KEY vào URL.'}), 401
    return None

# ── Routes ────────────────────────────────────────────────
@app.route('/docs')
def docs():
    return render_template_string(DOCS_HTML)

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'docs': '/docs',
                    'endpoints': ['/health', '/stock?ticker=ACB', '/stocks?tickers=ACB,FPT,HPG']})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/stock')
def get_stock():
    err = check_key()
    if err: return err
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker: return jsonify({'error': 'Missing ticker param'}), 400
    period_type, n = parse_params()
    return jsonify(fetch_one(ticker, period_type, n))

@app.route('/stocks')
def get_stocks():
    err = check_key()
    if err: return err
    raw = request.args.get('tickers', '')
    tickers = [t.strip().upper() for t in raw.split(',') if t.strip()]
    if not tickers: return jsonify({'error': 'Missing tickers param'}), 400
    period_type, n = parse_params()
    return jsonify({'data': [fetch_one(t, period_type, n) for t in tickers],
                    'count': len(tickers), 'period_type': period_type, 'n': n})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
