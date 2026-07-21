"""create system user

Revision ID: f554869b272c
Revises: af955e6f5f81
Create Date: 2026-07-19 23:06:58.327030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f554869b272c'
down_revision: Union[str, Sequence[str], None] = 'af955e6f5f81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        INSERT INTO users 
            (tg_id, created_at, tg_chat_id, tg_username)
        VALUES
            (0, now(), 0, NULL),
            (1, now(), 13455, 'user1'),
            (2, now(), 245621, 'user2')
        ON CONFLICT (tg_id) DO NOTHING;
    """)


def downgrade():
    op.execute("""
        DELETE FROM users
        WHERE tg_id IN (0, 1, 2);
    """)