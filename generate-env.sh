#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check for required commands
for cmd in tr sed openssl; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is required but not installed.${NC}"
        exit 1
    fi
done

# Function to generate secure random string
generate_secure_string() {
    local length=$1
    if command -v openssl &> /dev/null; then
        openssl rand -base64 $length | tr -dc 'A-Za-z0-9@#$%^&*' | head -c $length
    else
        LC_ALL=C tr -dc 'A-Za-z0-9@#$%^&*' < /dev/urandom | head -c $length
    fi
}

# Check if .env already exists
if [ -f .env ]; then
    read -p "A .env file already exists. Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    # Backup existing .env
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_FILE"
    echo -e "${GREEN}Created backup of existing .env at $BACKUP_FILE${NC}"
fi

# Copy the sample file
cp .env-sample .env

# Generate secure random values
SECRET_KEY=$(generate_secure_string 32)
TOTP_SECRET1=$(generate_secure_string 32)
TOTP_SECRET2=$(generate_secure_string 32)
PASSWORD_SALT=$(generate_secure_string 32)

# Validate generated values
if [ -z "$SECRET_KEY" ] || [ -z "$TOTP_SECRET1" ] || [ -z "$TOTP_SECRET2" ] || [ -z "$PASSWORD_SALT" ]; then
    echo -e "${RED}Error: Failed to generate secure values${NC}"
    exit 1
fi

# Replace the values in .env file
sed -i '' "s/SECRET_KEY=3nF3Rn@/SECRET_KEY=\"$SECRET_KEY\"/" .env
sed -i '' "s/SECURITY_TOTP_SECRETS=secret1,secret2/SECURITY_TOTP_SECRETS=\"$TOTP_SECRET1,$TOTP_SECRET2\"/" .env
sed -i '' "s/SECURITY_PASSWORD_SALT=3nF3Rn0/SECURITY_PASSWORD_SALT=\"$PASSWORD_SALT\"/" .env

echo -e "${GREEN}Successfully generated .env file with secure keys${NC}"
echo -e "${GREEN}Generated secure values for: SECRET_KEY, SECURITY_TOTP_SECRETS, SECURITY_PASSWORD_SALT${NC}"
echo -e "${GREEN}Please update the remaining configuration values in your .env file${NC}"
