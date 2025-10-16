import os

class Config:
    SECRET_KEY = os.environ.get("AI_NEXUS_SECRET_KEY", "dev-secret-for-local")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "AI_NEXUS_DATABASE_URI",
        "mysql+pymysql://root:sreelakam@localhost/ai_nexus_club"
    )

