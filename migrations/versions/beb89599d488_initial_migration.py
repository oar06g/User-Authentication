"""Initial migration

Revision ID: beb89599d488
Revises: 
Create Date: 2025-11-25 21:32:27.195357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'beb89599d488'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user") as batch_op:
        batch_op.create_unique_constraint("uq_user_email", ["email"])
        batch_op.create_unique_constraint("uq_user_username", ["username"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_constraint("uq_user_email", type_="unique")
        batch_op.drop_constraint("uq_user_username", type_="unique")