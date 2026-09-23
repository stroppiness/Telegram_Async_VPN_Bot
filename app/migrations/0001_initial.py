from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='User',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('telegram_id', fields.CharField(unique=True, max_length=255)),
                ('username', fields.CharField(max_length=255)),
                ('client_api_id', fields.CharField(null=True, max_length=255)),
            ],
            options={'table': 'users', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='VPNKeys',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('key_text', fields.TextField(unique=False)),
                ('user_id', fields.ForeignKeyField('models.User', source_field='user_id_id', db_constraint=True, to_field='telegram_id', related_name='keys', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'vpn_keys', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
