#Sources
#Sets environment variables for server before it is imported: https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files

import os
from cryptography.fernet import Fernet
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_CHARSET", "utf8mb4")
os.environ.setdefault("SECRET_KEY", "testkey")
os.environ.setdefault("TOTP_ENCRYPTION_KEY", Fernet.generate_key().decode())