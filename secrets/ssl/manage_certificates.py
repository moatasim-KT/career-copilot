#!/usr/bin/env python3
"""
SSL Certificate Management Script
Manages SSL certificates for different environments
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse


class SSLCertificateManager:
    """Manage SSL certificates."""
    
    def __init__(self):
        self.ssl_dir = Path(__file__).parent
        
    def generate_certificate(self, environment: str, domain: str = None):
        """Generate SSL certificate for environment."""
        env_dir = self.ssl_dir / environment
        env_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = env_dir / "cert.conf"
        cert_file = env_dir / "certificate.crt"
        key_file = env_dir / "private.key"
        
        # Copy template and customize if domain provided
        template_file = env_dir / "cert.conf.template"
        if template_file.exists():
            with open(template_file, 'r') as f:
                config_content = f.read()
                
            if domain and environment != "development":
                config_content = config_content.replace("your-domain.com", domain)
                
            with open(config_file, 'w') as f:
                f.write(config_content)
        else:
            print(f"Template not found: {template_file}")
            return False
            
        try:
            # Generate private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(key_file), "2048"
            ], check=True)
            
            # Generate certificate
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(key_file),
                "-out", str(cert_file), "-days", "365",
                "-config", str(config_file)
            ], check=True)
            
            # Set permissions
            key_file.chmod(0o600)
            cert_file.chmod(0o644)
            
            print(f"Certificate generated for {environment}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate certificate: {e}")
            return False
            
    def check_expiry(self, environment: str):
        """Check certificate expiry."""
        cert_file = self.ssl_dir / environment / "certificate.crt"
        
        if not cert_file.exists():
            print(f"Certificate not found: {cert_file}")
            return None
            
        try:
            result = subprocess.run([
                "openssl", "x509", "-in", str(cert_file),
                "-enddate", "-noout"
            ], capture_output=True, text=True, check=True)
            
            expiry_str = result.stdout.strip().replace("notAfter=", "")
            expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
            
            days_until_expiry = (expiry_date - datetime.now()).days
            
            print(f"Certificate for {environment} expires in {days_until_expiry} days")
            
            if days_until_expiry < 30:
                print("⚠️  Certificate expires soon!")
                
            return days_until_expiry
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to check expiry: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="SSL Certificate Manager")
    parser.add_argument("command", choices=["generate", "check", "renew"])
    parser.add_argument("environment", choices=["development", "staging", "production"])
    parser.add_argument("--domain", help="Domain name for certificate")
    
    args = parser.parse_args()
    
    manager = SSLCertificateManager()
    
    if args.command == "generate":
        manager.generate_certificate(args.environment, args.domain)
    elif args.command == "check":
        manager.check_expiry(args.environment)
    elif args.command == "renew":
        days_left = manager.check_expiry(args.environment)
        if days_left is not None and days_left < 30:
            manager.generate_certificate(args.environment, args.domain)
        else:
            print("Certificate does not need renewal yet")


if __name__ == "__main__":
    main()
