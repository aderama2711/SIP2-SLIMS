import mysql.connector
import datetime
import socket
import traceback

HOST = "127.0.0.1"  # The IP Address of Translator SIP 
PORT = 6001  # The port used by Translator SIP

library_name = "Perpustakaan"
language = "001"
slims_version = "8" # Please select the version

mydb = mysql.connector.connect(
  host="localhost", #IP Address of the database
  user="userslims", #db username (read/write) access
  password="slims", #db password
  port="3306", # port used by the db
  database="slims8" # name of the db
)

def gettime():
    return datetime.datetime.now().strftime("%Y%m%d    %H%M%S")

def logtime():
    return datetime.datetime.now().strftime("%d/%m/%Y %H/%M/%S")

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(logtime(),f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    string = data.decode('utf-8')
                    print(logtime(),string)
                    if not data:
                        break

                    resp = bytes("", "utf-8")
                    title = ""
                    item_id = ""
                    user_id = ""

                    # SC registration
                    if string[0:2] == "99":
                        print(logtime(),"SC registration")
                        resp = bytes("98YYYNNN500   003"+gettime()+"2.00AO"+library_name+"|BXNYYNYNNYNNYNNNNN"+"\r", 'utf-8')
                    
                    # item information
                    if string[0:2] == "17":
                        print(logtime(),"Item Information")
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
                            mycursor.execute("SELECT * FROM biblio WHERE biblio_id="+str(biblio_id))
                            myresult = mycursor.fetchall()
                            title = myresult[0][2]

                            # for circulation status
                            loaned = False

                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM loan WHERE item_code='"+item_id+"' ORDER BY `loan_id`")
                            myresult = mycursor.fetchall()
                            if len(myresult) != 0:
                                loaned = True
                                for x in myresult:
                                    last = x

                            due_date = ""
                                
                            if loaned :
                                if last[8] == 1 and last[9] == 1: # if is_lent 1 and is_return 1 then book returned and available
                                    cs = "03"
                                    # Form data
                                    resp = bytes("18"+cs+"0001"+gettime()+"AO"+library_name+"|AB"+item_id+"|AJ"+title+"\r", 'utf-8')

                                elif last[8] == 1 and last[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                    cs = "02"
                                    due_date = last[4]

                                    # Form data
                                    resp = bytes("18"+cs+"0001"+gettime()+"AO"+library_name+"|AH"+due_date.strftime('%Y-%m-%d')+"|AB"+item_id+"|AJ"+title+"\r", 'utf-8')
                            else:
                                cs = "03"
                                # Form data
                                resp = bytes("18"+cs+"0001"+gettime()+"AO"+library_name+"|AB"+item_id+"|AJ"+title+"\r", 'utf-8')

                    # patron end session
                    elif string[0:2] == "35":
                        print(logtime(),"Patron End Session")
                        # get user ID
                        user_id = string.split("AA")[1].split("|")[0]
                        resp = bytes("36Y"+gettime()+"|AO"+library_name+"|AA"+user_id+"\r", 'utf-8')
                    
                    # patron status
                    elif string[0:2] == "23":
                        print(logtime(),"Patron Status")
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
                                resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANGGOTA TIDAK AKTIF"+"\r", 'utf-8')
                            
                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * from loan where is_lent=1 and is_return=0 AND TO_DAYS(due_date) < TO_DAYS(NOW()) AND member_id='"+user_id+"'")
                            myresult = mycursor.fetchall()

                            if len(myresult) != 0:
                                resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANDA DIKENAKAN DENDA, SILAHKAN HUBUNGI MEJA SIRKULASI"+"\r", 'utf-8')    
                            resp = bytes("24"+" "*14+language+gettime()+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLY"+"\r", 'utf-8')


                    # patron information
                    elif string[0:2] == "63":
                        print(logtime(),"Patron Information")
                        # get user ID
                        user_id = string.split("AA")[1].split("|")[0]

                        # check user
                        mycursor = mydb.cursor()
                        mycursor.execute("SELECT * FROM member WHERE member_id='"+user_id+"'")
                        myresult = mycursor.fetchall()
                        if len(myresult) == 0:
                            resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|BLN|AFANGGOTA TIDAK ADA"+"\r","utf-8")
                        else :
                            name = myresult[0][1]
                            expdate = myresult[0][17]
                            if datetime.datetime.date(datetime.datetime.now()) > expdate:
                                resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLN|AFANGGOTA TIDAK AKTIF"+"\r","utf-8")
                            
                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * from loan where is_lent=1 and is_return=0 AND TO_DAYS(due_date) < TO_DAYS(NOW()) AND member_id='"+user_id+"'")
                            myresult = mycursor.fetchall()

                            if len(myresult) != 0:
                                resp = bytes("64              001"+gettime()+(" "*24)+"AO"+library_name+"|AA"+user_id+"|AE"+name+"|BLY|AFANDA DIKENAKAN DENDA, SILAHKAN HUBUNGI MEJA SIRKULASI"+"\r","utf-8")

                            loan_count = 0
                            summary = " "
                            id_list_loan = []

                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM loan WHERE member_id='"+user_id+"' ORDER BY `loan_id`")
                            myresult = mycursor.fetchall()
                            if len(myresult) != 0:
                                for x in myresult:
                                    if x[8] == 1 and x[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                        loan_count += 1
                                        id_list_loan.append(x[1])
                                        summary = "Y"
                            
                            charged_item = ""
                            for id in id_list_loan:
                                charged_item += "|AU"+id


                            resp = bytes("64  "+summary+"           001"+gettime()+(" "*8)+"   "+str(loan_count)+(" "*12)+"AO"+library_name+"|AA"+user_id+"|AE"+name+charged_item+"|BLY"+"\r","utf-8")

                    # check out
                    elif string[0:2] == "11":
                        print(logtime(),"Checkout")
                        # get user id and item id
                        user_id = string.split("AA")[1].split("|")[0]
                        item_id = string.split("AB")[1].split("|")[0]

                        mycursor = mydb.cursor()
                        mycursor.execute("SELECT * from loan where is_lent=1 and is_return=0 AND TO_DAYS(due_date) < TO_DAYS(NOW()) AND member_id='"+user_id+"'")
                        myresult = mycursor.fetchall()

                        if len(myresult) != 0:
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
                            
                            loan_limit = myresult[0][2]+1
                            loan_periode = myresult[0][3]
                            
                            # check loan
                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM loan WHERE member_id='"+user_id+"' ORDER BY `loan_id`")
                            myresult = mycursor.fetchall()
                            loan = 0
                            if len(myresult) != 0:
                                for x in myresult:
                                    if x[8] == 1 and x[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                        loan += 1
                        
                            if loan == loan_limit:
                                resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"|AH|AB"+item_id+"|AJ|AFSUDAH MENCAPAI LIMIT PEMINJAMAN"+"\r", 'utf-8')
                            
                            else:
                                # check book
                                mycursor = mydb.cursor()
                                mycursor.execute("SELECT * FROM item WHERE item_code='"+item_id+"'")
                                myresult = mycursor.fetchall()
                                if len(myresult) == 0 :
                                    resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"|AH|AB"+item_id+"|AJ|AFBUKU TIDAK DITEMUKAN"+"\r", 'utf-8')
                                else :
                                    biblio_id = myresult[0][1]
                                    mycursor = mydb.cursor()
                                    mycursor.execute("SELECT * FROM biblio WHERE biblio_id="+str(biblio_id))
                                    myresult = mycursor.fetchall()
                                    title = myresult[0][2]
                                    
                                    loaned = False

                                    mycursor = mydb.cursor()
                                    mycursor.execute("SELECT * FROM loan WHERE item_code='"+item_id+"' ORDER BY `loan_id`")
                                    myresult = mycursor.fetchall()
                                    if len(myresult) != 0:
                                        loaned = True
                                        for x in myresult:
                                            last = x

                                    if loaned:
                                        if last[8] == 1 and last[9] == 0: # if is_lent 1 and is_return 0 then book in lent and not available
                                            resp = bytes("120NNN"+gettime()+"AO"+library_name+"|AA"+user_id+"|AH|AB"+item_id+"|AJ"+title+"|AFBUKU SUDAH DIPINJAM"+"\r", 'utf-8')
                                        else :
                                            resp = bytes("121NNY"+gettime()+"AO"+library_name+"|AA"+user_id+"|AH"+str((datetime.datetime.now() + datetime.timedelta(days=loan_periode)).strftime('%Y-%m-%d'))+"|AB"+item_id+"|AJ"+title+"|AFBUKU BERHASIL DIPINJAM"+"\r", 'utf-8')
                                            
                                            # insert to loan
                                            sql = "INSERT INTO loan (item_code, member_id, loan_date, due_date, is_lent) VALUES (%s, %s, %s, %s, %s)"
                                            val = (item_id, user_id, datetime.datetime.now().strftime('%Y-%m-%d'), (datetime.datetime.now() + datetime.timedelta(days=loan_periode)).strftime('%Y-%m-%d'), 1)

                                            mycursor.execute(sql, val)

                                            mydb.commit()

                                            print(logtime(),mycursor.rowcount, "record inserted.")
                                            print(logtime(),mycursor._warnings)


                                            if slims_version == 9:
                                                # insert to log
                                                sql = "INSERT INTO system_log (log_type, id, log_location, sub_module, action, log_msg, log_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                                val = ("system", user_id, "circulation", "Loan", "Add", "Gateway: Loan", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                                                mycursor.execute(sql, val)

                                                mydb.commit()

                                                print(logtime(),mycursor.rowcount, "record inserted.")
                                                print(logtime(),mycursor._warnings)
                                    else:
                                        resp = bytes("121NNY"+gettime()+"AO"+library_name+"|AA"+user_id+"|AH"+str((datetime.datetime.now() + datetime.timedelta(days=loan_periode)).strftime('%Y-%m-%d'))+"|AB"+item_id+"|AJ"+title+"|AFBUKU BERHASIL DIPINJAM"+"\r", 'utf-8')
                                            
                                        # insert to loan
                                        sql = "INSERT INTO loan (item_code, member_id, loan_date, due_date, is_lent) VALUES (%s, %s, %s, %s, %s)"
                                        val = (item_id, user_id, datetime.datetime.now().strftime('%Y-%m-%d'), (datetime.datetime.now() + datetime.timedelta(days=loan_periode)).strftime('%Y-%m-%d'), 1)

                                        mycursor.execute(sql, val)

                                        mydb.commit()

                                        print(logtime(),mycursor.rowcount, "record inserted.")
                                        print(logtime(),mycursor._warnings)

                                        if slims_version == 9:
                                            # insert to log
                                            sql = "INSERT INTO system_log (log_type, id, log_location, sub_module, action, log_msg, log_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                            val = ("system", user_id, "circulation", "Loan", "Add", "Gateway: Loan", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                                            mycursor.execute(sql, val)

                                            mydb.commit()

                                            print(logtime(),mycursor.rowcount, "record inserted.")
                                            print(logtime(),mycursor._warnings)
                            
                    # check in
                    elif string[0:2] == "09":
                        print(logtime(),"Checkin")
                        returnY = string[3:7]
                        returnM = string[7:9]
                        returnD = string[9:11]
                        print(logtime(),returnY, returnM, returnD)
                        item_id = string.split("AB")[1].split("|")[0]

                        mycursor = mydb.cursor()
                        mycursor.execute("SELECT * from loan where is_lent=1 and is_return=0 AND TO_DAYS(due_date) < TO_DAYS(NOW()) and item_code='"+item_id+"'")
                        myresult = mycursor.fetchall()

                        if len(myresult) != 0:
                            resp = bytes("100NNY"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFANDA MENDAPAT DENDA, SILAHKAN KE SIRKULASI"+"\r", 'utf-8')

                        # check book
                        mycursor = mydb.cursor()
                        mycursor.execute("SELECT * FROM item WHERE item_code='"+item_id+"'")
                        myresult = mycursor.fetchall()
                        if len(myresult) == 0 :
                            resp = bytes("100NNN"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU TIDAK DITEMUKAN"+"\r", 'utf-8')

                        else :
                            biblio_id = myresult[0][1]
                            mycursor = mydb.cursor()
                            mycursor.execute("SELECT * FROM biblio WHERE biblio_id="+str(biblio_id))
                            myresult = mycursor.fetchall()
                            title = myresult[0][2]

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
                                    sql = "UPDATE loan SET is_return=%s, return_date=%s WHERE loan_id=%s"
                                    val = ("1", returnY + "-" + returnM + "-" + returnD, last[0])

                                    mycursor.execute(sql, val)

                                    mydb.commit()

                                    print(logtime(),mycursor.rowcount, "record inserted.")
                                    print(logtime(),mycursor._warnings)
                            
                            else:
                                resp = bytes("100NNY"+gettime()+"AO"+library_name+"|AB"+item_id+"|AQ|AJ"+title+"|AFBUKU BELUM DIPINJAM"+"\r", 'utf-8')


                    print(logtime(),resp)
                    conn.sendall(resp)
    except Exception as error:
        print(logtime(),traceback.format_exc())

# id = "B00001"

# mycursor = mydb.cursor()
# mycursor.execute("SELECT * FROM item WHERE item_code='"+id+"'")
# myresult = mycursor.fetchall()
# print(logtime(),myresult[0])


# mycursor = mydb.cursor()

# # get user info
# # mycursor.execute("SELECT * FROM member WHERE member_id="+str(id))

# # myresult = mycursor.fetchall()

# # for x in myresult:
# #   print(logtime(),x[1])


# # add loan
# sql = "INSERT INTO loan (item_code, member_id, loan_date, due_date, is_lent) VALUES (%s, %s, %s, %s, %s)"
# val = ("B00007", "123", datetime.datetime.now().strftime('%Y-%m-%d'), (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'), 1)



# mycursor.execute(sql, val)

# mydb.commit()

# print(logtime(),mycursor.rowcount, "record inserted.")
# print(logtime(),mycursor._warnings)
