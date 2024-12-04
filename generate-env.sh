#!/bin/bash

# Check if .env already exists
if [ -f .env ]; then
    read -p "A .env file already exists. Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Copy the sample file
cp .env-sample .env

# Generate secure random values
SECRET_KEY=$(LC_ALL=C tr -dc 'A-Za-z0-9@#$%^&*' < /dev/urandom | head -c 32)
TOTP_SECRET1=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)
TOTP_SECRET2=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)
PASSWORD_SALT=$(LC_ALL=C tr -dc 'A-Za-z0-9@#$%^&*' < /dev/urandom | head -c 32)

# Replace the values in .env file
sed -i '' "s/SECRET_KEY=3nF3Rn@/SECRET_KEY=\"$SECRET_KEY\"/" .env
sed -i '' "s/SECURITY_TOTP_SECRETS=secret1,secret2/SECURITY_TOTP_SECRETS=\"$TOTP_SECRET1,$TOTP_SECRET2\"/" .env
sed -i '' "s/SECURITY_PASSWORD_SALT=3nF3Rn0/SECURITY_PASSWORD_SALT=\"$PASSWORD_SALT\"/" .env

echo "Successfully generated .env file with secure keys"
echo "Generated secure values for: SECRET_KEY, SECURITY_TOTP_SECRETS, SECURITY_PASSWORD_SALT"
echo "Please update the remaining configuration values in your .env file"
