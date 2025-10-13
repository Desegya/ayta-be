#!/usr/bin/env python3
"""
Email viewer script - converts Django's file-based email backend files to viewable HTML
"""
import os
import re
import webbrowser
from pathlib import Path


def extract_html_from_email_file(email_file_path):
    """Extract HTML content from Django's email file format"""
    with open(email_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find HTML content between Content-Type: text/html and the next boundary
    html_pattern = r"Content-Type: text/html.*?\n\n(.*?)(?=\n--|\n\Z)"
    match = re.search(html_pattern, content, re.DOTALL)

    if match:
        return match.group(1)
    return None


def main():
    # Get the sent_emails directory
    current_dir = Path(__file__).parent
    emails_dir = current_dir / "sent_emails"

    if not emails_dir.exists():
        print("No sent_emails directory found. Run: python manage.py test_emails first")
        return

    # Create output directory for HTML files
    output_dir = current_dir / "email_previews"
    output_dir.mkdir(exist_ok=True)

    email_files = list(emails_dir.glob("*"))
    if not email_files:
        print("No email files found. Run: python manage.py test_emails first")
        return

    print(f"Found {len(email_files)} email files")

    for i, email_file in enumerate(sorted(email_files), 1):
        html_content = extract_html_from_email_file(email_file)

        if html_content:
            # Get subject from email file for naming
            with open(email_file, "r", encoding="utf-8") as f:
                email_content = f.read()

            subject_match = re.search(r"Subject: (.+)", email_content)
            subject = subject_match.group(1) if subject_match else f"Email_{i}"

            # Clean subject for filename
            safe_subject = re.sub(r"[^\w\s-]", "", subject).strip()
            safe_subject = re.sub(r"[-\s]+", "-", safe_subject)

            output_file = output_dir / f"{safe_subject}.html"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"✓ Converted: {safe_subject}.html")

            # Open the first file in browser
            if i == 1:
                webbrowser.open(f"file://{output_file.absolute()}")
        else:
            print(f"✗ No HTML content found in {email_file.name}")

    print(f"\nHTML files saved to: {output_dir}")
    print("Open these files in your browser to preview the emails!")


if __name__ == "__main__":
    main()
