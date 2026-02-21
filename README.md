# Taylan Dili (Türkçe)

## Çekirdek Özellikler

- Deðiþken atama: `x = 10`
- Yazdýrma: `yazdýr("merhaba")`
- Koþul:

```taylan
eðer x > 5:
    yazdýr("büyük")
deðilse:
    yazdýr("küçük")
bitti
```

- Döngü:

```taylan
x = 0
döngü x < 3:
    yazdýr(x)
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

### tsql (basit dosya tabanlý DB)
```taylan
dahil "tsql"

sql_db_olustur("db")
sql_tablo_sil("db", "kisiler")
sql_tablo_olustur("db", "kisiler", "ad,yas")
sql_ekle("db", "kisiler", "Ali,25")
yazdýr(sql_sec("db", "kisiler"))
```

### tmath (matematik)
```taylan
dahil "tmath"

yazdýr(mat_topla(5, 7))
yazdýr(mat_kok(81))
```

### tml (ML + basit NN)
```taylan
dahil "tml"

ml_model_olustur("model.json", 2)
ml_egit("model.json", "1,2,2,1", "3,3", 100, 0.01)
yazdýr(ml_tahmin("model.json", "1,2"))

ml_nn_olustur("nn.json", 2, 3, 1)
ml_nn_egit("nn.json", "0,0, 0,1, 1,0, 1,1", "0,1,1,0", 2000, 0.1)
yazdýr(ml_nn_tahmin("nn.json", "1,0"))
```

### tdata (tablo/dizi)
```taylan
dahil "tdata"

t = tablo_olustur("ad,yas")
tablo_ekle(t, "Ali,25")
tablo_ekle(t, "Ayse,30")
yazdýr(tablo_sec(t, "ad"))
```

### tdate (tarih/saat)
```taylan
dahil "tdate"

yazdýr(tarih())
yazdýr(saat())
yazdýr(tarih_saat())
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

yazdýr(kutu(10, 4))
```

### thttp (GET)
```taylan
dahil "thttp"

yazdýr(http_get("https://example.com"))
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
yazdýr(json_yukle("a.json"))
```

### tconfig
```taylan
dahil "tconfig"

yazdýr(cfg_oku(".env"))
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
- `GET /dashboard` ve `GET /dashboard.html` -> `dashboard.html`
- `GET /health` -> `ok`
- `POST /api/register` -> JSON `{ "username", "password" }`
- `POST /api/login` -> JSON `{ "username", "password" }`

Linux binary uret (WSL/Ubuntu):
`python3 -m taylan.cli native native_web.tay -o native_web --cc gcc`

Calistir:
`./native_web`

Render:
- Start Command: `chmod +x native_web && ./native_web`

## Setup'siz PaaS Dagitim Rehberi

Bu proje, Linux native binary (`native_web`) ile Python runtime olmadan calisir.
Yani platformda `setup.exe` kurmadan, dogrudan servis olarak acabilirsin.

Onemli:
- Bu adimlar Linux tabanli PaaS icindir.
- `users.db` dosyasi gecici diskte tutulur. Free planlarda yeniden baslatmada silinebilir.
- Kalici veri gerekiyorsa Postgres gibi harici veritabani kullan.

### 1. Render (Web Service)

1. Repo: `TaylanAslan1/Taylan-dil`
2. Build Command: `echo "skip build"`
3. Start Command: `chmod +x native_web && ./native_web`
4. Deploy et ve test et:
5. `GET /health` -> `ok`

### 2. Railway (GitHub Deploy)

1. New Project -> Deploy from GitHub Repo
2. Start Command: `chmod +x native_web && ./native_web`
3. Gerekirse Variables icine `PORT` tanimla (Railway genelde otomatik verir)
4. Deploy sonrasi `https://<app-url>/health` ile kontrol et

### 3. Fly.io (Docker ile)

1. Projeye Dockerfile ekle:

```dockerfile
FROM debian:bookworm-slim
WORKDIR /app
COPY native_web /app/native_web
COPY index.html /app/index.html
COPY dashboard.html /app/dashboard.html
RUN chmod +x /app/native_web
EXPOSE 8080
CMD ["/app/native_web"]
```

2. `fly launch`
3. `fly deploy`
4. `https://<app-name>.fly.dev/health` ile kontrol et

### 4. Google Cloud Run (Docker ile)

1. Yukaridaki Dockerfile'i kullan
2. Image build/push et
3. Cloud Run servisi olustur
4. Container port: `8080`
5. `/health` endpointinden kontrol et

### 5. Koyeb / Northflank / benzeri Docker PaaS

1. Dockerfile ile deploy et
2. Start command gerekmez (Docker `CMD` kullanilir)
3. Port olarak `8080` acik olsun
4. `/health` ile canlilik testi yap



### Turkiye notu (TR saglayicilar)

- Paylasimli hostinglerde native binary calistirma yetkisi genelde yoktur.
- TR bir VDS/VPS (Linux) alirsan ayni komutla calistirabilirsin: `chmod +x native_web && ./native_web`
- Domain baglamak icin Nginx reverse proxy ile uygulamayi `PORT` uzerinden yayinla.
