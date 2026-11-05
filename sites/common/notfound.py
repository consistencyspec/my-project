"""「ページが見つかりません」のページの共通部品(2つのサイトで共通)。"""

# URLの最後に付いた余計な文字(「）」や句読点など)を取り除いて、正しいページへ移す。
# 例: /rice/）→ /rice/ 。取り除くものがなければ何もしない(同じページへ移り続けることはない)。
FIX_URL_JS = """
(function () {
  var p;
  try { p = decodeURIComponent(location.pathname); } catch (e) { p = location.pathname; }
  var cleaned = p.replace(/[^A-Za-z0-9\\-\\/].*$/, '');
  if (cleaned.slice(-1) !== '/') cleaned += '/';
  if (cleaned !== p && cleaned !== location.pathname) location.replace(cleaned);
})();
"""


def not_found_body(h1_class, links, other_site):
    """links: [(URL, 名前), ...]、other_site: (URL, 説明)"""
    items = "".join(f'<li><a href="{u}">{n}</a></li>' for u, n in links)
    return f"""<h1 class="{h1_class}">ページが見つかりません</h1>
<p>URLが間違っているか、ページがなくなった可能性があります。下のページからお探しください。</p>
<ul class="nf-links">{items}</ul>
<p>{other_site[1]}は、<a href="{other_site[0]}">{other_site[0]}</a> にあります。</p>
<script>{FIX_URL_JS}</script>"""
