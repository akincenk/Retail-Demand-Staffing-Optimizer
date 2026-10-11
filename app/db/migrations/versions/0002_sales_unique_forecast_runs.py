"""Unique (store, SKU, day) on sales; run_id on forecasts.

Existing duplicate sales rows are merged into one row whose units are their sum, which is how the
forecast already treated them. Existing forecasts get run_id 'legacy' (one run per store and SKU).
"""
import sqlalchemy as sa
from alembic import op

revision = '0002_sales_unique_forecast_runs'
down_revision = '0001_create_core'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE sales SET units = (
            SELECT SUM(s2.units) FROM sales s2
            WHERE s2.store_id = sales.store_id AND s2.sku_id = sales.sku_id AND s2.d = sales.d
        )
        WHERE id IN (SELECT MAX(id) FROM sales GROUP BY store_id, sku_id, d HAVING COUNT(*) > 1)
        """
    )
    op.execute("DELETE FROM sales WHERE id NOT IN (SELECT MAX(id) FROM sales GROUP BY store_id, sku_id, d)")
    op.create_unique_constraint('uq_sales_store_sku_day', 'sales', ['store_id', 'sku_id', 'd'])

    op.add_column('forecasts', sa.Column('run_id', sa.String(length=36), nullable=True))
    op.execute("UPDATE forecasts SET run_id = 'legacy'")
    op.alter_column('forecasts', 'run_id', nullable=False)
    op.create_index('ix_forecasts_run_id', 'forecasts', ['run_id'])


def downgrade():
    op.drop_index('ix_forecasts_run_id', table_name='forecasts')
    op.drop_column('forecasts', 'run_id')
    op.drop_constraint('uq_sales_store_sku_day', 'sales', type_='unique')
