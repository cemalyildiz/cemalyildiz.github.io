# GTÜ TTO ham içeriğini (_import) site yapısına dönüştürür. Tek seferlik.
import os, re, json, shutil, datetime, urllib.parse as up
import yaml
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify
try:
    from PIL import Image
except ImportError:
    Image = None

IMP = "_import"
M = json.load(open(f"{IMP}/manifest.json", encoding="utf-8"))
SAYFALAR, DOSYALAR = M["sayfalar"], M["dosyalar"]
TR = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")
rapor = {"gorsel": 0, "gorsel_yok": 0, "dosya": 0}

def slug(s, n=80):
    s = up.unquote(s).translate(TR).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s[:n].rstrip("-")) or "icerik"

def html_of(url):
    v = SAYFALAR.get(url)
    if not v or "dosya" not in v:
        return None
    return BeautifulSoup(open(f"{IMP}/html/{v['dosya']}", encoding="utf-8").read(), "html.parser")

def urls(prefix):
    return [u for u in SAYFALAR if u.startswith("https://gtutto.com/" + prefix)]

def yaz(yol, on, govde=""):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    on = {k: v for k, v in on.items() if v not in (None, "", [])}
    with open(yol, "w", encoding="utf-8") as f:
        f.write("---\n" + yaml.safe_dump(on, allow_unicode=True, sort_keys=False, width=1000) + "---\n")
        if govde:
            f.write(govde.strip() + "\n")

def yaz_veri(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        yaml.safe_dump(veri, f, allow_unicode=True, sort_keys=False, width=1000)

# ---------- görseller ve dosyalar ----------
_gorsel = {}
def mutlak(u):
    if not u: return None
    u = up.urljoin("https://gtutto.com/", u.strip())
    p = up.urlparse(u)
    if p.netloc not in ("gtutto.com", "www.gtutto.com"): return u
    return up.urlunparse(("https", "gtutto.com", p.path, "", p.query, ""))

def gorsel(u, genislik=1600):
    u = mutlak(u)
    if not u or not u.startswith("https://gtutto.com/"): return u
    if u in _gorsel: return _gorsel[u]
    yerel = DOSYALAR.get(u)
    yol = up.unquote(up.urlparse(u).path).lstrip("/")
    parca = yol.split("/")
    klasor = slug(parca[-2].replace("_v", ""), 40) if len(parca) > 1 else "genel"
    ad, uz = os.path.splitext(parca[-1]); uz = uz.lower()
    ad = slug(ad, 60)
    if uz in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        kaynak = f"{IMP}/dosyalar/{yerel}" if yerel and not str(yerel).startswith("HATA") else None
        hedef_uz = ".jpg"
        if kaynak and os.path.exists(kaynak) and Image:
            try:
                im = Image.open(kaynak)
                saydam = im.mode in ("RGBA", "LA", "P") and (im.mode != "P" or "transparency" in im.info)
                if saydam:
                    im = im.convert("RGBA")
                    saydam = im.getextrema()[3][0] < 255
                hedef_uz = ".png" if saydam else ".jpg"
                hedef = f"assets/img/gtutto/{klasor}/{ad}{hedef_uz}"
                os.makedirs(os.path.dirname(hedef), exist_ok=True)
                if im.width > genislik:
                    im = im.resize((genislik, round(im.height * genislik / im.width)), Image.LANCZOS)
                if saydam:
                    im.save(hedef, optimize=True)
                else:
                    im.convert("RGB").save(hedef, "JPEG", quality=82, optimize=True, progressive=True)
                rapor["gorsel"] += 1
            except Exception as e:
                print("Görsel işlenemedi:", u, e); rapor["gorsel_yok"] += 1
        else:
            rapor["gorsel_yok"] += 1
        sonuc = f"/assets/img/gtutto/{klasor}/{ad}{hedef_uz}"
    else:
        hedef = f"assets/dosyalar/gtutto/{klasor}/{ad}{uz}"
        kaynak = f"{IMP}/dosyalar/{yerel}" if yerel and not str(yerel).startswith("HATA") else None
        if kaynak and os.path.exists(kaynak):
            os.makedirs(os.path.dirname(hedef), exist_ok=True)
            shutil.copyfile(kaynak, hedef); rapor["dosya"] += 1
        sonuc = "/" + hedef
    _gorsel[u] = sonuc
    return sonuc

def ham_dosya(u):
    u = mutlak(u)
    if not u or not u.startswith("https://gtutto.com/"): return u
    yerel = DOSYALAR.get(u)
    yol = up.unquote(up.urlparse(u).path).lstrip("/").split("/")
    klasor = slug(yol[-2].replace("_v", ""), 40) if len(yol) > 1 else "genel"
    ad, uz = os.path.splitext(yol[-1])
    hedef = f"assets/dosyalar/gtutto/{klasor}/{slug(ad, 60)}{uz.lower()}"
    kaynak = f"{IMP}/dosyalar/{yerel}" if yerel and not str(yerel).startswith("HATA") else None
    if kaynak and os.path.exists(kaynak):
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        shutil.copyfile(kaynak, hedef); rapor["dosya"] += 1
    return "/" + hedef

# ---------- bağlantı eşlemesi ----------
STATIK = {
    "": "/", "hakkimizda": "/kurumsal/hakkimizda/", "kurumsal-kimlik": "/kurumsal/kurumsal-kimlik/",
    "yonetim-kurulu": "/kurumsal/yonetim-kurulu/", "ekibimiz": "/kurumsal/ekibimiz/",
    "kurumsal-isbirlikleri": "/kurumsal/kurumsal-isbirlikleri/", "haberler-duyurular": "/duyurular/",
    "girisimcilerimiz": "/girisimcilik/girisimcilerimiz/", "cozum-ortaklari": "/girisimcilik/cozum-ortaklari/",
    "firsatlar": "/girisimcilik/firsatlar/", "biggbio": "/girisimcilik/biggbio/",
    "kulucka-merkezi": "/girisimcilik/programlar-ve-destekler/", "tto": "/hizmetler/tto/",
    "egitimler": "/hizmetler/egitimler/", "faaliyetlerimiz": "/faaliyetler/",
    "faaliyet-takvimi": "/faaliyetler/faaliyet-takvimi/", "patentler": "/patentler/",
    "kariyer": "/kariyer/", "blog": "/blog/", "iletisim": "/iletisim/",
}
DETAY = {"faaliyet-detail": "/faaliyet/", "haberler-duyurular-detail": "/duyurular/",
         "blog-detail": "/blog/", "egitim-detail": "/egitimler/"}
def detay_slug(u):
    return slug(up.urlparse(u).path.split("/", 2)[2])

def link(h):
    u = mutlak(h)
    if not u or not u.startswith("https://gtutto.com/"): return h
    yol = up.unquote(up.urlparse(u).path).strip("/")
    ilk = yol.split("/")[0]
    if ilk in DETAY and "/" in yol: return DETAY[ilk] + detay_slug(u) + "/"
    if yol in STATIK: return STATIK[yol]
    if ilk in ("panel", "assets"): return gorsel(u)
    return u

# ---------- HTML -> Markdown ----------
IZIN = {"p", "br", "strong", "b", "em", "i", "u", "a", "ul", "ol", "li", "h2", "h3", "h4", "h5", "h6",
        "img", "blockquote", "table", "thead", "tbody", "tr", "td", "th", "hr"}
def md(dugum):
    if dugum is None: return ""
    d = BeautifulSoup(str(dugum), "html.parser")
    for t in d(["script", "style", "button", "form", "input", "iframe", "noscript", "svg", "i"]):
        if t.name == "i" and t.get_text(strip=True): continue
        t.decompose()
    for t in d.find_all(True):
        if t.name == "img":
            src = t.get("src") or t.get("data-src")
            t.attrs = {"src": gorsel(src), "alt": ""} if src else {}
            if not src: t.decompose()
        elif t.name == "a":
            h = t.get("href")
            t.attrs = {"href": link(h)} if h and h != "#" else {}
        elif t.name in IZIN:
            t.attrs = {}
    for t in d.find_all(True):
        if t.name not in IZIN: t.unwrap()
    m = markdownify(str(d), heading_style="ATX", bullets="-", strip=["span"])
    m = re.sub(r"[ \t]+\n", "\n", m)
    m = re.sub(r"\n{3,}", "\n\n", m)
    return m.strip()

def baslik(s):
    h = s.select_one(".page-header h1")
    return h.get_text(" ", strip=True) if h else ""

# ---------- detay sayfaları ----------
YAZILAN = set()
def detaylar(onek, klasor, dosya_adi_tarihli=True):
    n = 0
    for u in urls(onek + "/"):
        s = html_of(u)
        if not s: continue
        if "A PHP Error was encountered" in s.get_text():
            rapor["bozuk"] = rapor.get("bozuk", 0) + 1; continue
        p = s.select_one(".post-single")
        if not p: continue
        on = {"title": baslik(s) or (p.find("h4").get_text(" ", strip=True) if p.find("h4") else "")}
        tarih = p.select_one(".post-meta li")
        t = tarih.get_text(strip=True) if tarih else ""
        on["date"] = t if re.match(r"\d{4}-\d\d-\d\d$", t) else None
        kapak = p.select_one(".post-thumb img")
        on["gorsel"] = gorsel(kapak.get("src")) if kapak else None
        galeri = [gorsel(i.get("src")) for i in p.select(".course-block img") if i.get("src")]
        on["galeri"] = galeri
        icerik = p.select_one(".single-post-content")
        if icerik:
            for x in icerik.select(".post-meta"): x.decompose()
            h4 = icerik.find("h4")
            if h4: h4.decompose()
        sl = detay_slug(u)
        ad = f"{on['date']}-{sl}" if (dosya_adi_tarihli and on.get("date")) else sl
        yol, i = f"{klasor}/{ad}.md", 2
        while yol in YAZILAN:
            yol = f"{klasor}/{ad}-{i}.md"; i += 1
        YAZILAN.add(yol)
        yaz(yol, on, md(icerik))
        n += 1
    print(onek, n)

detaylar("faaliyet-detail", "_faaliyetler", False)
detaylar("haberler-duyurular-detail", "_duyurular")
detaylar("blog-detail", "_blog")

# eğitimler
n = 0
for u in urls("egitim-detail/"):
    s = html_of(u)
    if not s or "A PHP Error was encountered" in s.get_text(): continue
    on = {"title": baslik(s)}
    k = s.select_one(".course-thumbnail img")
    on["gorsel"] = gorsel(k.get("src")) if k else None
    alanlar = {"Düzenleyen": "duzenleyen", "Başvuru Tarihi": "basvuru_tarihi", "Süre": "sure",
               "Eğitim Tipi": "egitim_tipi", "Fiyat": "fiyat"}
    for li in s.select(".course-details-info li"):
        d = li.find("div", recursive=False) or li.find("div")
        if not d: continue
        sp = d.find("span")
        if not sp: continue
        anahtar = sp.get_text(strip=True).rstrip(":").strip()
        deger = d.get_text(" ", strip=True).replace(sp.get_text(" ", strip=True), "", 1).strip()
        if anahtar in alanlar and deger: on[alanlar[anahtar]] = deger
    b = s.select_one(".buy-btn a")
    if b and b.get("href") and b["href"] != "#": on["basvuru_link"] = b["href"]
    yaz(f"_egitimler/{detay_slug(u)}.md", on, md(s.select_one(".single-course-details")))
    n += 1
print("egitim", n)

# ---------- ekip ve yönetim ----------
def ekip(sayfa, grup, onek):
    s = html_of("https://gtutto.com/" + sayfa)
    for i, k in enumerate(s.select(".team-item"), 1):
        ad = k.select_one(".team-info h5").get_text(" ", strip=True)
        on = {"title": ad, "grup": grup, "sira": i}
        un = k.select_one(".team-info p.yk-color")
        on["unvan"] = un.get_text(" ", strip=True) if un else None
        for p in k.select(".team-info p"):
            if "yk-color" in (p.get("class") or []): continue
            t = p.get_text(" ", strip=True)
            if "@" in t: on["eposta"] = t
            elif re.search(r"\d{3}", t): on["telefon"] = t
        img = k.find("img")
        on["foto"] = gorsel(img.get("src"), 600) if img else None
        yaz(f"_ekip/{onek}-{i:02d}-{slug(ad, 40)}.md", on)
ekip("yonetim-kurulu", "Yönetim Kurulu", "gtu-yk")
ekip("ekibimiz", "Ekip", "gtu-ekip")

# ---------- kart listeleri ----------
def kartlar(sayfa):
    s = html_of("https://gtutto.com/" + sayfa)
    out = []
    for k in s.select(".course-block"):
        img = k.select_one(".course-img img")
        h = k.select_one("h4")
        p = k.select_one(".course-content p")
        a = [x for x in k.select(".course-content a.btn") if x.get("href") and x["href"] != "#"]
        out.append({"ad": h.get_text(" ", strip=True) if h else "", "gorsel": gorsel(img.get("src"), 800) if img else "",
                    "aciklama": p.get_text(" ", strip=True) if p else "", "baglanti": [(x.get_text(strip=True), x["href"]) for x in a]})
    return out

for i, k in enumerate(kartlar("girisimcilerimiz"), 1):
    web = k["baglanti"][0][1] if k["baglanti"] else None
    yaz(f"_girisimciler/{i:02d}-{slug(k['ad'], 50)}.md", {"title": k["ad"], "logo": k["gorsel"], "web": web, "sira": i})

yaz_veri("_data/cozum_ortaklari.yml", {"logolar": [{"ad": k["ad"], "logo": k["gorsel"], "aciklama": k["aciklama"], "link": ""} for k in kartlar("cozum-ortaklari")]})
yaz_veri("_data/firsatlar.yml", {"kartlar": [{"ad": k["ad"], "gorsel": k["gorsel"], "aciklama": k["aciklama"]} for k in kartlar("firsatlar")]})
kimlik = []
for k in kartlar("kurumsal-kimlik"):
    d = {"gorsel": k["gorsel"]}
    for etiket, h in k["baglanti"]:
        d[slug(etiket, 20).replace("-", "_")] = ham_dosya(h)
    kimlik.append(d)
yaz_veri("_data/kurumsal_kimlik.yml", {"dosyalar": kimlik})
s = html_of("https://gtutto.com/kurumsal-isbirlikleri")
yaz_veri("_data/isbirlikleri.yml", {"logolar": [{"ad": slug(os.path.splitext(i["src"].split("/")[-1])[0]).replace("-", " ").title(), "logo": gorsel(i["src"], 600), "link": ""} for i in s.select(".client-logo img")]})

# ---------- ana sayfa: sayaçlar, kutular, vitrin ----------
s = html_of("https://gtutto.com/")
yaz_veri("_data/sayaclar.yml", {"sayaclar": [{"etiket": c.find("h6").get_text(" ", strip=True), "sayi": int(re.sub(r"\D", "", c.select_one(".counter").get_text()) or 0), "ikon": gorsel(c.find("img")["src"], 300)} for c in s.select(".counter-item")]})
yaz_veri("_data/anasayfa_kutular.yml", {"kutular": [{"baslik": k.find("h4").get_text(" ", strip=True), "metin": k.find("p").get_text(" ", strip=True) if k.find("p") else "", "ikon": gorsel(k.find("img")["src"], 300), "link": ""} for k in s.select(".feature-item") if k.find("img") and k.find("h4")]})
vitrin = []
for it in s.select(".testimonial-item"):
    img = it.find("img")
    if not img or "/slider/" not in img.get("src", ""): continue
    h = it.find("h4"); d = it.select_one(".testimonial-info-desc"); a = it.find("a", href=True)
    vitrin.append({"baslik": h.get_text(" ", strip=True) if h else "", "metin": d.get_text(" ", strip=True) if d else "",
                   "gorsel": gorsel(img["src"]), "link": link(a["href"]) if a else ""})
yaz_veri("_data/vitrin.yml", {"slaytlar": vitrin})

# ---------- faaliyet takvimi -> etkinlikler ----------
s = html_of("https://gtutto.com/faaliyet-takvimi")
for sec in s.select(".curriculum-sections"):
    d = {}
    for li in sec.select("li.section"):
        t = li.get_text(" ", strip=True)
        if ":" in t:
            k, v = t.split(":", 1); d[k.strip()] = v.strip()
    ad = d.get("Faaliyet Adı")
    if not ad: continue
    m = re.match(r"(\d\d)\.(\d\d)\.(\d{4})", d.get("Faaliyet Tarihi", ""))
    tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    yaz(f"_etkinlikler/{tarih or 'tarihsiz'}-{slug(ad, 50)}.md", {"title": ad, "date": tarih, "saat": d.get("Faaliyet Saati"), "ozet": d.get("Açıklama")})

# ---------- tek sayfalar ----------
def statik(sayfa, md_dosya, baslik_, kalici, liste=None):
    s = html_of("https://gtutto.com/" + sayfa)
    govde = []
    if s:
        for sec in s.find_all("section"):
            c = sec.get("class") or []
            if any(x in c for x in ("page-header", "footer", "map")): continue
            govde.append(md(sec))
    on = {"title": baslik_, "permalink": kalici, "liste": liste}
    yaz(f"sayfalar/{md_dosya}.md", on, "\n\n".join(g for g in govde if g))

statik("hakkimizda", "hakkimizda", "Hakkımızda", "/kurumsal/hakkimizda/")
statik("tto", "tto", "TTO", "/hizmetler/tto/")
statik("biggbio", "biggbio", "BiggBio", "/girisimcilik/biggbio/")
statik("kulucka-merkezi", "programlar-ve-destekler", "Programlar ve Destekler", "/girisimcilik/programlar-ve-destekler/")
statik("patentler", "patentler", "Patentler", "/patentler/")
statik("kariyer", "kariyer", "Kariyer", "/kariyer/")
statik("iletisim", "iletisim", "İletişim", "/iletisim/")

yaz("sayfalar/egitimler.md", {"title": "Eğitimler", "permalink": "/hizmetler/egitimler/", "liste": "egitimler"})
yaz("sayfalar/firsatlar.md", {"title": "Fırsatlar", "permalink": "/girisimcilik/firsatlar/", "liste": "firsat-kartlari"})
yaz("sayfalar/kurumsal-kimlik.md", {"title": "Kurumsal Kimlik", "permalink": "/kurumsal/kurumsal-kimlik/", "liste": "kimlik"})

# ---------- genel bilgiler ----------
g = yaml.safe_load(open("_data/genel.yml", encoding="utf-8")) or {}
g.update({"site_adi": "GTÜ TTO", "logo": gorsel("https://gtutto.com/assets/images/gtu-tto-logo.png", 600),
          "logo_acik": gorsel("https://gtutto.com/assets/images/gtu-tto-logo-light.png", 600),
          "alt_metin": "Bilgiyi Güce, Araştırmayı Değere Dönüştürüyoruz! Üniversite-sanayi işbirliğiyle, yenilikçi projeleri hayata geçirerek ülkemizin bilgi birikimine ve ekonomisine katkı sağlıyoruz.",
          "telefon": "+(90) 262 605 24 37", "eposta": "tto@gtu.edu.tr",
          "adres": "Cumhuriyet Mah. Gebze Teknik Üniversitesi 41400 Gebze/Kocaeli",
          "instagram": "https://www.instagram.com/gtu.tto/", "linkedin": "https://www.linkedin.com/company/gtu-tto/home/",
          "facebook": "https://www.facebook.com/gebzetto41", "arama_gizle": True})
yaz_veri("_data/genel.yml", g)

print("RAPOR", rapor)
