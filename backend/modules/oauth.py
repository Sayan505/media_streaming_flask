import os

from flask import current_app, url_for, redirect

from authlib.integrations.flask_client import OAuth
from flask_jwt_extended                import create_access_token

from config.orm        import db
from models.user_model import User

from config.logger     import log


from flask import Blueprint
blueprint = Blueprint("oauth_module", __name__)


oauth = OAuth(current_app)
oauth.register(
    name="google",
    server_metadata_url= "https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    client_kwargs={ "scope": "openid email profile"}
)


# oauth commence route
@blueprint.route("/api/login")
def login():
    redirect_uri = url_for("oauth_module.auth", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# oauth callback route
@blueprint.route("/api/auth")
def auth():
    token      = oauth.google.authorize_access_token()
    userinfo   = token["userinfo"]
    oauth_sub  = str(userinfo["sub"])
    oauth_name = str(userinfo["name"])

    jwt       = create_access_token(identity=oauth_sub)


    user_exists = bool(db.session.execute(db.select(User).filter_by(oauth_sub=oauth_sub)).first())
    if not user_exists:
        user = User()
        user.oauth_sub = oauth_sub
        user.displayname = oauth_name
        
        db.session.add(user)
        db.session.commit()

    return redirect(f"{os.environ["FRONTEND_URL"]}/?jwt="+jwt)

