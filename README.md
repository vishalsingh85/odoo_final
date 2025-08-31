# 🎉 EventHive – MVP

*EventHive* is a minimal yet functional *event management platform* that enables organizers to create and manage events while allowing attendees to discover and book them.  
The MVP is designed to deliver an end-to-end usable product with essential features, while keeping implementation lean and scalable.

---

## 🎯 Target Users
- *Organizers* → Event creators (admins, managers) who post and manage events.  
- *Attendees* → Users who browse, book, and attend events.  
- (Optional in MVP: Volunteers / role-based access with simple user types).

---

## 🚀 Core MVP Features

### 1. Event Creation & Publishing
- Create events with:
  - Title, description, date/time, location (address/virtual link), category.
  - 1–3 ticket types (General/VIP, etc.) with price, sale dates, max quantity.  
- Save as draft or publish for public view.  
- *MVP Limitation:* Only a single cover image (no galleries).  

---

### 2. Event Discovery & Search
- Homepage with event listings (grid/list view).  
- Basic filters: category, date, location, price range.  
- "Featured/Trending" section (manual or auto-sorted).  
- Pagination (10–20 results per page).  
- *Extra:* Simple Google Maps integration with event pins.  

---

### 3. Registration & Booking
- Select event → ticket type → quantity.  
- Fill basic form (name, email, phone).  
- Payment via Stripe/Razorpay (cards, UPI).  
- Generate *unique booking ID* on success.  
- *MVP Limitation:* No guest checkout (account required).  

---

### 4. Ticket Delivery
- Auto-generate tickets with QR/barcode.  
- Delivery via *Email (PDF)*   
- Attendee dashboard → Download ticket anytime.  

---

### 5. Notifications & Reminders
- Booking confirmation via email/WhatsApp.  
- Event reminders (24h & 1h before).  
- Basic push/SMS integration (Firebase/Twilio).  

---

### 6. Organizer Dashboard
- Manage owned events & ticket inventory.  
- Real-time sales stats (bookings, revenue).  
- Export attendee list (CSV).  
- Role-based access (Admin vs Event Manager).  

---

### 7. Attendee Dashboard
- *My Tickets* → View upcoming/past bookings.  
- Track booking history.  
- *Extra:* Refund requests → Organizer approves manually.  

---

### 8. Discounts & Promotions
- Promo codes (fixed/percentage discount).  
- Early bird pricing (based on dates).  
- Group offers (e.g., “Buy X, Get Y Free”).  
- Simple referral rewards (unique link-based).  

---

### 9. Event Check-In System
- QR/barcode scanning (web/mobile camera).  
- Real-time validation → Prevent duplicate entries.  
- Dashboard → Track check-in count.  

---

### 10. Analytics & Reports
- Organizer view → Tickets sold, revenue, demographics.  
- Export as PDF/CSV.  
- *MVP Limitation:* Basic queries only.  

---

## 🌟 Additional Features in MVP (Lightweight Integrations)
- *Social Sharing:* Share events via WhatsApp, Instagram, X, Facebook.  
- *Live Streaming Links:* Add YouTube/Zoom embed (no native streaming server).  
- *Refunds:* Basic manual workflow (partial/full refund).  

---

## 🛠 Tech Stack
- *Frontend:* HTML CSS JS (responsive web app).  
- *Backend:* Flask Python
- *Database:* Mysql
- *Payments:* Stripe / Razorpay / UPI / Wallet 
- *Auth:* Email/OTP 
- *Notifications:* Email(FOR TICKET BOOKED AND OTP)

---

## ✅ MVP Flow
1. Organizer → Creates & publishes event.  
2. Attendee → Discovers event → Books ticket → Pays online.  
3. System → Generates booking ID & QR ticket → Sends via email/WhatsApp.  
4. Attendee → Views tickets in dashboard & gets reminders.  
5. Organizer → Tracks sales, check-ins, and downloads reports.  

---

## 📅 VIDEO LINK

https://drive.google.com/file/d/1VDnVjo20QNJD3fp1mEOxboydZGixqyjS/view?usp=sharing

---

💡 EventHive MVP focuses on simplicity + usability → so that organizers can host events and attendees can experience a smooth booking journey without unnecessary overhead.
