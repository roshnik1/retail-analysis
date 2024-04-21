import csv
import math
from dash import Dash, html, dcc, dash_table
import dash
from dash.dependencies import State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from sqlalchemy import ForeignKey, Table, create_engine, MetaData
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import warnings
import os
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
import configparser
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import pandas as pd
from sqlalchemy import delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

username = 'roshnik'
password = 'Password123#'
database = 'retail-analysis'
hostname = 'retail-analysis-cloud.mysql.database.azure.com'
root_ca = '/Users/khatr/OneDrive/Documents/Cloud-Computing-Final-Project/DigiCertGlobalRootCA.crt.pem'

db_uri = f"mysql+pymysql://{username}:{password}@{hostname}/{database}"

engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{hostname}/{database}",
    connect_args={
        "ssl": {
            "ssl_ca": root_ca
        }
    },
    echo=True
)

db = SQLAlchemy()
config = configparser.ConfigParser()
conn = engine.connect()

print(engine)

Base = declarative_base()

class Household(Base):
    __tablename__ = 'household'

    hshd_num = Column(String(50), primary_key=True)
    l = Column(String(50))
    age_range = Column(String(50))
    marital = Column(String(50))
    income_range = Column(String(50))
    homeowner = Column(String(50))
    hshd_composition = Column(String(50))
    hh_size = Column(String(50))
    children = Column(String(50))
    transact = relationship('Transactions')

class Product(Base):
    __tablename__ = 'product'

    product_num = Column(String(50), primary_key=True)
    department = Column(String(50))
    commodity = Column(String(50))
    brand_ty = Column(String(50))
    natural_organic_flag = Column(String(50))
    transact = relationship('Transactions')

class Transactions(Base):
    __tablename__ = 'transaction'

    index = Column(String(50), primary_key=True)
    basket_num = Column(String(50))
    hshd_num = Column(String(50), ForeignKey('household.hshd_num'))
    purchase_ = Column(String(50))
    product_num = Column(String(50), ForeignKey('product.product_num'))
    spend = Column(String(50))
    units = Column(String(50))
    store_r = Column(String(50))
    week_num = Column(String(50))
    year = Column(String(50)) 

df = pd.read_csv('data/400_transactions.csv')
df = df.reset_index(drop=False)
transactions_df = df.rename(str.strip, axis='columns')

print (transactions_df.columns)

for column in transactions_df.columns:
    transactions_df[column] = transactions_df[column].astype(str)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# # Transactions.__table__.drop(engine)

for index, row in transactions_df.iterrows():
    # print(row["HSHD_NUM"], row["L"])

    trans = Transactions(index=row["index"].strip() if row["index"] is not None else "", 
                       basket_num=row["BASKET_NUM"].strip() if row["BASKET_NUM"] is not None else "",
                       hshd_num=row["HSHD_NUM"].strip() if row["HSHD_NUM"] is not None else "",
                       purchase_=row["PURCHASE_"].strip() if row["PURCHASE_"] is not None else "",
                       product_num=row["PRODUCT_NUM"].strip() if row["PRODUCT_NUM"] is not None else "",
                       spend=row["SPEND"].strip() if row["SPEND"] is not None else "",
                       units=row["UNITS"].strip() if row["UNITS"] is not None else "",
                       store_r=row["STORE_R"].strip() if row["STORE_R"] is not None else "",
                       week_num=row["WEEK_NUM"].strip() if row["WEEK_NUM"] is not None else "",
                       year=row["YEAR"].strip() if row["YEAR"] is not None else ""
                       )
    session.add(trans)
    session.commit()

# create a metadata object and load the table metadata
metadata = MetaData()
table = Table('transactions', metadata, autoload=True, autoload_with=engine)

# select all rows from the table
query = table.select()

# execute the query and fetch the results
result = conn.execute(query).fetchall()

print(len(result))

