#! /usr/bin/env python3

import sys, os, pymssql, requests, csv, json, collections

outfolder = '/var/www/toolbox'

with open('/root/sqlcreds', 'r') as f:
    server,database,user,password = f.readline().strip().split(':')

conn=pymssql.connect(server=server, user=user, password=password, database=database)


# ****************************** SC_Users ********************************
cursor = conn.cursor()
cursor.execute("""
DROP TABLE SC_users
;with usersfiltered as (
  select
    EMPLID as employeeID,
    FH_CENTERALIAS as uid,
    NAME as displayName,
    FH_EMAIL_ADDR1 as mail,
    BUSINESS_TITLE as title,
    FH_DIVISION as division,
    FH_SUPV_NAME as mgrName,
    case when PREFERRED_NAME = '' or PREFERRED_NAME is null
    then FIRST_NAME
    else PREFERRED_NAME collate Latin1_General_BIN
    end as givenName,
    LAST_NAME as sn,
    REHIRE_DT as hireDate,
    DEPTID as deptID,
    SUPERVISOR_ID as mgrID,
    PAYGROUP as paygroup,
    JOB_FUNCTION as jobFunc,
    JOBTITLE as jobTitle,
    EMPL_STATUS as status,
    row_number() over(partition by EMPLID order by EMPL_RCD desc) as RowNum
    from SCICOMP.dbo.PS_FH_STAFF
)
select *
into SCICOMP.dbo.SC_users
from usersfiltered
INNER JOIN SCICOMP.dbo.SC_CostCenters
ON usersfiltered.deptID = SCICOMP.dbo.SC_CostCenters.dept_id
where (paygroup <> 'CCA' and status <> 'T')
""")

conn.commit()

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_users')
columns = [i[0] for i in cursor.description]
rows = cursor.fetchall()

objects_list = []
objects_list_today = []
for row in rows:
	d = collections.OrderedDict()
	d['employeeID'] = row[0]
	d['uid'] = row[1]
	d['displayName'] = row[2]
	d['mail'] = row[3]
	d['title'] = row[4]
	d['division'] = row[5]
	d['mgrName'] = row[6]
	d['givenName'] = row[7].strip()
	d['sn'] = row[8]
	d['hireDate'] = row[9].isoformat()
	#d['deptID'] = row[10]
	d['mgrID'] = row[11]
	d['paygroup'] = row[12]
	d['jobFunc'] = row[13]
	d['jobTitle'] = row[14]
	d['status'] = row[15]
	#d['RowNum'] = row[16]
	d['dept_id'] = row[17]
	d['pi_dept'] = row[18]
	d['dept_manager'] = row[19]
	d['department'] = row[20]
	objects_list.append(d)
 
j = json.dumps(objects_list, indent=4, default=lambda x:str(x))

with open(outfolder + '/json/sc_users.json', 'w') as f:
	f.write(j)

with open(outfolder + '/csv/sc_users.csv', 'w') as f:
        mycsv = csv.writer(f, dialect='excel')
        mycsv.writerow(columns)
        mycsv.writerows(rows)


# *********************** SC_CostCenters_all *****************************

cursor = conn.cursor()
cursor.execute("""
DROP TABLE SC_CostCenters_all;
select
  DEPTID as dept_id,
  DESCRSHORT as pi_dept,
  COMPANY as organization,
  DESCR as department
into SCICOMP.dbo.SC_CostCenters_all
from SCICOMP.dbo.PS_DEPT_TBL
where (COMPANY <> 'CCA') ;
""")

conn.commit()

# ****************************** ALL_users ********************************
### DROP TABLE SC_users_all

cursor = conn.cursor()
cursor.execute("""
DROP TABLE SC_users_all
;with usersfiltered as (
  select
    EMPLID as employeeID,
    FH_CENTERALIAS as uid,
    NAME as displayName,
    FH_EMAIL_ADDR1 as mail,
    BUSINESS_TITLE as title,
    FH_DIVISION as division,
    FH_SUPV_NAME as mgrName,
    case when PREFERRED_NAME = '' or PREFERRED_NAME is null
    then FIRST_NAME
    else PREFERRED_NAME collate Latin1_General_BIN
    end as givenName,
    LAST_NAME as sn,
    REHIRE_DT as hireDate,
    DEPTID as deptID,
    SUPERVISOR_ID as mgrID,
    PAYGROUP as paygroup,
    JOB_FUNCTION as jobFunc,
    JOBTITLE as jobTitle,
    EMPL_STATUS as status,
    row_number() over(partition by EMPLID order by EMPL_RCD desc) as RowNum
    from SCICOMP.dbo.PS_FH_STAFF
)
select *
into SCICOMP.dbo.SC_users_all
from usersfiltered
INNER JOIN SCICOMP.dbo.SC_CostCenters_all
ON usersfiltered.deptID = SCICOMP.dbo.SC_CostCenters_all.dept_id
where (paygroup <> 'CCA' and status <> 'T')
""")


conn.commit()

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_users_all')
columns = [i[0] for i in cursor.description]
rows = cursor.fetchall()

objects_list = []
objects_list_today = []
for row in rows:
        d = collections.OrderedDict()
        d['employeeID'] = row[0]
        d['uid'] = row[1]
        d['displayName'] = row[2]
        d['mail'] = row[3]
        d['title'] = row[4]
        d['division'] = row[5]
        d['mgrName'] = row[6]
        d['givenName'] = row[7].strip()
        d['sn'] = row[8]
        d['hireDate'] = row[9].isoformat()
        #d['deptID'] = row[10]
        d['mgrID'] = row[11]
        d['paygroup'] = row[12]
        d['jobFunc'] = row[13]
        d['jobTitle'] = row[14]
        d['status'] = row[15]
        #d['RowNum'] = row[16]
        d['dept_id'] = row[17]
        d['pi_dept'] = row[18]
        d['dept_manager'] = row[19]
        d['department'] = row[20]
        objects_list.append(d)

j = json.dumps(objects_list, indent=4, default=lambda x:str(x))

with open(outfolder + '/json/users_all.json', 'w') as f:
        f.write(j)

with open(outfolder + '/csv/users_all.csv', 'w') as f:
        mycsv = csv.writer(f, dialect='excel')
        mycsv.writerow(columns)
        mycsv.writerows(rows)


# ****************************** SC_pi_all ********************************
cursor = conn.cursor()
cursor.execute("""
DROP TABLE SC_pi_all
select
  lower(last_name) + '_' + (case when PREFERRED_NAME = '' or PREFERRED_NAME is null
  then substring(lower(FIRST_NAME),1,1)
  else substring(lower(PREFERRED_NAME),1,1) collate Latin1_General_BIN
  end) as pi_dept,
  EMPLID as employeeID,
  FH_CENTERALIAS as uid,
  "NAME" as displayName,
  LAST_NAME as sn,
  case when PREFERRED_NAME = '' or PREFERRED_NAME is null
  then FIRST_NAME
  else PREFERRED_NAME collate Latin1_General_BIN
  end as givenName,
  FH_EMAIL_ADDR1 as mail,
  JOBTITLE as jobTitle,
  BUSINESS_TITLE as businessTitle,
  FH_SUPV_NAME as mgrName,
  DESCR as department,
  FH_DIVISION as division
into SCICOMP.dbo.SC_pi_all
from SCICOMP.dbo.PS_FH_STAFF
where (((JOB_FUNCTION = 'FAC' and PAYGROUP = 'FHC') or JOBTITLE = 'Full Member') and EMPL_STATUS <> 'T')
group by DEPTID, EMPLID, FH_CENTERALIAS, PREFERRED_NAME, "NAME", LAST_NAME, FIRST_NAME, FH_EMAIL_ADDR1, JOBTITLE, BUSINESS_TITLE, FH_SUPV_NAME, DESCR, FH_DIVISION
""")

conn.commit()


#### 

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_pi_all UNION SELECT * FROM SC_pi_extra order by employeeID')
columns = [i[0] for i in cursor.description]
rows = cursor.fetchall()

objects_list = []
objects_list_today = []
for row in rows:
        d = collections.OrderedDict()
        d['pi_dept'] = row[0]
        d['employeeID'] = row[1]
        d['uid'] = row[2]
        d['displayName'] = row[3]
        d['sn'] = row[4]
        d['givenName'] = row[5].strip()
        d['mail'] = row[6]
        d['jobTitle'] = row[7]
        d['businessTitle'] = row[8]
        d['mgrName'] = row[9]
        d['department'] = row[10]
        d['division'] = row[11]
        objects_list.append(d)

conn.commit()

j = json.dumps(objects_list, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/pi_all.json', 'w') as f:
        f.write(j)

with open(outfolder + '/csv/pi_all.csv', 'w') as f:
        mycsv = csv.writer(f, dialect='excel')
        mycsv.writerow(columns)
        mycsv.writerows(rows)

# listing just the faculty without the staff scientists

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_pi_all;')
columns = [i[0] for i in cursor.description]
rows = cursor.fetchall()

objects_list = []
objects_list_today = []
for row in rows:
        d = collections.OrderedDict()
        d['pi_dept'] = row[0]
        d['employeeID'] = row[1]
        d['uid'] = row[2]
        d['displayName'] = row[3]
        d['sn'] = row[4]
        d['givenName'] = row[5].strip()
        d['mail'] = row[6]
        d['jobTitle'] = row[7]
        d['businessTitle'] = row[8]
        d['mgrName'] = row[9]
        d['department'] = row[10]
        d['division'] = row[11]
        objects_list.append(d)

conn.close()

j = json.dumps(objects_list, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/faculty.json', 'w') as f:
        f.write(j)

with open(outfolder + '/csv/faculty.csv', 'w') as f:
        mycsv = csv.writer(f, dialect='excel')
        mycsv.writerow(columns)
        mycsv.writerows(rows)


sys.exit()

