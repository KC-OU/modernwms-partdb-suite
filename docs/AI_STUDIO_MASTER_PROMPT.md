# Google AI Studio Master Prompt: ModernWMS & PartDB Unified App

Copy and paste the prompt below into [Google AI Studio](https://aistudio.google.com) to generate a complete, fullstack web and mobile application based on this repository.

---

```markdown
You are a senior full-stack software engineer and warehouse systems architect.

I want you to design and build a modern, high-performance, unified Web and Mobile Application called **"ModernWMS & PartDB Unified Inventory Suite"** that unifies my component inventory system (PartDB) and warehouse management system (ModernWMS) into a single cohesive, lightning-fast application.

### Domain & System Context:
- **PartDB**: Stores engineering parts, LEGO elements, categories, lots, IPNs, manufacturer product numbers, and technical specifications in SQLite.
- **ModernWMS**: Manages warehouse logistics, SPUs, SKUs, inventory locations (Location: KCLEGO), stock receiving (ASN / Notice on Arrival tickets), picking, and roles (Admin 7354, Picker 10932, ViewOnly).
- **Existing Sync Engine**: Syncs parts 1:1, calculates consolidated stock totals, and exposes REST endpoints on port 8082 (`/api/status`, `/api/parts`, `/api/sync`, `/api/reset-password`, `/api/part-link`, `/metrics`).

### Key Features to Implement in the New App:
1. **Unified Dashboard & Search**:
   - Instant search across Part Name, SPU Code, Commodity Code, IPN, Category, and Barcode.
   - Real-time stock counts, category distributions, and sync status badges.
   - Quick action buttons: Quick Stock Add (+), ASN Receiving Drawer, Manual Link Overrides, and User Security Manager.

2. **Touch & Scanner-Optimized Receiving Station (ASN)**:
   - Barcode scanning support (hardware scanner keyboard wedge + camera video stream via ZXing/html5-qrcode).
   - On-screen touch keypad for fast numeric quantity input on mobile/tablets.
   - Automatic ASN ticket generation (`ASN{YYYYMMDDHHMMSS}`) with stock increment and printable receipt label.

3. **Unified User & Role Management**:
   - RBAC with Admin, Warehouse Operator/Picker, and View-Only roles.
   - One-click temporary password generator with forced first-login password reset.
   - Full audit trail logging for all inventory adjustments and security actions.

4. **Direct Dual-System Deep Linking**:
   - One-click direct links to PartDB Part details and ModernWMS Warehouse SKU views.
   - Editable link override modal with persistent storage.

5. **Recommended Tech Stack**:
   - **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Shadcn UI components, Zustand for state.
   - **Backend / API**: FastAPI (Python) or Next.js Server Actions with SQLite / SQLAlchemy / Drizzle ORM.
   - **Real-Time Layer**: WebSockets / Server-Sent Events (SSE) for instant inventory sync between warehouse terminals.
   - **Mobile / PWA**: Progressive Web App (PWA) with manifest, service worker for offline caching, and responsive tablet UI.

Please provide:
1. Complete Project Structure and file hierarchy.
2. Production-ready Backend API routes and database models.
3. Interactive, dark-mode Frontend UI components (Dashboard, Part Table, Receiving Station, Quick Add Overlay, and User Manager).
4. Docker Compose deployment configuration with hot-reloading and volume mounts.
```
