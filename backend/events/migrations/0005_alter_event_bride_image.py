from django.db import migrations, models
import events.models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_event_event_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="bride_image",
            field=models.ImageField(blank=True, null=True, upload_to=events.models.event_bride_upload_to),
        ),
    ]
