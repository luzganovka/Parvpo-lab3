from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import string
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

USERS_NUM = 10

#################################################################################
#       DECLARE THE DATABASE
#################################################################################

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id:         Mapped[int] = mapped_column(primary_key=True)
    login:      Mapped[str] = mapped_column(String(30))
    password:   Mapped[str]
    addresses:  Mapped[Optional[List["Address"]]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, login={self.login!r}, password={self.password!r})"

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")
    def __repr__(self) -> str:  #DEV: this func is NOT safe now!
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"

#################################################################################
#       CREATE ENGINE FOR DB
#################################################################################

engine = create_engine("sqlite://", echo=False) #DEV: echo=True for testing
Base.metadata.create_all(engine)

#################################################################################
#       INITIALISE DB WITH USERS
#################################################################################

with Session(engine) as session:
    for i in range (USERS_NUM):
        hilda = User(
            login       =                        str(''.join(random.choices(string.ascii_letters, k=5))),
            password    =                        str(''.join(random.choices(string.ascii_letters, k=7))),
            addresses   = [Address(email_address=str(''.join(random.choices(string.ascii_letters, k=9))),)],
        )
        session.add_all([hilda])
        session.commit()
    # DEV: Just for testing!
    hilda = User(
        login       = "Hilda",
        password    = "123",
        addresses   = [Address(email_address="hilda@addr")],
    )
    session.add_all([hilda])
    session.commit()

#################################################################################
#       SELECT USER BY LOGIN
#################################################################################

login = "Hilda"

with Session(engine) as session:

    stmt = select(User).where(User.login.in_(["Hilda"]))

    print("DB:  I've found:")
    for user in session.scalars(stmt):
        print(user)