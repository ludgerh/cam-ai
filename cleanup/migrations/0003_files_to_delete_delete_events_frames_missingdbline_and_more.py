# Generated by Django 4.2.5 on 2024-07-18 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cleanup', '0002_rename_name_events_frames_missingdbline_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='files_to_delete',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.DeleteModel(
            name='events_frames_missingdbline',
        ),
        migrations.DeleteModel(
            name='events_frames_missingframe',
        ),
        migrations.RenameField(
            model_name='status_line',
            old_name='events_frames_missingevents',
            new_name='eframes_correct',
        ),
        migrations.AddField(
            model_name='status_line',
            name='eframes_missingdb',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='eframes_missingfiles',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='trainer_correct',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='trainer_missingdb',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='trainer_missingfiles',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='video_correct',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='video_missingdb',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='video_missingfiles',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status_line',
            name='video_temp',
            field=models.BigIntegerField(default=0),
        ),
    ]
