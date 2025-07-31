import secrets

# Generate a 256-bit (32-byte) hex secret key
jwt_secret = secrets.token_hex(32)
print(jwt_secret)
