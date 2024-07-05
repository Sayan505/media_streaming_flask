import os

from flask              import Flask
from flask_jwt_extended import JWTManager

from config.orm         import db

# import modules
from modules            import oauth


# init server
app = Flask(__name__)
app.url_map.strict_slashes   = False
app.config["JSON_SORT_KEYS"] = False
#app.config["SERVER_NAME"]    = f"{os.environ["BACKEND_URL"]}"
app.secret_key               = os.environ["FLASK_SECRET_KEY"]

# init PyJWT
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
JWTManager(app)


# init db
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}@db:5432/{os.environ["POSTGRES_DB"]}"
db.init_app(app)
with app.app_context():
    db.create_all()


# register module
module_blueprints = [
    oauth.blueprint
]
for mbp in module_blueprints:
    app.register_blueprint(mbp)

