"""
Setup script - creates a .env file from .env.example if one doesn't
already exist. Run this once after cloning the project, before running
the tests.

Usage: python setup.py
"""
import shutil
import os

if os.path.exists(".env"):
    print(".env already exists - nothing to do.")
else:
    shutil.copy(".env.example", ".env")
    print(".env created from .env.example. You're ready to run the tests.")