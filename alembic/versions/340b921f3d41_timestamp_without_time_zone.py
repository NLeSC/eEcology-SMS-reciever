"""Timestamp without time zone

Revision ID: 340b921f3d41
Revises:
Create Date: 2015-05-18 11:27:32.504448

"""

# revision identifiers, used by Alembic.
revision = '340b921f3d41'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('raw_message', 'sent_timestamp', schema='sms', type_=sa.DateTime(timezone=False))
    op.alter_column('message', 'date_time', schema='sms', type_=sa.DateTime(timezone=False))
    op.alter_column('position', 'date_time', schema='sms', type_=sa.DateTime(timezone=False))
    pass


def downgrade():
    op.alter_column('raw_message', 'sent_timestamp', schema='sms', type_=sa.DateTime(timezone=True))
    op.alter_column('message', 'date_time', schema='sms', type_=sa.DateTime(timezone=True))
    op.alter_column('position', 'date_time', schema='sms', type_=sa.DateTime(timezone=True))
    pass
