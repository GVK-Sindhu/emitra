#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Step 1: Installing python packages in production environment..."
pip install -r requirements.txt

echo "Step 2: Applying committed database migrations..."
python manage.py migrate --noinput

echo "Step 3: Collecting static files for WhiteNoise..."
python manage.py collectstatic --noinput --clear

echo "Step 4: Bootstrapping database seeding..."
python seed.py

echo "Deployment build completed successfully!"
