from django.db import migrations

def create_or_update_superusers(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Ensure kashii superuser exists
    user_kashii, created = User.objects.get_or_create(
        username='kashii',
        defaults={
            'email': 'kashichavan7777@gmail.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    user_kashii.is_staff = True
    user_kashii.is_superuser = True
    user_kashii.is_active = True
    user_kashii.save()

    # Ensure kashichavan7777 superuser exists
    user_kashichavan, created = User.objects.get_or_create(
        username='kashichavan7777',
        defaults={
            'email': 'kashichavan7777@gmail.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    user_kashichavan.is_staff = True
    user_kashichavan.is_superuser = True
    user_kashichavan.is_active = True
    user_kashichavan.save()

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0013_rename_req_sv_time_bot_idx_requirement_timesta_1fc0a4_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(create_or_update_superusers, backwards),
    ]
