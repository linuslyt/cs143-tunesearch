#!/usr/bin/python3

import psycopg2
from psycopg2 import sql

import re
import string
import sys

_PUNCTUATION = frozenset(string.punctuation)

def _remove_punc(token):
    """Removes punctuation from start/end of token."""
    i = 0
    j = len(token) - 1
    idone = False
    jdone = False
    while i <= j and not (idone and jdone):
        if token[i] in _PUNCTUATION and not idone:
            i += 1
        else:
            idone = True
        if token[j] in _PUNCTUATION and not jdone:
            j -= 1
        else:
            jdone = True
    return "" if i > j else token[i:(j+1)]

def _get_tokens(query):
    rewritten_query = []
    tokens = re.split('[ \n\r]+', query)
    for token in tokens:
        lowered_token = token.lower()
        cleaned_token = _remove_punc(lowered_token)
        if cleaned_token:
            if "'" in cleaned_token:
                cleaned_token = cleaned_token.replace("'", "''")
            rewritten_query.append(cleaned_token)
    return rewritten_query


# query: search terms
# query_type: AND / OR
# page:
def search(query, query_type, total_offset, repeat, total_rows):
    
    rewritten_query = _get_tokens(query)
    num_rows = 0

    print("query: ", query)
    print("rewritten query: ", rewritten_query)
    print("repeat: ", repeat, "total_rows: ", total_rows, "total offset:", total_offset)

    try:
        conn = psycopg2.connect("dbname='searchengine' user='cs143' host='localhost' password='cs143'")
        print("Connected to database")
    except:
        print("ERROR: could not connect to TuneSearch database")

    try:
        cur = conn.cursor()
        num_tokens = len(rewritten_query)

        # print(query_tokens)
        if query_type == "or":
            if repeat == "0":
                print ("hi")
                try:
                    print("hi")
                    cur.execute("DROP MATERIALIZED VIEW IF EXISTS last_query")
                    conn.commit()
                except:
                    print("View could not be dropped")

                orq = sql.SQL("""   CREATE MATERIALIZED VIEW last_query AS
                                    SELECT song_name, artist_name, page_link, SUM(score) as rank FROM tfidf 
                                    INNER JOIN song ON tfidf.song_id = song.song_id 
                                    INNER JOIN artist ON song.artist_id = artist.artist_id 
                                    WHERE token IN ({})
                                    GROUP BY tfidf.song_id, song_name, artist_name, page_link 
                                    ORDER BY rank DESC   
                                    WITH DATA;
                              """
                             ).format(sql.SQL(', ').join(sql.Placeholder() * num_tokens))              


            try:
                print(orq.as_string(conn))
                cur.execute(orq, rewritten_query)
                conn.commit()
                num_rows = cur.rowcount
                print("total rows: ", num_rows)
            except:
                print("ERROR: could not set up OR materialized view")            

        elif query_type == "and":
            if repeat == "0":
                try:
                    cur.execute("DROP MATERIALIZED VIEW IF EXISTS last_query")
                except:
                    print("View could not be dropped")

                andq = sql.SQL("""  CREATE MATERIALIZED VIEW last_query AS
                                    SELECT song_name, artist_name, page_link, SUM(score) as rank FROM (
                                        SELECT R.song_id, R.score FROM (
                                            SELECT song_id, score FROM tfidf WHERE token IN ({}) 
                                            GROUP BY song_id, token ORDER BY song_id
                                        ) candidates 
                                        INNER JOIN tfidf R ON candidates.song_id = R.song_id WHERE R.token IN ({})
                                        GROUP BY R.song_id, R.token HAVING COUNT(candidates.song_id) = {}
                                    ) results 
                                    INNER JOIN song ON results.song_id = song.song_id
                                    INNER JOIN artist ON song.artist_id = artist.artist_id
                                    GROUP BY results.song_id, song_name, artist_name, page_link
                                    ORDER BY rank DESC
                                    WITH DATA   
                               """
                              ).format(sql.SQL(', ').join(sql.Placeholder() * num_tokens), 
                                       sql.SQL(', ').join(sql.Placeholder() * num_tokens), 
                                       sql.Placeholder())


            try:
                print(andq.as_string(conn))
                args = rewritten_query + rewritten_query + [str(num_tokens)]
                cur.execute(andq, args)    
                conn.commit()
                num_rows = cur.rowcount
                print("total rows: ", num_rows)
            except:
                print("ERROR: could not set up AND materialized view")
            
        q = sql.SQL("SELECT * FROM last_query LIMIT 20 OFFSET {}").format(sql.Placeholder())
        cur.execute(q, [total_offset])
        rows = cur.fetchall()
        conn.close()
        return rows, num_rows

    except:
        print("ERROR: could not fetch results from database")

    conn.close()
    return [], 0

if __name__ == "__main__":
    if len(sys.argv) > 2:
        result = search(' '.join(sys.argv[2:]), sys.argv[1].lower())
        print(result)
    else:
        print("USAGE: python3 search.py [or|and] term1 term2 ...")

