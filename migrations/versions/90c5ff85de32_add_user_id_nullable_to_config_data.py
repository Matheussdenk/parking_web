from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '90c5ff85de32'
down_revision = '3e9c160cece6'
branch_labels = None
depends_on = None

def upgrade():
    # config_data: só cria foreign key, pois a coluna já deve existir e ser nullable
    with op.batch_alter_table('config_data', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # entry: adiciona coluna nullable
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
    
    # atualiza registros existentes com user_id = 1 (mude para o id do usuário que quiser)
    op.execute('UPDATE entry SET user_id = 1 WHERE user_id IS NULL')

    # altera para NOT NULL e cria foreign key
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # exit: mesma coisa
    with op.batch_alter_table('exit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
    
    op.execute('UPDATE exit SET user_id = 1 WHERE user_id IS NULL')

    with op.batch_alter_table('exit', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # vehicle_type: adiciona coluna nullable, ajusta tipo e remove constraint, atualiza dados, altera coluna e cria foreign key
    with op.batch_alter_table('vehicle_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.alter_column('type',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.drop_constraint('vehicle_type_type_key', type_='unique')

    op.execute('UPDATE vehicle_type SET user_id = 1 WHERE user_id IS NULL')

    with op.batch_alter_table('vehicle_type', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])


def downgrade():
    # reversão simplificada
    with op.batch_alter_table('vehicle_type', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('user_id', nullable=True)
        batch_op.create_unique_constraint('vehicle_type_type_key', ['type'])
        batch_op.drop_column('user_id')

    with op.batch_alter_table('exit', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('user_id', nullable=True)
        batch_op.drop_column('user_id')

    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('user_id', nullable=True)
        batch_op.drop_column('user_id')

    with op.batch_alter_table('config_data', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
