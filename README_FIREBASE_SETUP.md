# 🔥 Firebase Authentication Setup Guide for SocietyPro

This guide explains how to configure Firebase Authentication for Google Sign-In across local development and production deployments (such as Vercel).

---

## 1. Create / Open your Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** (or select your existing project).
3. Name your project (e.g., `SocietyPro`) and complete project setup.

---

## 2. Enable Google Sign-In Provider

1. In the left sidebar of the Firebase Console, navigate to **Build** -> **Authentication**.
2. Click **Get Started** (if opening Authentication for the first time).
3. Under the **Sign-in method** tab, click **Google**.
4. Toggle the **Enable** switch to ON.
5. Set the **Project support email** (select your email).
6. Click **Save**.

---

## 3. Register a Web App & Copy Configuration

1. In Firebase Console, click the **Settings icon (⚙️)** in the top-left sidebar -> **Project settings**.
2. Under the **General** tab, scroll down to the **Your apps** section.
3. Click the **Web icon (`</>`)** to add a new web application.
4. Enter an App nickname (e.g. `SocietyPro Web`) and click **Register app**.
5. You will see your `firebaseConfig` object with properties similar to:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "societypro-xyz.firebaseapp.com",
     projectId: "societypro-xyz",
     storageBucket: "societypro-xyz.appspot.com",
     messagingSenderId: "123456789012",
     appId: "1:123456789012:web:abcdef123456",
     measurementId: "G-XXXXXXXXXX"
   };
   ```

---

## 4. Add Environment Variables

### A. Local Development (`backend/.env`)
Open `backend/.env` and update the Firebase variables with values from step 3:

```env
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=societypro-xyz.firebaseapp.com
FIREBASE_PROJECT_ID=societypro-xyz
FIREBASE_STORAGE_BUCKET=societypro-xyz.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456
FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

### B. Vercel Deployment (Production)
If you deploy to **Vercel**:
1. Go to your project on the [Vercel Dashboard](https://vercel.com).
2. Navigate to **Settings** -> **Environment Variables**.
3. Add the following environment variables (matching the values in your `.env`):
   - `FIREBASE_API_KEY`
   - `FIREBASE_AUTH_DOMAIN`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_STORAGE_BUCKET`
   - `FIREBASE_MESSAGING_SENDER_ID`
   - `FIREBASE_APP_ID`
   - `FIREBASE_MEASUREMENT_ID`
4. Redeploy your project (or push a new commit) for the variables to take effect.

---

## 5. Add Authorized Domains in Firebase

To allow Google sign-in to work on your live deployment:
1. In Firebase Console, go to **Authentication** -> **Settings** tab -> **Authorized domains**.
2. Click **Add domain**.
3. Add your Vercel deployment domain (e.g., `society-pro.vercel.app` or your custom domain).
4. `localhost` is authorized by default.

---

## 6. How Sign-In Works in SocietyPro

1. **Admin Sign-In (`/admin/login`)**:
   - Admin clicks **Sign in with Google**.
   - Firebase handles Google authentication in a secure popup.
   - The verified Firebase ID token is sent to `/admin/google_login`.
   - The backend validates the token and logs the admin into the dashboard if their email is registered as an admin.

2. **Resident Sign-In (`/user/login`)**:
   - Resident clicks **Sign in with Google**.
   - Firebase verifies the Google account.
   - The backend checks for a resident record matching that email and establishes a resident session.

3. **Admin Registration (`/admin/register`)**:
   - Admin clicks **Auto-fill with Google**.
   - Firebase populates their Name and Email automatically.
   - Admin enters the Society Name and password to register their society.
