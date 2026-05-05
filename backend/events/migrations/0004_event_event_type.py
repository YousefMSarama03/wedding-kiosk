from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_event_max_photos"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("wedding", "Wedding"),
                    ("palestinian_henna", "Palestinian Henna Party"),
                    ("graduation", "Graduation"),
                ],
                default="wedding",
                max_length=32,
            ),
        ),
    ]
