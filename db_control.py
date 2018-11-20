from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.sql import select

Base = declarative_base()

engine = create_engine('sqlite:///app.db', echo=True)
metadata = MetaData()
print(metadata)

goal = Table('goal', metadata, autoload=True, autoload_with=engine)
substitution = Table('substitution', metadata, autoload=True, autoload_with=engine)
card = Table('card', metadata, autoload=True, autoload_with=engine)
penalty_missed = Table('penalty_missed', metadata, autoload=True, autoload_with=engine)


with engine.connect() as conn:
    conn.execute(card.delete())
    # query = select([goal])
    # for row in conn.execute(query):
    #     print(row)