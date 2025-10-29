# 🧠 AI Nexus

**AI Nexus** is a Flask-based web application that connects **students, clubs, and colleges**.  
It allows admin to manage **clubs, events, announcements, and members** all in one place.  
The project includes both a **web interface** and **REST API endpoints** for integration.

---

## 🚀 Features

- **Dashboard**: Overview of key statistics and recent activities
- **Club Management**: Create, view, edit, and delete clubs
- **Event Management**: Organize and track events with participant management
- **Member Management**: Handle member registrations and club affiliations
- **Coordinator Management**: Assign and manage club coordinators
- **College Management**: Maintain college information 
- **Announcement System**: Post and manage announcements
- **Search & Filter**: Advanced search and filtering capabilities
- **Pagination**: Efficient data handling with pagination


---

## 🛠️ Tech Stack

- **Backend:** Python (Flask Framework)  
- **Database:**  MySQL (via SQLAlchemy ORM)  
- **Frontend:** HTML, CSS, JavaScript (Flask Templates)  
- **Tools:** PyCharm / VS Code, GitHub Desktop, Postman  

---

## ⚙️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

1. **Clone the repository**
   ```bash
   git clone https://github.com/vinnietp/AI_NEXUS
   cd AI_NEXUS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the environment**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
5. **Configure the application**
   - Update `app/config.py` with your database settings and other configurations

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open in your browser:**  
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔗 Example API Endpoints

| **Method** | **Endpoint** | **Description** |
|-------------|--------------|-----------------|
| `GET` | `/api/clubs` | Get all clubs |
| `POST` | `/api/clubs` | Create a new club |
| `PUT` | `/api/clubs/<id>` | Update club details |
| `DELETE` | `/api/clubs/<id>` | Soft delete a club |
| `GET` | `/api/events` | List all events |
| `GET` | `/api/announcements` | Get announcements list |

---

## 📁 Project Structure

```
AI_NEXUS/
│
├── app/
│   ├── models.py        # Database models
│   ├── routes.py        # Flask routes (HTML pages)
│   ├── api.py           # REST API endpoints
│   ├── utils.py         # Helper functions
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, uploads
│
├── requirements.txt
└── README.md
```
## Usage

### Dashboard
- View key statistics (total clubs, events, members, etc.)
- Access recent activities and upcoming events
- Quick navigation to different sections

### Managing Entities

#### Clubs
- View all clubs in a tabular format
- Add new clubs with details
- Edit existing club information
- Delete clubs (with confirmation)
- Search and filter clubs

#### Events
- Create and manage events
- Track event participants
- Set event dates and descriptions
- View event status (upcoming, completed)

#### Members
- Register new members
- Assign members to clubs
- Track member status and join dates
- Manage member information

#### Coordinators
- Assign coordinators to clubs
- Manage coordinator contact information
- Track coordinator departments

#### Colleges
- Maintain college information
- Track college affiliations
- Manage college contacts

#### Announcements
- Post announcements
- Set announcement visibility
- Track announcement status

## Future Enhancements
- User authentication and authorization
- Role-based access control
- Email notifications
- Unit and integration tests


