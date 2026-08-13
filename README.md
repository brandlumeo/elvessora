# Elvassora — Luxury Perfume E-Commerce Platform

A complete Python/Django e-commerce website for luxury perfume sales, built for **Elvassora**.

## Features

### Storefront
- Homepage with hero banners, best sellers, new arrivals, collections, gift sets
- Shop with search, advanced filters, and sorting
- Product detail pages with fragrance notes, variants, reviews, related products
- Shop by Fragrance Family (Woody, Floral, Fresh, Citrus, Oud, etc.)
- Shop by Occasion (Daily Wear, Office, Date Night, Wedding, etc.)
- Best Sellers & New Arrivals sections
- Gift Sets with custom wrapping and personalized messages
- **Perfume Finder Quiz** — recommends products based on preferences

### E-Commerce
- Add to Cart, Buy Now, Wishlist
- Coupon/promo codes
- Guest checkout
- Secure checkout with tax & shipping calculation
- **Razorpay** payment integration (Card, UPI, Net Banking)
- Cash on Delivery (COD)
- Order tracking, order history, reorder

### Customer Account
- Registration, login, logout
- Forgot/reset password
- Profile management
- Saved addresses
- Wishlist
- Order history & details

### Admin Dashboard (`/admin/`)
- Products, categories, collections, fragrance families, occasions
- Product variants, sizes, inventory & stock
- Orders, payments, refunds
- Customers, reviews, coupons
- Gift sets, banners, homepage sections
- Site settings, FAQs, legal pages
- Low-stock indicators

### Marketing
- WhatsApp integration
- Newsletter subscription
- Promotional pop-ups
- Seasonal offers via coupons

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment (optional)

Copy `.env.example` to `.env` and update values:

```bash
copy .env.example .env
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Load sample data

```bash
python manage.py setup_sample_data
```

This creates:
- Site settings & brand info
- 6 sample perfumes with variants
- Fragrance families & occasions
- Sample coupon `WELCOME10`
- Admin user: **admin / admin123**

### 5. Start the server

```bash
python manage.py runserver
```

Visit:
- **Storefront:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/

## Project Structure

```
elvassora/
├── config/          # Django settings & URLs
├── core/            # Homepage, About, Contact, FAQ, Legal pages
├── products/        # Products, categories, collections, gift sets
├── accounts/        # User registration, profile, addresses, wishlist
├── cart/            # Shopping cart
├── orders/          # Checkout, payments, order tracking
├── quiz/            # Perfume Finder Quiz
├── reviews/         # Product reviews & ratings
├── marketing/       # Banners, newsletter, promo popups
├── templates/       # HTML templates
└── static/          # CSS, JS assets
```

## Payment Setup

For live payments, add your Razorpay credentials to `.env`:

```
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
```

Without Razorpay keys, online orders are auto-confirmed in development mode. COD always works.

## Tech Stack

- **Python 3.12+**
- **Django 6**
- **Bootstrap 5** (UI)
- **SQLite** (development database)
- **Razorpay** (payments)
- **Pillow** (image uploads)

## License

Proprietary — Elvassora Perfumes
