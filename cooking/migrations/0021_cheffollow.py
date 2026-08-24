from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cooking', '0020_alter_recipe_recipe_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChefFollow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('follower_email', models.EmailField(max_length=254)),
                ('followed_email', models.EmailField(max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('follower_email', 'followed_email')},
            },
        ),
    ]
