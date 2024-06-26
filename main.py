from flask import Flask, render_template, request, jsonify, abort
import segno
import socket
import json
import hashlib
import datetime
import base64
import os
import random


app = Flask(__name__)
PORT = 5000


# Generate QR code dynamically
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_address = s.getsockname()[0]
s.close()


# Load library structure
with open("lib/library.json") as vlib:
    db_library = json.load(vlib)

# Load member list
members_db={}
with open("lib/members.json") as memreg:
    members_db = json.load(memreg)
members_uids=[]
for i in members_db["members"].keys():
    members_uids.append(members_db["members"][i]["uid"])
# Generate QR code
qr_url = f"http://{ip_address}:{PORT}/"
qr_filename = "./static/qr.png"
segno.make_qr(qr_url).save(qr_filename, scale=20)


# Generate authentication token
current_day = datetime.datetime.now().day
AUTH_TOKEN = base64.encodebytes(hashlib.sha1(
    f"{current_day}get salted lol".encode("utf-8")).digest()).decode("ascii").strip()


# Save token to a file (token.admin)
with open("token.admin", "w") as tockstore:
    tockstore.write(AUTH_TOKEN)


# Load or initialize database
DB_FILE = "./lib/db.json"
if not os.path.exists(DB_FILE):
    db = {"library": input("enter your library's name: "),
          "books": {"btemplate": {}}}
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)
else:
    with open(DB_FILE, "r") as f:
        db = json.load(f)


# Create searchable dictionary
searchable = {}
for i in db["books"]:
    searchable[db["books"][i]["search_qry"]] = i


@app.route("/", methods=["GET", "POST"])
def home_page():
    disp_list_collections = list(db["books"].keys())
    random.shuffle(disp_list_collections)
    if request.method == "GET":
        library_name = db["library"]
        disp_list_collections_ids = []
        book_lib = db["books"]
        if len(disp_list_collections) <= 200:
            disp_list_collections_ids = disp_list_collections
        else:
            disp_list_collections_ids = disp_list_collections[:200]
        return render_template("Index.html", library_name=library_name, book_lib=book_lib, book_disp=disp_list_collections_ids, cover_pic="cover_src", name="name", author="author", search_word="")
    else:
        library_name = db["library"]
        search_qry = request.form.get("search")
        disp_list_collections_ids = []
        book_lib = db["books"]
        for i in searchable.keys():
            if search_qry.replace(" ", "") in i:
                disp_list_collections_ids.append(searchable[i])
        return render_template("Index.html", library_name=library_name, book_lib=book_lib, book_disp=disp_list_collections_ids, cover_pic="cover_src", name="name", author="author", search_word=search_qry)


@app.route("/share", methods=["GET"])
def qrcode():
    return render_template("disp_qr.html", qr_image=qr_filename)


@app.route("/books", methods=["GET", "POST"])
def book_upload():
    if request.method == "POST":
        form_data = request.form
        auth_id = form_data.get("auth_id", "")

        if auth_id == "" or auth_id != AUTH_TOKEN:
            return jsonify({"error": "Authentication token was not given or is incorrect."}), 401

        code = form_data.get("code", "")
        book_name = form_data.get("book_name", "")
        author_name = form_data.get("author_name", "")

        if code == "":
            return jsonify({"error": "Error: Book code not given."}), 400
        if not code.isdecimal():
            return jsonify({"error": "Error: Book code can only contain numbers."}), 400
        if book_name == "":
            return jsonify({"error": "Error: Book name is necessary for registration."}), 400
        if author_name == "":
            return jsonify({"error": "Error: Author's name is required."}), 400

        picture = ""
        # Uncomment and handle picture upload if needed
        # pic_value = request.files.get("pic_cover")
        # if pic_value and pic_value.filename != "":
        # picture = f"b{code}.{pic_value.filename.split('.')[-1]}"
        # pic_value.save(f"./static/covers/{picture}")

        template_books = {
            "name": book_name,
            "author": author_name,
            "genres": form_data.getlist("genres"),
            "subjects": form_data.getlist("subjects"),
            "categories": form_data.getlist("categories"),
            "cover_src": picture if picture else "default.svg",
            "search_qry": str(f"{code},{book_name},{author_name},{','.join(form_data.getlist('genres') + form_data.getlist('categories') + form_data.getlist('subjects') + list(map(lambda x: x.strip(), form_data.get('keywords').lower().split(','))))}").lower().replace(" ", "")
        }

        db["books"][f"b{code}"] = template_books
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=4)

        return jsonify(template_books), 200

    else:
        return render_template("register_book.html", database=db)


@app.route("/shelves", methods=["GET", "POST"])
def book_shelf_upload():
    if request.method == "POST":
        form_data = request.form
        auth_id = form_data.get("auth_id", "")

        if auth_id == "" or auth_id != AUTH_TOKEN:
            return jsonify({"error": "Authentication token was not given or is incorrect."}), 401

        code = form_data.get("code", "")
        shelf = form_data.get("shelf", "")
        row = form_data.get("rack", "")

        if code == "":
            return jsonify({"error": "Error: Book code not given."}), 400
        if not code.isdecimal():
            return jsonify({"error": "Error: Book code can only contain numbers."}), 400
        if shelf not in db_library["shelves"]:
            return jsonify({"error": "Error: Select a valid shelf."}), 401
        if row not in db_library["shelves"][shelf]["racks"]:
            return jsonify({"error": f"Error: Select a valid rack. '{row}' not found in {list(db_library['shelves'][shelf]['racks'].keys())}"}), 402

        if f"b{code}" not in db_library["shelves"][shelf]["racks"][row]:
            db_library["shelves"][shelf]["racks"][row].append(f"b{code}")
        else:
            return "error book already in place"
        with open("lib/library.json", "w") as f:
            json.dump(db_library, f, indent=4)

        return jsonify({"message": "Book successfully added to the shelf."}), 200

    else:
        return render_template("register_book_shelf.html", database=db_library["shelves"])


@app.route("/book/<path:book_id>", methods=["GET", "POST"])
def book_page(book_id):
    if request.method == "GET":
        if book_id not in db["books"]:
            return "<h1>ERROR: 404</h1><br/><h2>BOOK ID ({}) NOT FOUND</h2>".format(book_id), 404
        return render_template("books.html", library_name=db["library"], book_name=db["books"][book_id]["name"], book_id=book_id, home_page=qr_url, book_lib=db["books"],db=db, cover_pic="cover_src", isavailable="")
    else:
        return "lol"

@app.route("/book/<path:book_id>/borrow")
def borrow(book_id ,methods=["GET","POST"]):
    if request.method=="GET":
        return render_template("borrow.html",library_name=db["library"],book_name=db["books"][book_id]["name"],book_id=book_id)
    else:
        return "lol"


def gen_user(og_uid_list:list,name:str,usr_type:int):
    id=""
    def genuid():
        uid=random.choice("abcdefghijkmnpqrstuvwxyz23456789")+random.choice("abcdefghijkmnpqrstuvwxyz23456789")
        if uid in og_uid_list:
            return genuid()
        else:
            return uid
    id=genuid()
    return { "books":[],"uid":id,"type":usr_type}



@app.route("/members", methods=["GET", "POST"])
def members_register():
    if request.method == "POST":
        form_data = request.form
        auth_id = form_data.get("auth_id", "")

        if not auth_id or auth_id != AUTH_TOKEN:
            return jsonify({"error": "Authentication token was not given or is incorrect."}), 401

        member = form_data.get("name", "")
        usr_type = 0 if form_data.get("membership_type", "") == "adults" else 1

        if not member:
            return jsonify({"error": "Error: name not given."}), 400

        if member in members_db["members"]:
            return jsonify({"error": "Error: member already exists."}), 409

        members_db["members"][member] = gen_user(members_uids, member, usr_type)

        with open("lib/members.json", "w") as f:
            json.dump(members_db, f, indent=4)

        return jsonify({"message": f"{member} successfully added with id: {members_db['members'][member]['uid']}"}), 201

    else:
        return render_template("people.html", database=db_library["shelves"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
