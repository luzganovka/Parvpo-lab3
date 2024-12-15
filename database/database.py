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
from sqlalchemy.orm import scoped_session, sessionmaker

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
#       INITIALISE DB WITH USERS
#################################################################################
def DB_init(num):
    session = Session()
    for i in range (num):
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
    session.close()

#################################################################################
#       SELECT USER BY LOGIN
#################################################################################

def get_user_by_login(login):
    session = Session()  # Create new session for particular request
    try:
        stmt = select(User).where(User.login.in_([login]))
        return session.scalars(stmt).all()  # calling .all(), to create a list
    finally:
        session.close()

#################################################################################
#       SERVER PART
#################################################################################

from flask import Flask, request, jsonify
# import requests

app = Flask(__name__)

@app.route('/', methods=['GET'])
def handle_post():
    session = Session()
    print("DB:\tGot get request", flush=True)

    login = request.args.get('login')
    print(f"DB:\tGot login = '{login}'", flush=True)
    # pid = int(request.headers['pid'])
    found = get_user_by_login(login)

    print(f"DB:\tI've found:\t{found[0]}", flush=True)
    session.close()

    # DEV: this return is unsafe!
    # str_addresses = ''.join(str(x)+"," for x in found[0].addresses)
    return jsonify({"id": found[0].id, "password": found[0].password}), 200

#################################################################################
#       MAIN
#################################################################################

if __name__=='__main__':

    #################################################################################
    #       CREATE ENGINE AND INIT DB
    #################################################################################

    engine = create_engine("sqlite:///users.db", echo=False)   #DEV: echo=True for testing
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    print("DB:\tEngine created")

    DB_init(USERS_NUM)
    print("DB:\tDB inited")
    
    print("DB:\tStarting server...")
    app.run(debug=False, host="0.0.0.0", port=8080)

    # found = get_user_by_login("Hilda")
    # for user in found:
    #     print(f"MAIN:\t{user}")
    