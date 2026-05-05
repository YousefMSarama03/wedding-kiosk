# Ensures INSERTs that omit moderation columns still succeed (e.g. stale app code vs migrated DB).

from django.db import migrations


def set_photo_moderation_defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'ALTER TABLE photos_photo ALTER COLUMN is_approved SET DEFAULT true'
        )
        cursor.execute(
            'ALTER TABLE photos_photo ALTER COLUMN is_featured SET DEFAULT false'
        )
        cursor.execute(
            'ALTER TABLE photos_photo ALTER COLUMN is_hidden SET DEFAULT false'
        )


def drop_photo_moderation_defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for column in ("is_approved", "is_featured", "is_hidden"):
            cursor.execute(
                f"ALTER TABLE photos_photo ALTER COLUMN {column} DROP DEFAULT"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0004_alter_photo_paths"),
    ]

    operations = [
        migrations.RunPython(set_photo_moderation_defaults, drop_photo_moderation_defaults),
    ]
