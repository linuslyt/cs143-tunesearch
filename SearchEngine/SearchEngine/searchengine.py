#!/usr/bin/python3

from flask import Flask, render_template, request

import search

application = app = Flask(__name__)
app.debug = True

total_rows = 0
total_offset = 0

@app.route('/search', methods=["GET"])
def dosearch():
    global total_offset
    global total_rows
    print(request.args)

    query = request.args['query']
    qtype = request.args['query_type']
    temp_repeat = request.args.get('repeat_last_query')
    if temp_repeat is None:
        repeat = 0
    else:
        repeat = temp_repeat
    
    offset = request.args.get('offset')
    if offset is None:
        print("RESET")
        total_offset = 0
    elif str(offset) == "+":
        print("NEXT")
        total_offset += 20
    elif str(offset) == "-":
        print("PREV")
        total_offset -= 20

    print(total_offset)      

    search_results, temp_total_rows = search.search(query, qtype, total_offset, repeat, total_rows)
        
    if repeat == "0":
        total_rows = temp_total_rows

    return render_template('results.html',
            query=query,
            query_type=qtype,
            results=len(search_results),
            search_results=search_results,
            page_offset=total_offset,
            total_rows=total_rows,
            repeat_last_query=repeat)

@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        pass
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
