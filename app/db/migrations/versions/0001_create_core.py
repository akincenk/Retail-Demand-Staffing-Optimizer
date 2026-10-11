from alembic import op
import sqlalchemy as sa

revision = '0001_create_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'skus',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku_id', sa.Integer(), sa.ForeignKey('skus.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'forecasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku_id', sa.Integer(), sa.ForeignKey('skus.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=32), nullable=False, server_default='ma'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'staffing_plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('staff_required', sa.Integer(), nullable=False),
        sa.Column('min_staff', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_staff', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

def downgrade():
    op.drop_table('staffing_plans')
    op.drop_table('forecasts')
    op.drop_table('sales')
    op.drop_table('skus')
    op.drop_table('stores')
