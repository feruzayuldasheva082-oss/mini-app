# Hot Dog Mafia — Telegram Mini App va Admin Bot

Telegram uchun **Hot Dog Mafia** loyihasi: mijozlar boti (Mini App ichida buyurtma berish), admin boti (buyurtmalarni boshqarish) va Mini App web-interfeysi.

## Tarkib
- `customer_bot.py` — mijozlar boti (`/start`, Mini App tugmalari)
- `admin_bot.py` — admin boti (yangi buyurtmalar, holatni o‘zgartirish)
- `server.py` — FastAPI server (Mini App va API: `/api/menu`, `/api/orders`)
- `webapp/` — Mini App (`index.html`, `app.js`, `style.css`, `logo.svg`)
- `database.py` — SQLite baza (menyu va buyurtmalar)
- `config.py`, `.env.example` — sozlamalar
- `main.py` — server + mijoz boti + admin botni birga ishga tushirish

## Imkoniyatlar
- **Mini App:** “Hot Dog Mafia’ga xush kelibsiz!”, **Buyurtma berish**, **Mening buyurtmalarim**, **Mafia menyusi** (ishlaydigan tugmalar/navigatsiya)
- Savat, buyurtmani rasmiylashtirish va “Buyurtmangiz qabul qilindi!” holati (alohida muvaffaqiyat ekranida)
- **Admin bot:** `/new`, `/orders`, `/order <id>`, inline tugmalar bilan status o‘zgartirish (`Yangi`, `Qabul qilindi`, `Tayyorlanmoqda`, `Yetkazilmoqda`, `Yakunlandi`, `Bekor qilindi`)
- Yangi buyurtma kelganda admin(lar)ga xabar yuboriladi

## O‘rnatish
1. Python 3.10+ o‘rnating.
2. Kutubxonalar:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env.example` ni `.env` ga nusxalang va to‘ldiring:
   - `CUSTOMER_BOT_TOKEN` — mijozlar boti tokeni
   - `ADMIN_BOT_TOKEN` — admin boti tokeni
   - `ADMIN_IDS` — admin Telegram ID(lar)i, vergul bilan (masalan: `123456789,987654321`)
   - `WEBAPP_URL` — Mini App ochiladigan **HTTPS** manzil (Telegram Mini App uchun HTTPS shart; lokal testda `ngrok`/`cloudflare tunnel` ishlating)
   - `HOST`, `PORT` — server manzili (standart `0.0.0.0:8000`)

## Ishga tushirish
```bash
python main.py
```
- Web/Mini App: `http://localhost:8000` (yoki `WEBAPP_URL`)
- Tokenlar kiritilmagan bo‘lsa mos bot ishga tushmaydi, lekin server ishlashi mumkin.

## Eslatma
- `WEBAPP_URL` botdagi WebApp tugmasi uchun ishlatiladi, shuning uchun u tashqaridan ochiladigan HTTPS bo‘lishi kerak.
- **ngrok free domen** birinchi marta ochilganda “Visit Site” ogohlantirish sahifasini ko‘rsatishi mumkin. Uni oddiy brauzerda bir marta ochib, “Visit Site” ni bosing — keyin Telegram ichida Mini App normal ochiladi.
- Mijoz botidagi “Mening buyurtmalarim” tugmasi Mini App’ni to‘g‘ridan-to‘g‘ri buyurtmalar bo‘limida ochadi (`?view=orders`). `/tart` buyrug‘i ham `/start` kabi ishlaydi.
- Menyu va buyurtmalar `hotdog_mafia.db` (SQLite) faylida saqlanadi; birinchi ishga tushishda namuna menyu avtomatik qo‘shiladi.
- `logo.svg` va `webapp/logo.svg` — Hot Dog Mafia logotipi (stikersiz, toza dizayn).
