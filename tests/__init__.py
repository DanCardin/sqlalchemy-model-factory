from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker


def get_session(Base, *, session=None):
    if session is None:
        engine = create_engine("sqlite:///")
        Session = sessionmaker(engine)
        session = Session()

    Base.metadata.create_all(session.connection())
    return session
