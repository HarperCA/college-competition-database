"""为可以入库的比赛从官方来源页面找海报并转存。

用法: python3 -I scripts/fetch_posters.py data/学生比赛名录/2026-10-26复判/全量比赛资料表.csv data/学生比赛名录/海报
只处理 最终分类=可以入库 的行；只从该行"官方来源"里标【官方】的页面取图。
结果: <输出目录>/posters/<源行号>.<ext> 和 <输出目录>/海报清单.csv（可断点续跑）。
"""
import csv, hashlib, io, os, re, subprocess, sys, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
IMG_DIR = os.path.join(OUT, 'posters')
os.makedirs(IMG_DIR, exist_ok=True)
LIST = os.path.join(OUT, '海报清单.csv')
COLS = ['源行号', 'name', 'editionYear', '海报文件', '海报原图网址', '所在页面', '判定依据', '宽x高',
        '状态', '核验日期']
TODAY = time.strftime('%Y-%m-%d')
POSTER_WORDS = re.compile(r'海报|poster|宣传画|主视觉|kv', re.I)
SKIP_WORDS = re.compile(r'logo|icon|banner_bg|qrcode|二维码|erweima|wx|weixin|gif$|loading|arrow|btn|share', re.I)


def fetch(url, max_bytes=30_000_000):
    """curl 走预配置代理；返回 (bytes, final_url) 或 (None, err)。"""
    p = subprocess.run(['curl', '-sSL', '-m', '40', '--max-filesize', str(max_bytes), '-A',
                        'Mozilla/5.0', '-w', '\n%{url_effective}', url], capture_output=True)
    if p.returncode != 0:
        return None, p.stderr.decode(errors='ignore').strip()[:120]
    body, _, final = p.stdout.rpartition(b'\n')
    return body, final.decode(errors='ignore')


def official_pages(row):
    urls = []
    for line in row['官方来源'].split('\n'):
        if '| 官方 |' not in line:
            continue
        m = re.search(r'https?://\S+', line)
        if m and not m.group(0).lower().split('?')[0].endswith(('.pdf', '.doc', '.docx', '.zip', '.xlsx')):
            urls.append(m.group(0).rstrip('|').strip())
    return list(dict.fromkeys(urls))


def candidates(html, page_url):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('data-original') or img.get('src') or ''
        if not src or src.startswith('data:'):
            continue
        absu = urljoin(page_url, src)
        hint = ' '.join(filter(None, [img.get('alt'), img.get('title'), src,
                                      (img.find_parent(['p', 'div', 'figure']) or img).get_text(' ', strip=True)[:80]]))
        if SKIP_WORDS.search(src):
            continue
        out.append((absu, hint))
    return out


def accept(data, hint):
    """返回 (是否采用, 依据, 宽x高)。保守：要么带'海报'字样，要么是大尺寸竖版图。"""
    try:
        im = Image.open(io.BytesIO(data)); w, h = im.size
    except Exception:
        return False, '', ''
    if w < 400 or h < 400:
        return False, '', f'{w}x{h}'
    if POSTER_WORDS.search(hint):
        return True, '官方页面图片，替代文本/文件名/上下文含"海报"类字样', f'{w}x{h}'
    if h >= 900 and h / w >= 1.25:
        return True, '官方页面大尺寸竖版图（疑似海报，需人工确认）', f'{w}x{h}'
    return False, '', f'{w}x{h}'


done = {}
if os.path.exists(LIST):
    for r in csv.DictReader(open(LIST, encoding='utf-8-sig')):
        done[r['源行号']] = r
rows = [r for r in csv.DictReader(open(SRC, encoding='utf-8-sig')) if r['最终分类'] == '可以入库']
results = []
for i, row in enumerate(rows, 1):
    k = row['源行号']
    if k in done and done[k]['状态'] != '页面无法访问':
        results.append(done[k]); continue
    rec = dict.fromkeys(COLS, ''); rec.update(源行号=k, name=row['name'], editionYear=row['editionYear'], 核验日期=TODAY)
    pages = official_pages(row)
    reachable = False
    for page in pages:
        html, final = fetch(page, 5_000_000)
        if html is None:
            continue
        reachable = True
        for imgurl, hint in candidates(html.decode('utf-8', errors='ignore'), final)[:40]:
            data, _ = fetch(imgurl)
            if not data:
                continue
            ok, why, size = accept(data, hint)
            if ok:
                ext = (Image.open(io.BytesIO(data)).format or 'jpg').lower().replace('jpeg', 'jpg')
                fn = f'{k}.{ext}'
                open(os.path.join(IMG_DIR, fn), 'wb').write(data)
                rec.update(海报文件=f'posters/{fn}', 海报原图网址=imgurl, 所在页面=page, 判定依据=why,
                           宽x高=size, 状态='已转存' if '海报' in why else '已转存（待人工确认）')
                break
        if rec['海报文件']:
            break
    if not rec['海报文件']:
        rec['状态'] = '未找到官方海报' if reachable else ('页面无法访问' if pages else '无可抓取的官方网页来源')
        rec['所在页面'] = '；'.join(pages)
    results.append(rec)
    if i % 20 == 0 or i == len(rows):
        with open(LIST, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(results + [d for kk, d in done.items() if kk not in {r['源行号'] for r in results}])
        print(f'{i}/{len(rows)}', flush=True)
