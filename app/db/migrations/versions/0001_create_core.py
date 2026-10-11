import sqlalchemy as sa
from alembic import op

revision = '0001_create_core'
down_revision = None
branch_labels = None
depends_on = None


def _ts(name):
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)


def upgrade():
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        _ts('created_at'),
        _ts('updated_at'),
    )

    op.create_table(
        'skus',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64)),
        _ts('created_at'),
        _ts('updated_at'),
    )

    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku_id', sa.Integer(), sa.ForeignKey('skus.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False),
        _ts('created_at'),
    )
    op.create_index('ix_sales_store_id', 'sales', ['store_id'])
    op.create_index('ix_sales_sku_id', 'sales', ['sku_id'])

    op.create_table(
        'forecasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku_id', sa.Integer(), sa.ForeignKey('skus.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=32), nullable=False, server_default='ma'),
        _ts('created_at'),
    )
    op.create_index('ix_forecasts_store_id', 'forecasts', ['store_id'])
    op.create_index('ix_forecasts_sku_id', 'forecasts', ['sku_id'])

    op.create_table(
        'staffing_plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('store_id', sa.Integer(), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('staff_required', sa.Integer(), nullable=False),
        sa.Column('min_staff', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_staff', sa.Integer(), nullable=False, server_default='20'),
        _ts('created_at'),
    )
    op.create_index('ix_staffing_plans_store_id', 'staffing_plans', ['store_id'])


def downgrade():
    op.drop_table('staffing_plans')
    op.drop_table('forecasts')
    op.drop_table('sales')
    op.drop_table('skus')
    op.drop_table('stores')
