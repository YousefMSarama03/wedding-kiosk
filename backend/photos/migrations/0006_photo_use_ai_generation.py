from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0005_photo_moderation_db_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="use_ai_generation",
            field=models.BooleanField(
                default=True,
                help_text="If False, guest capture is copied to generated/ (no AI).",
            ),
        ),
    ]
