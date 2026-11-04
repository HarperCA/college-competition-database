"""给每条"可以入库"的比赛找一张海报并转存。

用法:
  pip install beautifulsoup4 pillow
  python3 -I scripts/fetch_posters.py data/学生比赛名录/2026-11-04补查/全量比赛资料表.csv data/学生比赛名录/海报 [并发数，默认8]

取图来源：该行"官方来源"里的网页（标"官方"的优先，其次是"检索所得来源"），跳过 pdf/doc 等附件。
每页按以下顺序取第一张合格的图（宽高都 >= 400 像素）：
  1. 替代文本/文件名/上下文含"海报 poster 宣传画 主视觉 KV"的图        -> 状态 已转存（海报）
  2. 大尺寸竖版图（高 >= 900 且 高/宽 >= 1.25）                         -> 状态 已转存（疑似海报，待人工确认）
  3. 页面声明的分享图（og:image / twitter:image）                         -> 状态 已转存（页面分享图，非海报）
  4. 页面上面积最大的图                                                   -> 状态 已转存（页面主图，非海报）
官方页面都没有合格图片时记"未找到图片"；打不开记"页面无法访问"；没有网页来源记"无可抓取的网页来源"。
结果: <输出目录>/posters/<源行号>.<ext>、<输出目录>/海报清单.csv。可断点续跑：已转存的行跳过，其余重试。
"""
import csv, io, os, re, subprocess, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image

Image.MAX_IMAGE_PIXELS = 200_000_000
SRC, OUT = sys.argv[1], sys.argv[2]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
IMG_DIR = os.path.join(OUT, 'posters')
os.makedirs(IMG_DIR, exist_ok=True)
LIST = os.path.join(OUT, '海报清单.csv')
COLS = ['源行号', 'name', 'editionYear', '海报文件', '海报原图网址', '所在页面', '取图方式', '宽x高', '状态', '核验日期']
TODAY = time.strftime('%Y-%m-%d')
POSTER_WORDS = re.compile(r'海报|poster|宣传画|主视觉|\bkv\b', re.I)
SKIP_WORDS = re.compile(r'logo|icon|favicon|banner_bg|qrcode|二维码|erweima|wechat|weixin|loading|arrow|btn|share|avatar|\.gif(\?|$)|\.svg(\?|$)', re.I)
DOC_EXT = ('.pdf', '.doc', '.docx', '.zip', '.rar', '.xls', '.xlsx', '.ppt', '.pptx')
MAX_IMGS_PER_PAGE = 40
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def fetch(url, max_bytes=30_000_000, referer=None):
    """返回 (bytes, final_url) 或 (None, 错误信息)。用 curl（Windows 10+、macOS、Linux 自带）。"""
    cmd = ['curl', '-sSL', '--compressed', '-m', '40', '--max-filesize', str(max_bytes), '-A', UA,
           '-w', '\n%{url_effective}']
    if referer:
        cmd += ['-e', referer]
    try:
        p = subprocess.run(cmd + [url], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None, 'timeout'
    if p.returncode != 0:
        return None, p.stderr.decode(errors='ignore').strip()[:120]
    body, _, final = p.stdout.rpartition(b'\n')
    return body, final.decode(errors='ignore')


def decode_html(raw):
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000], re.I)
    for enc in ([m.group(1).decode()] if m else []) + ['utf-8', 'gb18030']:
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode('utf-8', errors='ignore')


def web_pages(row):
    """官方页面在前，检索所得来源在后；去重，跳过附件。"""
    official, searched = [], []
    for line in row['官方来源'].split('\n'):
        m = re.search(r'https?://[^\s|]+', line)
        if not m or m.group(0).lower().split('?')[0].endswith(DOC_EXT):
            continue
        if '| 官方 |' in line:
            official.append(m.group(0))
        elif '检索所得来源' in line:
            searched.append(m.group(0))
    return list(dict.fromkeys(official + searched))


def candidates(html, page_url):
    soup = BeautifulSoup(html, 'html.parser')
    meta = []
    for key in ('og:image', 'twitter:image'):
        tag = soup.find('meta', attrs={'property': key}) or soup.find('meta', attrs={'name': key})
        if tag and tag.get('content'):
            meta.append(urljoin(page_url, tag['content']))
    imgs = []
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('data-original') or img.get('data-lazy-src') or img.get('src') or ''
        if not src or src.startswith('data:') or SKIP_WORDS.search(src):
            continue
        parent = img.find_parent(['p', 'div', 'figure', 'a'])
        hint = ' '.join(filter(None, [img.get('alt'), img.get('title'), src,
                                      parent.get_text(' ', strip=True)[:80] if parent else '']))
        imgs.append((urljoin(page_url, src), hint))
    return list(dict.fromkeys(meta)), list(dict.fromkeys(imgs))[:MAX_IMGS_PER_PAGE]


def open_image(data):
    try:
        im = Image.open(io.BytesIO(data)); im.load()
        return im
    except Exception:
        return None


def pick(page, html, final):
    """在一个页面上按优先级选图。返回 (data, img_url, 方式, 宽x高, 状态, 扩展名) 或 None。"""
    meta, imgs = candidates(html, final)
    tiers = {1: None, 2: None, 3: None, 4: None}
    best_area = 0
    for url, hint in imgs:
        data, _ = fetch(url, referer=final)
        im = open_image(data) if data else None
        if not im:
            continue
        w, h = im.size
        if w < 400 or h < 400:
            continue
        rec = (data, url, im)
        if POSTER_WORDS.search(hint):
            tiers[1] = rec; break
        if tiers[2] is None and h >= 900 and h / w >= 1.25:
            tiers[2] = rec
        if w * h > best_area:
            best_area, tiers[4] = w * h, rec
    if tiers[1] is None and tiers[2] is None:
        for url in meta:
            data, _ = fetch(url, referer=final)
            im = open_image(data) if data else None
            if im and min(im.size) >= 400:
                tiers[3] = (data, url, im); break
    labels = {1: ('替代文本/文件名/上下文含"海报"类字样', '已转存（海报）'),
              2: ('大尺寸竖版图', '已转存（疑似海报，待人工确认）'),
              3: ('页面分享图 og:image', '已转存（页面分享图，非海报）'),
              4: ('页面上面积最大的图', '已转存（页面主图，非海报）')}
    for t in (1, 2, 3, 4):
        if tiers[t]:
            data, url, im = tiers[t]
            ext = (im.format or 'jpg').lower().replace('jpeg', 'jpg')
            return data, url, labels[t][0], f'{im.size[0]}x{im.size[1]}', labels[t][1], ext, t
    return None


def process(row):
    k = row['源行号']
    rec = dict.fromkeys(COLS, '')
    rec.update(源行号=k, name=row['name'], editionYear=row['editionYear'], 核验日期=TODAY)
    pages = web_pages(row)
    if not pages:
        rec['状态'] = '无可抓取的网页来源'
        return rec
    reachable, best = False, None
    for page in pages:
        raw, final = fetch(page, 5_000_000)
        if raw is None:
            continue
        reachable = True
        got = pick(page, decode_html(raw), final)
        if got and (best is None or got[6] < best[0][6]):
            best = (got, page)
        if best and best[0][6] <= 2:  # 已找到海报或疑似海报，不再翻其他页面
            break
    if best:
        (data, url, how, size, status, ext, _), page = best
        fn = f'{k}.{ext}'
        with open(os.path.join(IMG_DIR, fn), 'wb') as f:
            f.write(data)
        rec.update(海报文件=f'posters/{fn}', 海报原图网址=url, 所在页面=page, 取图方式=how, 宽x高=size, 状态=status)
    else:
        rec['状态'] = '未找到图片' if reachable else '页面无法访问'
        rec['所在页面'] = '；'.join(pages)
    return rec


def save(results):
    with open(LIST, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, COLS); w.writeheader()
        w.writerows(sorted(results.values(), key=lambda r: int(r['源行号'])))


def main():
    results = {}
    if os.path.exists(LIST):
        for r in csv.DictReader(open(LIST, encoding='utf-8-sig')):
            results[r['源行号']] = r
    rows = [r for r in csv.DictReader(open(SRC, encoding='utf-8-sig')) if r['最终分类'] == '可以入库']
    todo = [r for r in rows if not results.get(r['源行号'], {}).get('状态', '').startswith('已转存')]
    print(f'可以入库 {len(rows)} 条，本次处理 {len(todo)} 条，并发 {WORKERS}', flush=True)
    lock, n = threading.Lock(), 0
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(process, r): r['源行号'] for r in todo}
        for fut in as_completed(futs):
            try:
                rec = fut.result()
            except Exception as e:  # 单条出错不影响整体
                rec = dict.fromkeys(COLS, ''); rec.update(源行号=futs[fut], 状态=f'出错：{e}'[:100], 核验日期=TODAY)
            with lock:
                results[rec['源行号']] = rec; n += 1
                if n % 20 == 0 or n == len(todo):
                    save(results); print(f'{n}/{len(todo)}', flush=True)
    save(results)
    from collections import Counter
    for k, v in Counter(r['状态'] for r in results.values()).most_common():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
