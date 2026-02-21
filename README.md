# Taylan Dili (Türkçe)

## Çekirdek Özellikler

- Değişken atama: `x = 10`
- Yazdırma: `yazdır("merhaba")`
- Koşul:

```taylan
eğer x > 5:
    yazdır("büyük")
değilse:
    yazdır("küçük")
bitti
```

- Döngü:

```taylan
x = 0
döngü x < 3:
    yazdır(x)
    x = x + 1
bitti
```

- Fonksiyon:

```taylan
fonksiyon kare(n):
    dön n * n
bitti
```

- Modül dahil etme:

```taylan
dahil "tmath"
```

## Yerel Kütüphaneler

### tsql (basit dosya tabanlı DB)
```taylan
dahil "tsql"

sql_db_olustur("db")
sql_tablo_sil("db", "kisiler")
sql_tablo_olustur("db", "kisiler", "ad,yas")
sql_ekle("db", "kisiler", "Ali,25")
yazdır(sql_sec("db", "kisiler"))
```

### tmath (matematik)
```taylan
dahil "tmath"

yazdır(mat_topla(5, 7))
yazdır(mat_kok(81))
```

### tml (ML + basit NN)
```taylan
dahil "tml"

ml_model_olustur("model.json", 2)
ml_egit("model.json", "1,2,2,1", "3,3", 100, 0.01)
yazdır(ml_tahmin("model.json", "1,2"))

ml_nn_olustur("nn.json", 2, 3, 1)
ml_nn_egit("nn.json", "0,0, 0,1, 1,0, 1,1", "0,1,1,0", 2000, 0.1)
yazdır(ml_nn_tahmin("nn.json", "1,0"))
```

### tdata (tablo/dizi)
```taylan
dahil "tdata"

t = tablo_olustur("ad,yas")
tablo_ekle(t, "Ali,25")
tablo_ekle(t, "Ayse,30")
yazdır(tablo_sec(t, "ad"))
```

### tdate (tarih/saat)
```taylan
dahil "tdate"

yazdır(tarih())
yazdır(saat())
yazdır(tarih_saat())
```

### timg (görüntü)
```taylan
dahil "timg"

ppm = ppm_olustur(2, 2, 255, 0, 0)
ppm_kaydet("kirmizi.ppm", ppm)
```

### tgame (ASCII)
```taylan
dahil "tgame"

yazdır(kutu(10, 4))
```

### thttp (GET)
```taylan
dahil "thttp"

yazdır(http_get("https://example.com"))
```

### tasync (bekleme)
```taylan
dahil "tasync"

bekle(500)
```

### tjson
```taylan
dahil "tjson"

json_yaz("a.json", {"ad":"Ali"})
yazdır(json_yukle("a.json"))
```

### tconfig
```taylan
dahil "tconfig"

yazdır(cfg_oku(".env"))
```

### tlog
```taylan
dahil "tlog"

log_yaz("log.txt", "merhaba")
```

## Replit Kurulum

Bu proje Replit Linux ortaminda calisir. Ayrica native bir EXE derlemek zorunda degilsin.

1. Replitte projeyi ac.
2. `Run` tusuna bas.
3. Baslangic komutu: `python -m taylan.cli calistir replit_web.tay`
4. Sunucu `PORT` ortam degiskeninden port alir ve `0.0.0.0` hostunda dinler.

Ek not:
- `replit.nix` icinde `python311` ve `gcc` var.
- Web modul adi `tweb` olarak kullanilir (`dahil "tweb"`).

## Self-Host Bootstrap (v2)

Bu adim, Taylan ile yazilmis transpiler + blok parser + expression AST parser kullanir ve `.tay` kaynagini Python koduna cevirir.

Komut:
`python -m taylan.cli selfhost selfhost/sample_core.tay -o selfhost/sample_core.py`

Calistirma:
`python selfhost/sample_core.py`

Ikinci ornek:
`python -m taylan.cli selfhost selfhost/sample_blocks.tay -o selfhost/sample_blocks.py`

Ucuncu ornek:
`python -m taylan.cli selfhost selfhost/sample_expr.tay -o selfhost/sample_expr.py`

Not:
- Cekirdek alt kume desteklenir (`eger`, `degilse`, `dongu`, `fonksiyon`, `don`, atama, `yazdir`).
- Bu surumde tokenizasyon, blok parse ve expression parse akisi Taylan kodu icindedir (`selfhost/transpiler_v0.tay`).
- Sonraki adim: Python cikisi yerine dogrudan hedef kod/bytecode uretmek.

## Native Binary (Python Runtime Yok)

Bu mod, `.tay` dosyasini C koduna cevirir ve C derleyici ile native binary uretir.
Uretilen binary calisirken Python gerektirmez.

Sadece C uret:
`python -m taylan.cli native native_demo.tay --emit-c-only -o native_demo.c`

Binary uret (gcc gerekir):
`python -m taylan.cli native native_demo.tay -o native_demo`

Calistir:
`./native_demo`

Render notu:
- Render'a `native_demo` gibi derlenmis Linux binary yukleyip `Start Command` olarak `./native_demo` verebilirsin.
- Bu durumda runtime olarak Python calismaz; sadece binary calisir.

## Native Web Binary (Render)

`native_web.tay` dosyasi, PORT ortamini okuyup HTTP server baslatir:
- `GET /` ve `GET /index.html` -> `index.html`
- `GET /health` -> `ok`
- `POST /api/register` -> JSON `{ "username", "password" }`
- `POST /api/login` -> JSON `{ "username", "password" }`

Linux binary uret (WSL/Ubuntu):
`python3 -m taylan.cli native native_web.tay -o uygulama --cc gcc`

Calistir:
`./uygulama`

Render:
- Start Command: `./uygulama`
