import os
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"     # Symmetrical encryption


# Instantiates Argon2id with default secure parameters:
# Defaults are mem: 64MB, time cost: 3 iterations, parallelism: 4 threads
ph = PasswordHasher()


def hash_password(password):
    return ph.hash(password)


def verify_password(plain_pass, hashed_pass):
    try:
        return ph.verify(hashed_pass, plain_pass)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False
    
    
def create_access_token(data):
    to_encode = data.copy()     # Will probably contain 
    expire = datetime.now(timezone.utc) + timedelta(weeks=1)    # Expires after 1 week
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)   # Encode non-sensitive metadata that you want to inspect them in fastapi without accessing the db.