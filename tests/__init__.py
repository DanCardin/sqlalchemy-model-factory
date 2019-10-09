from sqlalchemy import Column, create_engine, ForeignKey, types
from sqlalchemy.orm.session import sessionmaker


def get_session(Base):
    engine = create_engine("sqlite:///")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    return Session()
