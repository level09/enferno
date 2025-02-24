#!/bin/bash
set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Find latest Python 3 version
PYTHON_CMD=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}Error: No Python 3.x installation found${NC}"
    exit 1
fi

echo -e "${GREEN}Using Python: $($PYTHON_CMD --version)${NC}"

# Create and activate virtual environment
if [ -d "env" ]; then
    read -p "Virtual environment 'env' already exists. Recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf env
    else
        echo -e "${RED}Aborting setup${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Creating virtual environment...${NC}"
$PYTHON_CMD -m venv env

# Activate virtual environment
source env/bin/activate

# Install requirements
echo -e "${GREEN}Installing requirements...${NC}"
pip install -r requirements.txt

# Check for required commands
for cmd in tr openssl awk; do
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

# Check if .env-sample exists
if [ ! -f .env-sample ]; then
    echo -e "${RED}Error: .env-sample file not found${NC}"
    exit 1
fi

# Check if .env already exists
if [ -f .env ]; then
    read -p "A .env file already exists. Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    # Backup existing .env
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    if ! cp .env "$BACKUP_FILE"; then
        echo -e "${RED}Error: Failed to create backup file${NC}"
        exit 1
    fi
    echo -e "${GREEN}Created backup of existing .env at $BACKUP_FILE${NC}"
fi

# Copy the sample file
if ! cp .env-sample .env; then
    echo -e "${RED}Error: Failed to copy .env-sample to .env${NC}"
    exit 1
fi

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

# Process the .env file
if ! awk -v sk="$SECRET_KEY" -v ts1="$TOTP_SECRET1" -v ts2="$TOTP_SECRET2" -v ps="$PASSWORD_SALT" '
{
    if ($0 ~ /^SECRET_KEY=/) {
        print "SECRET_KEY=\"" sk "\""
    }
    else if ($0 ~ /^SECURITY_TOTP_SECRETS=/) {
        print "SECURITY_TOTP_SECRETS=\"" ts1 "," ts2 "\""
    }
    else if ($0 ~ /^SECURITY_PASSWORD_SALT=/) {
        print "SECURITY_PASSWORD_SALT=\"" ps "\""
    }
    else if ($0 ~ /^SQLALCHEMY_DATABASE_URI=/) {
        print "SQLALCHEMY_DATABASE_URI=sqlite:///enferno.sqlite3"
        print "# PostgreSQL alternative:"
        print "# SQLALCHEMY_DATABASE_URI=postgresql://postgres:pass@localhost/dbname"
    }
    else {
        print $0
    }
}' .env > .env.new; then
    echo -e "${RED}Error: Failed to process .env file${NC}"
    exit 1
fi

if ! mv .env.new .env; then
    echo -e "${RED}Error: Failed to save .env file${NC}"
    rm -f .env.new
    exit 1
fi

# Verify the file was created
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file was not created${NC}"
    exit 1
fi

echo -e "${GREEN}Successfully generated .env file with secure keys${NC}"
echo -e "${GREEN}Generated secure values for: SECRET_KEY, SECURITY_TOTP_SECRETS, SECURITY_PASSWORD_SALT${NC}"
echo -e "${GREEN}SQLite database configured at: enferno.sqlite3${NC}"
echo
echo -e "${GREEN}Next steps:${NC}"
echo -e "1. Update the remaining values in your .env file (mail settings, redis, etc.)"
echo -e "2. Run ${GREEN}flask create-db${NC} to initialize the database"
echo -e "3. Run ${GREEN}flask install${NC} to create the first admin user" 