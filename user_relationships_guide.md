# User Relationships — How Everything Is Tied to a User

---

## The User Table Is Just a Hub

The `user` table itself only stores two things:

```
user_id  |  email
---------|------------------
1        |  usera@demo.com
2        |  userb@demo.com
```

All the actual data lives in separate tables that each hold a `user_id` column pointing back to the user. This is the foreign key relationship.

---

## Two Types of Relationships

**One-to-One (`uselist=False`)** — a user has exactly one of these:

| Relationship | What it means |
|---|---|
| `credentials` | One password per user |
| `profile` | One profile per user |
| `career_preferences` | One set of preferences per user |

**One-to-Many (`list[...]`)** — a user can have multiple of these:

| Relationship | What it means |
|---|---|
| `educations` | Multiple degrees |
| `experiences` | Multiple jobs |
| `skills` | Multiple skills |
| `documents` | Multiple uploaded files |
| `applied_jobs` | Multiple tracked jobs |

---

## How the FK Actually Works in the Database

Every child table has a `user_id` column that references `user.user_id`:

```
skills table
skill_id | user_id | name       | category
---------|---------|------------|----------
1        | 1       | Python     | Languages
2        | 1       | React      | Frontend
3        | 2       | Java       | Languages
```

User 1 owns skills 1 and 2. User 2 owns skill 3. The data is physically stored in the `skills` table — not inside the user row.

---

## How SQLAlchemy Loads It

When you do `user.skills` in Python, SQLAlchemy automatically runs:

```sql
SELECT * FROM skills WHERE user_id = 1
```

You never write that query yourself — the `relationship()` declaration handles it. That's the whole point of the ORM.

See `backend/database/models/user.py` lines 28–39 for the full relationship declarations.
