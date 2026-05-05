from django.db import migrations, models
import photos.models


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0003_kiosk_settings_and_photo_moderation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="guest_image",
            field=models.ImageField(upload_to=photos.models.photo_guest_upload_to),
        ),
        migrations.AlterField(
            model_name="photo",
            name="generated_image",
            field=models.ImageField(blank=True, null=True, upload_to=photos.models.photo_generated_upload_to),
        ),
    ]
