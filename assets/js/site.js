(function () {
  // Mobil menü
  var menuDugme = document.querySelector('.menu-dugme');
  var menu = document.getElementById('ana-menu');
  if (menuDugme && menu) {
    menuDugme.addEventListener('click', function () {
      var acik = menu.classList.toggle('acik');
      menuDugme.setAttribute('aria-expanded', acik);
    });
  }

  // Alt menüler
  var acilirlar = document.querySelectorAll('.acilir');
  function hepsiniKapat(haric) {
    acilirlar.forEach(function (li) {
      if (li !== haric) {
        li.classList.remove('acik');
        li.querySelector('.alt-dugme').setAttribute('aria-expanded', 'false');
      }
    });
  }
  acilirlar.forEach(function (li) {
    var d = li.querySelector('.alt-dugme');
    d.addEventListener('click', function (e) {
      e.stopPropagation();
      hepsiniKapat(li);
      var acik = li.classList.toggle('acik');
      d.setAttribute('aria-expanded', acik);
    });
  });
  document.addEventListener('click', function () { hepsiniKapat(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hepsiniKapat(); });

  // Tarih hesapları
  function gunFarki(metin) {
    if (!metin) return null;
    var p = metin.split('-');
    if (p.length !== 3) return null;
    var hedef = new Date(+p[0], +p[1] - 1, +p[2]);
    var bugun = new Date(); bugun.setHours(0, 0, 0, 0);
    return Math.round((hedef - bugun) / 86400000);
  }
  function durumYaz(kutu, gun) {
    var etiket = kutu.querySelector('.durum');
    if (!etiket || gun === null) return;
    if (gun < 0) { etiket.textContent = 'Süresi doldu'; etiket.className = 'durum kapali'; kutu.classList.add('bitti'); }
    else if (gun === 0) { etiket.textContent = 'Son gün'; etiket.className = 'durum acil'; kutu.classList.add('yakin-bitis'); }
    else if (gun <= 14) { etiket.textContent = gun + ' gün kaldı'; etiket.className = 'durum acil'; kutu.classList.add('yakin-bitis'); }
    else { etiket.textContent = gun + ' gün kaldı'; etiket.className = 'durum normal'; }
  }
  document.querySelectorAll('[data-son]').forEach(function (k) { durumYaz(k, gunFarki(k.getAttribute('data-son'))); });

  // Çağrı listeleri: süresi dolanlar sona, istenirse gizle
  document.querySelectorAll('[data-cagri-liste]').forEach(function (liste) {
    var kartlar = Array.prototype.slice.call(liste.querySelectorAll('.cagri'));
    var sadeceAcik = liste.hasAttribute('data-sadece-acik');
    var limit = parseInt(liste.getAttribute('data-limit'), 10) || Infinity;
    var gosterilen = 0;
    kartlar.filter(function (k) { return k.classList.contains('bitti'); })
      .forEach(function (k) { liste.appendChild(k); });
    kartlar.forEach(function (k) {
      if (sadeceAcik && k.classList.contains('bitti')) { k.hidden = true; return; }
      if (gosterilen >= limit) { k.hidden = true; return; }
      gosterilen++;
    });
    if (sadeceAcik && gosterilen === 0) {
      var bos = liste.parentNode.querySelector('[data-acik-yok]');
      if (bos) bos.hidden = false;
    }
  });

  // Ana sayfa: en yakın son başvuru
  var yakin = document.getElementById('yakin-cagri');
  var veri = document.getElementById('cagri-verisi');
  if (yakin && veri) {
    var cagrilar = [];
    try { cagrilar = JSON.parse(veri.textContent); } catch (e) {}
    var enYakin = null;
    cagrilar.forEach(function (c) {
      var g = gunFarki(c.s);
      if (g !== null && g >= 0 && (!enYakin || g < enYakin.g)) { enYakin = { g: g, c: c }; }
    });
    var gunAlan = yakin.querySelector('[data-gun]');
    var adAlan = yakin.querySelector('[data-ad]');
    var tarihAlan = yakin.querySelector('[data-tarih]');
    if (enYakin) {
      gunAlan.innerHTML = enYakin.g === 0 ? 'Bugün' : enYakin.g + '<small>gün</small>';
      adAlan.textContent = enYakin.c.t;
      adAlan.href = enYakin.c.u;
      var p = enYakin.c.s.split('-');
      tarihAlan.textContent = 'Son başvuru ' + p[2] + '.' + p[1] + '.' + p[0];
    } else {
      gunAlan.textContent = '–';
      adAlan.textContent = 'Şu an açık çağrı yok';
    }
  }

  // Faaliyet takvimi: geçmiş faaliyetleri ayır
  document.querySelectorAll('[data-takvim]').forEach(function (t) {
    var yaklasan = t.querySelector('[data-yaklasan]');
    var gecmis = t.querySelector('[data-gecmis]');
    var ogeler = Array.prototype.slice.call(yaklasan.querySelectorAll('.takvim-oge'));
    var gecmisler = ogeler.filter(function (o) { var g = gunFarki(o.getAttribute('data-tarih')); return g !== null && g < 0; });
    gecmisler.reverse().forEach(function (o) { gecmis.appendChild(o); });
    if (gecmisler.length) t.querySelector('[data-gecmis-kutu]').hidden = false;
    if (gecmisler.length === ogeler.length) t.querySelector('[data-yaklasan-yok]').hidden = false;
  });

  // Sayaçlar: görünür olunca sayarak artsın
  var azHareket = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var sayilar = document.querySelectorAll('.sayac-sayi');
  if (!azHareket && 'IntersectionObserver' in window && sayilar.length) {
    var gozlem = new IntersectionObserver(function (girdiler) {
      girdiler.forEach(function (g) {
        if (!g.isIntersecting) return;
        gozlem.unobserve(g.target);
        var el = g.target, hedef = parseInt(el.getAttribute('data-sayi'), 10) || 0, bas = null;
        function adim(t) {
          if (!bas) bas = t;
          var oran = Math.min((t - bas) / 1200, 1);
          el.textContent = Math.round(hedef * (1 - Math.pow(1 - oran, 3)));
          if (oran < 1) requestAnimationFrame(adim);
        }
        requestAnimationFrame(adim);
      });
    }, { threshold: 0.4 });
    sayilar.forEach(function (s) { s.textContent = '0'; gozlem.observe(s); });
  }

  // Haber kaydırıcı
  document.querySelectorAll('[data-kaydirici]').forEach(function (k) {
    var slaytlar = k.querySelectorAll('.slayt');
    if (slaytlar.length < 2) return;
    var sira = k.querySelector('[data-sira]');
    var i = 0, zamanlayici;
    function goster(n) {
      slaytlar[i].hidden = true;
      i = (n + slaytlar.length) % slaytlar.length;
      slaytlar[i].hidden = false;
      if (sira) sira.textContent = (i + 1) + ' / ' + slaytlar.length;
    }
    function baslat() { if (!azHareket) zamanlayici = setInterval(function () { goster(i + 1); }, 6000); }
    function durdur() { clearInterval(zamanlayici); }
    var onceki = k.querySelector('[data-onceki]'), sonraki = k.querySelector('[data-sonraki]');
    if (onceki) onceki.addEventListener('click', function () { durdur(); goster(i - 1); });
    if (sonraki) sonraki.addEventListener('click', function () { durdur(); goster(i + 1); });
    k.addEventListener('mouseenter', durdur);
    k.addEventListener('focusin', durdur);
    goster(0);
    baslat();
  });
})();
