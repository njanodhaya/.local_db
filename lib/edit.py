import json
db_file=open("lib/db.json")
db=json.load(db_file)
db_file.close()
print(len(db["books"]))
# for i in db["books"]:
#     tmp_i=db["books"][i]["search_qry"]
#     for j in db["books"][i]["search_qry"].split(","):
#         if j in db["subjects"]:
#             tmp_i+=f',{db["subjects"][j]}'
#     db["books"][i]["search_qry"]=tmp_i
# db_file=open("lib/db.json","w")
# json.dump(db,db_file)
# db_file.close()
