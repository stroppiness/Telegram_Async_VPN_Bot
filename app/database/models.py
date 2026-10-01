from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(primary_key=True)
    telegram_id = fields.CharField(unique=True, max_length=255)
    username = fields.CharField(max_length=255)

    class Meta:
        table = "users"


class VPNKeys(Model):
    key_text = fields.TextField()
    user_id = fields.ForeignKeyField(
        'models.User',
        to_field='telegram_id',
        related_name='keys',
        on_delete=fields.CASCADE,
    )
    protocol = fields.CharField(unique=False, max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "vpn_keys"
