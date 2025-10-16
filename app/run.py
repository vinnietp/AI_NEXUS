# run.py
import os
from flask import Flask
from config import Config
from models import db
from routes import register_routes
from api import api
# Initialize the Flask application and load configuration settings from the Config class
app = Flask(__name__)
app.config.from_object(Config)


# Configure upload directories and file size limits
app.config.setdefault("UPLOAD_FOLDER", os.path.join(app.static_folder, "uploads"))
app.config.setdefault("CLUB_UPLOAD_FOLDER",        os.path.join(app.config["UPLOAD_FOLDER"], "clubs"))
app.config.setdefault("EVENT_UPLOAD_FOLDER",       os.path.join(app.config["UPLOAD_FOLDER"], "events"))
app.config.setdefault("COORDINATOR_UPLOAD_FOLDER", os.path.join(app.config["UPLOAD_FOLDER"], "coordinators"))
app.config.setdefault("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)  # 5 MB

# Initialize database with the Flask app
db.init_app(app)

#register all application routes
register_routes(app)

app.register_blueprint(api)

if __name__ == "__main__":
    #creates an application context, allowing database operations
    with app.app_context():
        # make sure all upload dirs exist
        for key in ("UPLOAD_FOLDER", "CLUB_UPLOAD_FOLDER", "EVENT_UPLOAD_FOLDER", "COORDINATOR_UPLOAD_FOLDER"):
            os.makedirs(app.config[key], exist_ok=True)
        #db.drop_all()
        db.create_all()
        print("✅ Tables ready.")
    app.run(debug=True)
