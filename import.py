import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    lst =[]
    fp = open("movies.csv","r")
    data = fp.readlines()[1:]
    for x in data:
        lst.append(x.split(";"))
    for x in lst:
        db.execute("INSERT INTO movies (title,lowercase_title,year,runtime,imdbID,imdbRating) VALUES (:title,:lowercase_title,:year,:runtime,:imdbID,:imdbRating)",
                {"title":x[0],"lowercase_title":x[0].lower().replace(" ","").strip(),"year":int(x[1]),"runtime":int(x[2]),"imdbID":x[3],"imdbRating":float(x[4])})
    db.commit()

if __name__ == "__main__":
    main()

 