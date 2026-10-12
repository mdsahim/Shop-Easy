# ShopEasy – Modern Online Shopping Store

A complete, modern, responsive full-stack e-commerce web application built with **Python 3**, **Django**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript**.

![ShopEasy Banner](https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1200&q=80)

---

## 🌟 Key Features

### 🛍️ Customer Experience & Storefront
- **Modern Responsive Design**: Clean aesthetic inspired by leading e-commerce platforms (Amazon, Apple, Shopify), optimized for desktop, tablet, and mobile screens.
- **Product Catalog & Category Filtering**: Browse by categories (*Audio & Headphones, Wearables, Laptops, Accessories, Smartphones*).
- **Live Search & Dynamic Sorting**: Real-time keyword search across names and descriptions, sorting by *Price: Low to High*, *Price: High to Low*, *Newest Arrivals*, and *Customer Rating*.
- **Interactive Product Details**: High-resolution image galleries, stock counters, dynamic quantity selectors, customer rating summaries, and related product recommendations.
- **Session-Based Shopping Cart**:
  - Preserves cart items across sessions and browser visits.
  - Live AJAX quantity increment/decrement and removal with dynamic toast notifications.
  - Real-time cart badge counter in the navigation bar.
  - Automatic inventory stock limits (prevents adding more than available stock).
  - Free shipping progress calculator ($50+ free shipping threshold).

### 💳 Checkout & Order Processing
- **Cash on Delivery (COD)**: Transparent, risk-free checkout where customers pay upon package delivery.
- **Server-Side Security & Price Integrity**:
  - Product prices and totals are verified against the authoritative database.
  - Double validation on both frontend and backend for customer name, email, phone, and PIN/postal code.
  - Atomically locks inventory rows (`select_for_update`) to prevent race conditions during high-volume purchasing.
  - Automatically reduces stock count immediately after order creation.
- **Order Confirmation & Invoicing**:
  - Generates unique order reference codes (`SE-YYYYMMDD-XXXXXX`).
  - Visual order timeline status tracker (*Order Placed &rarr; Processing &rarr; Shipped &rarr; Delivered*).
  - Printable receipt/invoice view.

### 👤 Customer Authentication & Account Portal
- Built on Django's secure authentication system with PBKDF2 password hashing.
- User registration, login, and logout.
- **Customer Order History**: Logged-in customers can view their complete past orders and detailed invoices.
- **Data Protection**: Strict permission controls preventing customers from viewing orders that do not belong to them.

### ⚙️ Administrator Dashboard
- Fully customized Django Admin interface (`/admin/`):
  - Product management with inline stock and price editing.
  - Category manager with automatic slug generation.
  - Order management with nested itemized order lines (`OrderItemInline`).
  - Search and filter orders by customer name, order number, delivery status, and date.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons |
| **Backend** | Python 3.12, Django 5/6 |
| **Database** | SQLite 3 (ACID-compliant with transactional order processing) |
| **Image Handling** | Pillow |

---

## 🚀 Quick Start Guide (Windows & VS Code)

### 1. Prerequisites
Make sure **Python 3.10+** is installed on your computer. You can check by opening PowerShell or Command Prompt:
```powershell
python --version
```

### 2. Open Project in VS Code
Open VS Code, press `Ctrl + O` (or `File > Open Folder...`), and select the project folder:
```
e-commerace website pr 1
```

Open a new terminal inside VS Code: `` Ctrl + ` `` (Backtick) or `Terminal > New Terminal`.

---

### 3. Setup Virtual Environment

Run the following commands in the PowerShell terminal:

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1
```

> **Note for PowerShell execution policy**: If you see a script execution policy restriction, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```

---

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

### 5. Apply Database Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

---

### 6. Load Sample Products & Demo Accounts

We have created an automated data seeding command that populates categories, all requested sample products, and ready-to-use demo accounts:

```powershell
python manage.py load_sample_data
```

This will automatically load:
- **Sample Products**:
  - Wireless Headphones
  - Smart Watch
  - Laptop
  - Mechanical Keyboard
  - Gaming Mouse
  - Smartphone
  - Bluetooth Speaker
  - Laptop Stand
  - Noise-Cancelling Earbuds
  - 4K Ultra HD IPS Monitor
- **Demo Customer Account**:
  - Username: `customer`
  - Password: `customer123`
- **Superuser Admin Account**:
  - Username: `admin`
  - Password: `admin123`

*(Optional) You can also create your own custom superuser anytime using:*
```powershell
python manage.py createsuperuser
```

---

### 7. Run the Development Server

Start the local Django server:

```powershell
python manage.py runserver
```

Now open your web browser and visit:
- **Storefront**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Dashboard**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Running Automated Tests

Run the full automated test suite (17 tests covering catalog views, search, cart session, stock reduction, checkout integrity, and authentication security):

```powershell
python manage.py test store
```

Expected result:
```
Ran 17 tests in 50.357s
OK
```

---

## 📁 Project Structure

```
e-commerace website pr 1/
├── manage.py                     # Django CLI management entrypoint
├── requirements.txt              # Project dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignored files (venv, db, media)
├── README.md                     # Documentation & setup instructions
│
├── ecommerce_store/              # Project Configuration Package
│   ├── __init__.py
│   ├── settings.py               # Django settings (apps, templates, static/media, sessions)
│   ├── urls.py                   # Root URL routing & media serving
│   ├── asgi.py
│   └── wsgi.py
│
├── store/                        # Main E-Commerce Application
│   ├── __init__.py
│   ├── admin.py                  # Admin configuration (Products, Categories, Orders)
│   ├── apps.py                   # Store app configuration
│   ├── cart.py                   # Session-based shopping cart manager
│   ├── context_processors.py     # Global cart count & category context processor
│   ├── forms.py                  # CheckoutForm, UserRegisterForm, UserLoginForm
│   ├── models.py                 # Category, Product, Order, OrderItem models
│   ├── tests.py                  # Automated test suite (17 tests)
│   ├── urls.py                   # Storefront URL endpoints
│   ├── views.py                  # Catalog, cart, checkout, order & auth views
│   │
│   ├── management/
│   │   └── commands/
│   │       └── load_sample_data.py # Sample data seeding command
│   │
│   └── migrations/               # Database migration files
│       └── 0001_initial.py
│
├── templates/                    # HTML5 Templates
│   ├── base.html                 # Master layout (Header, Navbar, Footer, Toasts)
│   └── store/
│       ├── home.html             # Homepage (Hero banner, perks, featured, categories)
│       ├── product_list.html     # Catalog with search, filters & sorting
│       ├── product_detail.html   # Single product details & quantity selector
│       ├── cart.html             # Shopping cart view with itemized table
│       ├── checkout.html         # Delivery details form & COD confirmation
│       ├── order_confirmation.html # Order success receipt & timeline tracker
│       ├── order_history.html    # Customer's past orders dashboard
│       ├── order_detail.html     # Single order invoice breakdown
│       ├── login.html            # Customer login page
│       ├── register.html         # Customer registration page
│       └── contact.html          # Contact support & inquiries page
│
└── static/                       # Static Frontend Assets
    ├── css/
    │   └── style.css             # Custom design system & animations
    ├── js/
    │   └── script.js             # AJAX cart operations, counters & notifications
    └── images/                   # Static icons & brand assets
```

---

## 🔒 Security Best Practices Implemented

1. **CSRF Protection**: All POST forms include Django's `{% csrf_token %}` and JavaScript requests carry `X-CSRFToken`.
2. **Authoritative Server Pricing**: The checkout view never trusts prices passed by the client; unit prices and totals are calculated from the database.
3. **Database Concurrency & Race Conditions**: Implemented `transaction.atomic()` and `select_for_update()` during checkout to guarantee accurate stock subtraction.
4. **Order Confidentiality**: Customers can only view their own orders (`order.user == request.user`); attempts by other users return a 404 response.
5. **Secure Password Hashing**: Utilizes Django's PBKDF2 with SHA256 password hashing.
6. **Input Validation**: Backend regex validation for phone numbers, postal codes, and email uniqueness.

---

## 📄 License
This project is open-source and free to use for personal, educational, or commercial purposes.
#   S h o p - E a s y  
 