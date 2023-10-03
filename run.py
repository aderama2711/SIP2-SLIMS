import mysql.connector
import datetime
import socket

HOST = "192.168.20.254"  # The server's hostname or IP address
PORT = 6001  # The port used by the server

library_name = "Coba_Aja"
language = "001"

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  port="3404",
  database="bulian"
)

def gettime():
    return datetime.datetime.now().strftime("%Y%m%d    %H%M%S")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            string = data.decode('utf-8')
            print(string)
            if not data:
                break

            resp = bytes("", "utf-8")

            # SC registration
            if string[0:2] == "99":
                resp = bytes("98YYYNNN500   003"+gettime()+"2.00AO"+library_name+"|BXNYYNYNNYNNYNNNNN"+"\r", 'utf-8')
            
            # item information
            if string[0:2] == "17":
                # get book ID
                item_id = string.split("AB")[1].split("|")[0]

                # get book information
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM item WHERE item_code='"+item_id+"'")
                myresult = mycursor.fetchall()

                if len(myresult) == 0:
                    resp = bytes("18000001"+gettime()+"AO"+library_name+"|AB"+item_id+"|AJ|AFBUKU TIDAK DITEMUKAN"+"\r", 'utf-8')

                else :

                    # get title
                    biblio_id = myresult[0][1]
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM search_biblio WHERE biblio_id="+str(biblio_id))
                    myresult = mycursor.fetchall()
                    title = myresult[0][1]

                    # for circulation status
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM loan WHERE item_code='"+item_id+"' ORDER BY `loan_id`")
                    myresult = mycursor.fetchall()
                    if len(myresult) != 0:
                        for x in myresult:
                            last = x
                            print(last)
                        
                    if last[8] == 1 and last[9] == 1: # if is_lent 1 and is_return 1 then book returned and available
                        cs = "03"
                    elif last[8] == 1 and last[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                        cs = "02"
                    else :
                        cs = "03"

                    # Form data
                    resp = bytes("18"+cs+"0001"+gettime()+"AO"+library_name+"|AB"+item_id+"|AJ"+title+"\r", 'utf-8')

            # patron end session
            elif string[0:2] == "35":
                # get user ID
                user_id = string.split("AA")[1].split("|")[0]
                resp = bytes("36Y"+gettime()+"|AO"+library_name+"|AA"+user_id+"\r", 'utf-8')
            
            # patron status
            elif string[0:2] == "23":
                # get user ID
                user_id = string.split("AA")[1].split("|")[0]

                # check user
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM member WHERE member_id='"+user_id+"'")
                myresult = mycursor.fetchall()

                if len(myresult) == 0:
                    resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|BLN|AFANGGOTA TIDAK DITEMUKAN"+"\r", 'utf-8')
                else :
                    name = myresult[0][1]
                    expdate = myresult[0][17]
                    if datetime.datetime.date(datetime.datetime.now()) > expdate:
                        resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANGGOTATIDAKAKTIF"+"\r", 'utf-8')
                    
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM fines WHERE member_id='"+user_id+"'")
                    myresult = mycursor.fetchall()
                    debet = 0
                    credit = 0
                    for x in myresult:
                        debet += x[3]
                        credit += x[4]

                    if debet - credit != 0:
                        resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANDA DIKENAKAN DENDA, SILAHKAN HUBUNGI MEJA SIRKULASI"+"\r", 'utf-8')    
                    resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLY"+"\r", 'utf-8')


            # patron information
            elif string[0:2] == "63":
                # get user ID
                user_id = string.split("AA")[1].split("|")[0]

                # check user
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM member WHERE member_id='"+user_id+"'")
                myresult = mycursor.fetchall()
                if len(myresult) == 0:
                    resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|BLN|AFANGGOTA TIDAK DITEMUKAN"+"\r","utf-8")
                else :
                    name = myresult[0][1]
                    expdate = myresult[0][17]
                    if datetime.datetime.date(datetime.datetime.now()) > expdate:
                        resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANGGOTATIDAKAKTIF"+"\r","utf-8")
                    
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM fines WHERE member_id='"+user_id+"'")
                    myresult = mycursor.fetchall()
                    debet = 0
                    credit = 0
                    for x in myresult:
                        debet += x[3]
                        credit += x[4]

                    if debet - credit != 0:
                        resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLY|AFANDA DIKENAKAN DENDA, SILAHKAN HUBUNGI MEJA SIRKULASI"+"\r","utf-8")

                    resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLY"+"\r","utf-8")

            # check out
            elif string[0:2] == "11":
                # get user id and item id
                user_id = string.split("AA")[1].split("|")[0]
                item_id = string.split("AB")[1].split("|")[0]

                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM fines WHERE member_id='"+user_id+"'")
                myresult = mycursor.fetchall()
                debet = 0
                credit = 0
                for x in myresult:
                    debet += x[3]
                    credit += x[4]

                if debet - credit != 0:
                    resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"AH|AB"+item_id+"|AJ|AFANDA DIKENAKAN DENDA, SILAHKAN HUBUNGI MEJA SIRKULASI"+"\r", 'utf-8')
                    
                else :
                    # get member type
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM member WHERE member_id='"+user_id+"'")
                    myresult = mycursor.fetchall()
                    member_type = myresult[0][4]

                    # get max loan, and loan duration
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM mst_member_type WHERE member_type_id='"+str(member_type)+"'")
                    myresult = mycursor.fetchall()
                    loan_limit = myresult[0][2]
                    loan_periode = myresult[0][3]
                    
                    # check loan
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM loan WHERE member_id='"+user_id+"' ORDER BY `loan_id`")
                    myresult = mycursor.fetchall()
                    loan = 0
                    if len(myresult) != 0:
                        for x in myresult:
                            print(x)
                            if x[8] == 1 and x[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                loan += 1
                    
                    print(loan)
                    if loan == loan_limit:
                        resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"AH|AB"+item_id+"|AJ|AFSUDAH MENCAPAI LIMIT PEMINJAMAN"+"\r", 'utf-8')
                    
                    else:
                        # check book
                        mycursor = mydb.cursor()
                        mycursor.execute("SELECT * FROM item WHERE item_code='"+item_id+"'")
                        myresult = mycursor.fetchall()
                        if len(myresult) == 0 :
                            resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"AH|AB"+item_id+"|AJ|AFBUKU TIDAK DITEMUKAN"+"\r", 'utf-8')
                        else :
                            biblio_id = myresult[0][1]
                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM search_biblio WHERE biblio_id="+str(biblio_id))
                            myresult = mycursor.fetchall()
                            title = myresult[0][1]

                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM loan WHERE item_code='"+item_id+"' ORDER BY `loan_id`")
                            myresult = mycursor.fetchall()
                            if len(myresult) != 0:
                                for x in myresult:
                                    last = x
                                
                            if last[8] == 1 and last[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"AH|AB"+item_id+"|AJ"+title+"|AFBUKU SUDAH DIPINJAM"+"\r", 'utf-8')
                            else :
                                resp = bytes("121NNY"+gettime()+"AO"+library_name+"|AA"+user_id+"AH|AB"+item_id+"|AJ"+title+"|AFBUKU BERHASIL DIPINJAM"+"\r", 'utf-8')
                                
                                # insert to loan
                                sql = "INSERT INTO loan (item_code, member_id, loan_date, due_date, is_lent, input_date, last_update) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                val = (item_id, user_id, datetime.datetime.now().strftime('%Y-%m-%d'), (datetime.datetime.now() + datetime.timedelta(days=loan_periode)).strftime('%Y-%m-%d'), 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                                mycursor.execute(sql, val)

                                mydb.commit()

                                print(mycursor.rowcount, "record inserted.")
                                print(mycursor._warnings)

                                # insert to log
                                sql = "INSERT INTO system_log (log_type, id, log_location, sub_module, action, log_msg, log_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                val = ("system", user_id, "circulation", "Loan", "Add", "Gateway: Loan", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                                mycursor.execute(sql, val)

                                mydb.commit()

                                print(mycursor.rowcount, "record inserted.")
                                print(mycursor._warnings)
                    
            # check in
            elif string[0:2] == "09":
                returnY = string[3:7]
                returnM = string[7:9]
                returnD = string[9:11]
                print(returnY, returnM, returnD)
                item_id = string.split("AB")[1].split("|")[0]

                # check book
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM item WHERE item_code='"+item_id+"'")
                myresult = mycursor.fetchall()
                if len(myresult) == 0 :
                    resp = bytes("100NNN"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU TIDAK DITEMUKAN"+"\r", 'utf-8')

                else :
                    biblio_id = myresult[0][1]
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM search_biblio WHERE biblio_id="+str(biblio_id))
                    myresult = mycursor.fetchall()
                    title = myresult[0][1]

                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM loan WHERE item_code='"+item_id+"' ORDER BY `loan_id`")
                    myresult = mycursor.fetchall()
                    if len(myresult) != 0:
                        for x in myresult:
                            last = x

                        if last[8] == 1 and last[9] == 1: # if is_lent 1 and is_return 0 then book in lent and not available    
                            resp = bytes("100NNY"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU BELUM DIPINJAM"+"\r", 'utf-8')
                        
                        else:
                            resp = bytes("101YNN"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU BERHASIL DIKEMBALIKAN"+"\r", 'utf-8')

                            # update to loan
                            sql = "UPDATE loan SET is_return=%s, return_date=%s, last_update=%s WHERE loan_id=%s"
                            val = ("1", returnY + "-" + returnM + "-" + returnD, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), last[0])

                            mycursor.execute(sql, val)

                            mydb.commit()

                            print(mycursor.rowcount, "record inserted.")
                            print(mycursor._warnings)
                    
                    else:
                        resp = bytes("100NNY"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU BELUM DIPINJAM"+"\r", 'utf-8')


            print(resp)
            conn.sendall(resp)

# id = "B00001"

# mycursor = mydb.cursor()
# mycursor.execute("SELECT * FROM item WHERE item_code='"+id+"'")
# myresult = mycursor.fetchall()
# print(myresult[0])


# mycursor = mydb.cursor()

# # get user info
# # mycursor.execute("SELECT * FROM member WHERE member_id="+str(id))

# # myresult = mycursor.fetchall()

# # for x in myresult:
# #   print(x[1])


# # add loan
# sql = "INSERT INTO loan (item_code, member_id, loan_date, due_date, is_lent) VALUES (%s, %s, %s, %s, %s)"
# val = ("B00007", "123", datetime.datetime.now().strftime('%Y-%m-%d'), (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'), 1)



# mycursor.execute(sql, val)

# mydb.commit()

# print(mycursor.rowcount, "record inserted.")
# print(mycursor._warnings)