"""
Data migration to clean up duplicate email addresses before adding unique constraint
"""
from django.db import migrations


def remove_duplicate_emails(apps, schema_editor):
    """Remove duplicate users, keeping the most recent one for each email"""
    User = apps.get_model('accounts', 'User')
    
    # Find emails that appear more than once
    from django.db.models import Count
    duplicate_emails = (
        User.objects.values('email')
        .annotate(count=Count('email'))
        .filter(count__gt=1)
        .values_list('email', flat=True)
    )
    
    for email in duplicate_emails:
        # Get all users with this email, ordered by date_joined (oldest first)
        users = list(User.objects.filter(email=email).order_by('date_joined'))
        
        # Keep the most recent user (last in the list), delete the rest
        if len(users) > 1:
            users_to_delete = users[:-1]  # All except the last one
            
            print(f"Cleaning up email: {email}")
            for user in users_to_delete:
                print(f"  Deleting user: {user.username} (ID: {user.id}, joined: {user.date_joined})")
                user.delete()
            
            # Keep the most recent user
            kept_user = users[-1]
            print(f"  Keeping user: {kept_user.username} (ID: {kept_user.id}, joined: {kept_user.date_joined})")


def reverse_migration(apps, schema_editor):
    """This migration cannot be reversed as we can't recreate deleted users"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_alter_user_profile_picture'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_emails, reverse_migration),
    ]