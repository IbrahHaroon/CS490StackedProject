# Schema Enforcement of User Ownership

This document defines how user ownership is enforced across the database and backend.  
It ensures that users can only access and modify data that belongs to them.

---

## 🧑‍💼 User-Owned Tables

### 👤 Profile
- **Owned by:** `Profile.userID`  
- **Rule:** Only the authenticated user can access or update their profile  
- **Enforcement:**  
  `Profile.userID = authenticatedUser.id`  
- **Reason:** Contains personal account information  

---

### 📄 Documents
- **Owned by:** `Documents.userID`  
- **Rule:** Only the authenticated user can access their documents  
- **Enforcement:**  
  `Documents.userID = authenticatedUser.id`  
- **Reason:** Documents are private user files  

---

### 💼 Jobs
- **Owned by:** `Jobs.userID`  
- **Rule:** Only the authenticated user can access or modify their job/application records  
- **Enforcement:**  
  `Jobs.userID = authenticatedUser.id`  
- **Reason:** Represents user-specific job/application activity  

---

### 🎓 Education
- **Owned by:** `Education.userID`  
- **Rule:** Only the authenticated user can access or modify their education records  
- **Enforcement:**  
  `Education.userID = authenticatedUser.id`  
- **Reason:** Contains personal education history  

---

## 🏢 Non User-Owned Tables

### 🏢 Company Info
- **Owned by:** Not user-owned  
- **Rule:** Access is controlled by role or public visibility  
- **Enforcement:**  
  Not enforced via `userID`; handled through application logic  
- **Reason:** Represents company data shared across users  

---

### 📌 Position
- **Owned by:** Not user-owned  
- **Rule:** Job listings are publicly accessible; modification may require authorization  
- **Enforcement:**  
  Not enforced via `userID`; controlled via public access or roles  
- **Reason:** Represents general job postings  

---

## 📌 Key Points

- Tables with a `userID` field are **user-owned** and must be validated against the authenticated user:
- Where 'table.userID = authenticated.userID
- - Tables without a `userID` field are **not user-owned** and should be controlled through:
- public visibility  
- role-based permissions  

---

## 🧠 Takeaway

Ownership is enforced at the backend level by combining:
- authentication (who the user is)
- database checks (what data they are allowed to access)

This ensures secure and isolated access to user-specific data. 
  
