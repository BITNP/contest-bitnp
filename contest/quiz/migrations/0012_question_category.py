from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0011_alter_answer_choice_alter_draftanswer_response_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="category",
            field=models.CharField(
                choices=[("R", "单项选择"), ("B", "判断")],
                default="R",
                max_length=1,
                verbose_name="类型",
            ),
            preserve_default=False,
        ),
    ]
