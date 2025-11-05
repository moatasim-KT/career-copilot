"""make_hashed_password_nullable

Revision ID: 3e72c1c42810
Revises: 00c13b2e1e65
Create Date: 2025-11-03 15:21:26.425626

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e72c1c42810"
down_revision: Union[str, Sequence[str], None] = "00c13b2e1e65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	# Make hashed_password nullable since authentication is disabled
	op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
	"""Downgrade schema."""
	# Make hashed_password required again
	op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=False)
