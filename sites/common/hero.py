"""トップページの大きなカルーセル(写真とステップの紹介)。2つのサイトで共通。

スライドは各サイトの config.json の "hero_slides" に書きます。
  {"kicker": "STEP 01", "title": "まず、予算を決める。", "text": "...", "button": "予算の決め方", "href": "/meyasu/",
   "image": "hero-2.jpg", "image_alt": "田んぼの写真"}
image は sites/<サイト>/static/ に置いた写真のファイル名です。写真がない(または空の)ときは、
落ち着いた色の面に大きな文字(kicker)を表示します。
"""
from html import escape


def e(text):
    return escape(str(text), quote=True)


# 自動で次のスライドへ(6秒ごと)。マウスを乗せている間・操作中は止める。動きを減らす設定の人には自動で動かさない。
HERO_JS = """
document.querySelectorAll('[data-hero]').forEach(function (root) {
  var track = root.querySelector('.hs-track'), slides = track.children, dots = root.querySelectorAll('.hs-dot');
  var i = 0, timer = null, reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function go(n) {
    i = (n + slides.length) % slides.length;
    track.scrollTo({ left: slides[i].offsetLeft - track.offsetLeft, behavior: reduce ? 'auto' : 'smooth' });
    dots.forEach(function (d, k) { d.setAttribute('aria-current', k === i ? 'true' : 'false'); });
  }
  function start() { if (!reduce && slides.length > 1) { stop(); timer = setInterval(function () { go(i + 1); }, 6000); } }
  function stop() { if (timer) clearInterval(timer); timer = null; }
  root.querySelector('.hs-prev').addEventListener('click', function () { go(i - 1); start(); });
  root.querySelector('.hs-next').addEventListener('click', function () { go(i + 1); start(); });
  dots.forEach(function (d, k) { d.addEventListener('click', function () { go(k); start(); }); });
  track.addEventListener('scroll', function () {
    var n = Math.round(track.scrollLeft / track.clientWidth);
    if (n !== i) { i = n; dots.forEach(function (d, k) { d.setAttribute('aria-current', k === i ? 'true' : 'false'); }); }
  }, { passive: true });
  root.addEventListener('mouseenter', stop); root.addEventListener('mouseleave', start);
  root.addEventListener('focusin', stop); root.addEventListener('focusout', start);
  start();
});
"""


def hero_html(slides, available_images, brand):
    """slides: config の hero_slides、available_images: static にあるファイル名の集合、brand: 左上の小さな英字。"""
    if not slides:
        return ""
    items = []
    for n, s in enumerate(slides, 1):
        img = s.get("image", "")
        if img and img in available_images:
            visual = (f'<div class="hs-photo"><img src="/{e(img)}" alt="{e(s.get("image_alt", ""))}" '
                      f'width="1200" height="800" {"" if n == 1 else "loading=\"lazy\" "}decoding="async"></div>')
        else:
            visual = f'<div class="hs-photo hs-blank" aria-hidden="true"><span>{e(s.get("kicker", ""))}</span></div>'
        title = "<br>".join(e(t) for t in s["title"].split("\n"))
        button = (f'<a class="hs-btn" href="{e(s["href"])}">{e(s["button"])}</a>' if s.get("button") and s.get("href") else "")
        items.append(f"""<div class="hs-slide" role="group" aria-roledescription="スライド" aria-label="{n} / {len(slides)}">
<div class="hs-text">
<p class="hs-brand">{e(brand)}</p>
<p class="hs-kicker">{e(s.get('kicker', ''))}</p>
<p class="hs-title">{title}</p>
<p class="hs-desc">{e(s.get('text', ''))}</p>
{button}
</div>
{visual}
</div>""")
    dots = "".join(f'<button class="hs-dot" type="button" aria-label="{n}枚目" aria-current="{"true" if n == 1 else "false"}"></button>'
                   for n in range(1, len(slides) + 1))
    return f"""<section class="hs" data-hero aria-roledescription="カルーセル" aria-label="このサイトの使い方">
<div class="hs-track">{''.join(items)}</div>
<div class="hs-nav"><button class="hs-prev" type="button" aria-label="前へ">←</button>{dots}<button class="hs-next" type="button" aria-label="次へ">→</button></div>
<script>{HERO_JS}</script>
</section>"""


HERO_CSS = """
/* トップのカルーセル */
.hs { margin: 0 calc(50% - 50vw); background: var(--bg-2); border-bottom: 1px solid var(--rule); }
.hs-track { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; max-width: 1240px; margin: 0 auto; }
.hs-track::-webkit-scrollbar { display: none; }
.hs-slide { flex: 0 0 100%; scroll-snap-align: start; display: grid; grid-template-columns: 5fr 6fr; min-height: 460px; }
.hs-text { padding: 56px 56px 48px; display: flex; flex-direction: column; justify-content: center; }
.hs-brand { margin: 0; font-family: var(--latin); font-size: .8rem; letter-spacing: .32em; color: var(--ink-2); }
.hs-brand::after { content: ""; display: block; width: 52px; height: 1px; background: var(--ink); margin: 18px 0 26px; }
.hs-kicker { margin: 0 0 8px; font-family: var(--latin); font-size: .82rem; letter-spacing: .3em; color: var(--accent); }
.hs-title { margin: 0 0 18px; font-size: 2.3rem; line-height: 1.55; letter-spacing: .12em; font-weight: 500; color: var(--ink); }
.hs-desc { margin: 0 0 30px; font-size: .92rem; color: var(--ink-2); line-height: 2; max-width: 26em; }
.hs-btn { align-self: flex-start; background: var(--night); color: #fff; text-decoration: none; font-size: .9rem; letter-spacing: .16em; padding: 14px 30px; transition: opacity .2s; }
.hs-btn:hover { opacity: .85; }
.hs-btn::after { content: "  →"; }
.hs-photo { position: relative; overflow: hidden; background: var(--rule); }
.hs-photo img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.hs-blank { display: grid; place-items: center; background: linear-gradient(135deg, var(--bg) 0%, var(--bg-2) 100%); border-left: 1px solid var(--rule); }
.hs-blank span { font-family: var(--latin); font-size: clamp(3rem, 8vw, 6.5rem); letter-spacing: .08em; color: var(--rule); font-weight: 500; }
.hs-nav { display: flex; justify-content: center; align-items: center; gap: 10px; padding: 16px 0 18px; }
.hs-prev, .hs-next { background: none; border: 0; font-size: 1rem; color: var(--ink-2); cursor: pointer; padding: 4px 14px; font-family: var(--latin); }
.hs-dot { width: 52px; height: 2px; padding: 0; border: 0; background: var(--rule); cursor: pointer; }
.hs-dot[aria-current="true"] { background: var(--ink); }
@media (max-width: 760px) {
  .hs-slide { grid-template-columns: 1fr; grid-template-rows: 240px auto; min-height: 0; }
  .hs-photo { order: -1; }
  .hs-blank { border-left: 0; border-bottom: 1px solid var(--rule); }
  .hs-text { padding: 28px 22px 26px; }
  .hs-brand::after { margin: 12px 0 16px; }
  .hs-title { font-size: 1.55rem; }
  .hs-desc { margin-bottom: 22px; }
  .hs-dot { width: 32px; }
}
"""
