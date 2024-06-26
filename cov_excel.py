import pandas as pd
import json
lib_=json.load(open("lib/db.json",encoding="utf-8"))["books"]
lib_.pop("btemplate")
codes_books=list(map(lambda x: int(x.replace("b","")),lib_.keys()))
book_names=[]
author_name=[]
subjects_list=[]
catogeries_list=[]
for i in codes_books:
    book_names.append(lib_[f"b{i}"]["name"])
    author_name.append(lib_[f"b{i}"]["author"])
    subjects_list.append(",".join(lib_[f"b{i}"]["subjects"]))
    catogeries_list.append(",".join(lib_[f"b{i}"]["categories"]))

dta={
    "Book Code":codes_books,
    "Title":book_names,
    "author":author_name,
    "subjects":subjects_list,
    "catogeries":catogeries_list
}
pd.DataFrame(dta).to_excel("sup.xlsx",index=False)

