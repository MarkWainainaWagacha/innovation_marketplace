
<<<<<<< HEAD
<<<<<<< HEAD
A full-stack role-based marketplace platform connecting student innovators with recruiters through structured project showcasing and secure evaluation workflows.

---

## 📌 Overview

Innovation Marketplace enables:

- 🎓 Students to submit and manage capstone projects  
- 🛠 Admins to review and approve submissions  
- 🧑‍💼 Recruiters to discover vetted talent  
- 🛍 Users to purchase official merchandise  
- 💳 Secure payments via M-Pesa (Safaricom Daraja Sandbox)
=======
Innovation Marketplace is a full-stack web platform built to bridge the gap between student innovation and industry recruitment.
=======
# Innovation Marketplace
>>>>>>> 7d41a71 (docs: enhance README with badges and project status section)

Full-stack application implementing a role-based project marketplace with recruiter discovery tools and integrated payment processing.

---

## System Design

The system follows a decoupled client-server architecture:

Client (Next.js) ↔ REST API (Flask) ↔ Database (PostgreSQL)

Authentication is handled via NextAuth (frontend) and JWT verification (backend).

---

## Modules

<<<<<<< HEAD
- Full-stack architecture (Next.js + Flask)
- JWT authentication with role-based control
- Admin approval workflow
- Recruiter analytics dashboard
- Secure M-Pesa STK Push integration
- PostgreSQL production-ready setup
>>>>>>> ea4bf2f (docs: enhance README with badges and project status section)

---

## 🌍 Live Deployment

<<<<<<< HEAD
- **Frontend:** _Add Vercel deployment link_  
- **Backend API:** _Add Render deployment link_  

---

## 🏗 System Architecture

### Frontend
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- ShadCN UI

### Backend
- Flask REST API
- SQLAlchemy ORM
- Flask-Migrate

### Database
- PostgreSQL (Production)
- SQLite (Development)

### Authentication
- NextAuth (Frontend)
- JWT (Backend)

### Payments
- M-Pesa Daraja API (Sandbox)

---

## 📂 Project Structure

```
innovation_marketplace/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│
├── server/
│   ├── models.py
│   ├── resources/
│   ├── migrations/
│
└── README.md
```

---

## ⚙️ Backend Setup

### Prerequisites
- Python 3.10+  
- PostgreSQL (optional for production)  

### Steps
```bash
cd server
pipenv install
pipenv shell
flask db upgrade
flask run
```

Create a `.env` file inside `/server`:
```
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
JWT_SECRET_KEY=
DATABASE_URL=
```

---

## ⚙️ Frontend Setup

### Prerequisites
- Node.js v18+  

### Steps
=======
Frontend → Next.js  
Backend → Flask REST API  
Database → PostgreSQL  
Auth → NextAuth + JWT  
Payments → M-Pesa Daraja Sandbox  
=======
### 1. Authentication Module
- User registration
- Login
- Role assignment
- JWT token verification

### 2. Project Module
- CRUD operations
- Approval flag
- Technology tagging
- Category classification

### 3. Recruiter Module
- Approved project access
- Technology filtering
- Search queries

### 4. Payment Module
- M-Pesa STK Push request
- Token generation
- Order creation
- Payment confirmation handling

---

## Database Models

- User
- Project
- Category
- Technology
- Order
- Merchandise
>>>>>>> 7d41a71 (docs: enhance README with badges and project status section)

---

## API Security

- JWT-based route protection
- Role-based authorization middleware
- Environment variable isolation
- CORS configuration

---

## Setup Instructions

### Backend

```bash
cd server
pipenv install
flask db upgrade
flask run
```

### Frontend

>>>>>>> ea4bf2f (docs: enhance README with badges and project status section)
```bash
cd frontend
npm install
npm run dev
```

<<<<<<< HEAD
Create a `.env.local` file inside `/frontend`:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXTAUTH_SECRET=
```

---

## 🔄 Approval Workflow

1. Student submits project  
2. Admin reviews submission  
3. Admin approves project  
4. Project becomes visible on:
   - Public `/projects`
   - Recruiter dashboard  
5. Unapproved projects remain hidden  

---

## 🔐 Security

- Role-based route protection  
- Server-side validation  
- Secure environment variables  
- Protected admin endpoints  
- Payment credential isolation  

---

## 👥 User Roles & Capabilities

### 🎓 Student
- Submit projects
- Upload thumbnails
- Add categories & technologies
- Edit their own projects

### 🛠 Admin
- Approve or reject submissions
- Manage users
- Manage merchandise
- Control project visibility

### 🧑‍💼 Recruiter
- Access recruiter dashboard
- View approved projects only
- Filter by technology
- Search by student/team
- Evaluate tech stacks

---

## ✨ Core Features

### 🔐 Authentication & Authorization
- Role-based access control
- Protected routes
- Server-side session validation
- Secure JWT handling

### 📁 Project Management
- CRUD functionality
- Admin approval workflow
- Thumbnail image uploads
- Category & tech tagging
- Public visibility control

### 🔎 Advanced Filtering
- Search by title, description, author
- Filter by category
- Sort by:
  - Newest
  - Most viewed
  - Highest rated

### 📊 Recruiter Dashboard
- Approved projects only
- Displays:
  - Total projects
  - Unique students
  - Technologies used
- Live filtering

### 🛍 Merchandise Store
- Cart system
- Checkout process
- Order tracking
- Payment verification

### 💳 M-Pesa Integration
- STK Push (Sandbox)
- Token generation
- Secure credential management
- Order creation after payment confirmation

---

## 👨‍💻 Contributors

- Joshua Imbusi — Frontend & Integration  
- Ruth Jelagat — Frontend & Integration  
- Castro Kimaru — Frontend & Integration  
- Grace Odongo — Backend  
- Mark Wagacha — Backend  

---

## 🏫 Academic Attribution

This project was developed as part of the **Moringa Innovation Marketplace Project** at Moringa School.

---

## 📄 License

Developed for academic purposes.  
This is a Moringa Innovation Marketplace project.
=======
---

## Production Notes

- Use PostgreSQL
- Set secure JWT secret
- Configure environment variables
- Enable HTTPS
- Restrict CORS origins

---

## License

<<<<<<< HEAD
- Joshua Imbusi  
- Ruth Jelagat  
- Castro Kimaru  
- Grace Odongo  
- Mark Wagacha  

---

Academic project — Portfolio Ready.
>>>>>>> ea4bf2f (docs: enhance README with badges and project status section)
=======
Academic use only.
>>>>>>> 7d41a71 (docs: enhance README with badges and project status section)
