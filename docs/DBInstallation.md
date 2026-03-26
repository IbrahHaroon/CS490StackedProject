# Installation Process:

## For Linux Ubuntu Users:
- For understanding purposes markdown uses # for headers so I will replace bash # comments by // C conventional comments
# Commands in Terminal (Bash):
- sudo apt update // Update your package lists
- sudo apt install postgresql postgresql-contrib // Installing PostgreSQL server and additional utilities related to it
- sudo systemctl status postgresql  // Verify the installation by checking the service status 
- sudo service postgresql start

For Windows Users(Graphical Installation):
Interactive Download
Follow Instructions on the link:
[postgresql download](https://www.postgresql.org/download)

For Mac Users(Graphical Installation):
Similar to Windows Installation
For more information follow instruction in the link:
[macosx installation](https://www.postgresql.org/download/macosx/)

For Mac Users(using Bash Command line)
Commands:
- brew install postgresql
- brew services start postgresql

Creating the Database (using Bash)
Step 1: Install PostgreSQL

Step 2:Open PostgreSQL
Commands:
- psql postgres
- CREATE DATABASE myapp_db;
- CREATE USER myuser WITH PASSWORD 'mypassword';
- GRANT ALL PRIVELEGES ON DATABASE myapp_db TO myuser;

Step 3:Setting Up Environment Variables
- Create a .env file inside the backend folder:
<img width="608" height="106" alt="image" src="https://github.com/user-attachments/assets/b79ba881-34fe-41f2-9edf-74a7eef12c6c" />
