# Generated by Django 4.1.2 on 2022-10-30 16:44

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [
        ("quiz", "0005_alter_draftanswer_choice"),
        ("quiz", "0006_draftresponse_deadline"),
        ("quiz", "0007_alter_draftresponse_student"),
    ]

    dependencies = [
        ("quiz", "0004_alter_answer_options_alter_choice_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="draftanswer",
            name="choice",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="quiz.choice",
            ),
        ),
        migrations.AddField(
            model_name="draftresponse",
            name="deadline",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="截止时刻"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="draftresponse",
            name="student",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="quiz.student"
            ),
        ),
    ]
