# GitHub Profil Kurulumu

**Hedef depo:** https://github.com/OguzhanDUYAR/OguzhanDUYAR  
**Varsayılan dal:** `main`

## Kurulum

1. ZIP arşivini aç. Dosyaları **klasör yapısını koruyarak** profil deposunun köküne kopyala: `README.md`, `assets/`, `scripts/`, `tests/`, `.github/workflows/profile.yml`.
2. Değişiklikleri `main` dalına commit et ve GitHub'a gönder.
3. Depodaki **Actions → Refresh profile visuals → Run workflow** yolunu izleyerek ilk güncellemeyi başlat.
4. Çalışma tamamlandığında **Actions** sayfasındaki sonucu kontrol et. Başarılıysa `assets/*.svg` dosyalarının yer tutucuları gerçek istatistik ve animasyonlarla değiştirilir.
5. Sonrasında iş akışı her gün yaklaşık **05:17 UTC (08:17 Türkiye saati)** için planlanır. GitHub, zamanlanan işleri gecikmeli çalıştırabilir veya uzun süre etkin olmayan depolarda devre dışı bırakabilir.

## CLI ile yükleme

Profil deposunu önceden klonladıysan arşiv içeriğini köküne kopyaladıktan sonra:

```bash
set -euo pipefail
git status --short
python3 -m unittest discover -s tests -v
# Dosyaların hedef depoya ait olduğuna emin ol.
git add README.md assets/ scripts/ tests/ .github/workflows/profile.yml
git commit -m "feat(profile): redesigned bioinformatics and engineering profile"
git push origin main
```

## Sorun giderme

- **Action çalışmıyorsa:** Depo → Settings → Actions → General bölümündeki GitHub Actions etkinliğini, izinleri ve `GITHUB_TOKEN` için `contents: write` yetkisinin kurum politikasıyla engellenmediğini kontrol et. İş akışı YAML dosyasında bu izin zaten tanımlıdır.
- **Sayılar `--` kalıyorsa:** İlk workflow henüz başarılı çalışmamıştır. Gerçek olmayan başlangıç istatistikleri özellikle konulmamıştır.
- **İstatistikler gecikiyorsa:** Bunlar anlık veri değil, günlük oluşturulan GitHub API anlık görüntüleridir.
- **Stats veya snake adımı hata verirse:** Üçüncü taraf Action sürümlerini ve iş akışı günlüğünü incele. Bu hizmetler kapalıyken yerel SVG panelleri çalışmaya devam edebilir; yalnızca workflow başarıyla tamamlanırsa yeni dosyalar commit edilir.
- **Özel depolar görünmüyorsa:** Tasarım yalnızca herkese açık verileri göstermeyi amaçlar. `GITHUB_TOKEN` ile özel depo bilgilerinin toplanması hedeflenmez.
- **Kişisel bilgiler:** README'ye geçersiz eski Twitter bağlantısı ve e-posta adresi konulmadı. İstersen iletişim bilgilerini sonradan ekleyebilirsin.

## Verilerin kapsamı

- **Public repos:** GitHub `/users/OguzhanDUYAR/repos` uç noktasının döndürdüğü sahibine ait açık depolar.
- **Stars earned:** Bu depolardaki yıldızların toplamı, senin yıldızladığın depoların sayısı değil.
- **Active / 90d:** Son 90 günde push tarihi bulunan, fork olmayan açık depoların sayısı.
- **Languages:** Fork olmayan ve dil atanmış açık depolardaki **birincil dil** dağılımı; bayt veya yetkinlik yüzdesi değil.
- **Recent pulse:** Açık depolardaki `pushed_at` alanına göre sıralama.
- **Graph/stats:** `stats-organization` ve `Platane/snk` üzerinden GitHub Actions ortamında üretilir; çalışma koşulları üçüncü tarafların sürümlerine bağlıdır.

Herhangi bir yeni özel erişim anahtarı (PAT) oluşturulması veya depoya konulması gerekmez. İlgili akış GitHub'ın otomatik `GITHUB_TOKEN` değerini kullanır.
