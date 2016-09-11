#! /usr/bin/env python3

import sys, os, pymssql, requests, json, collections

outfolder = '/var/www/toolbox/json'

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
where (paygroup <> 'CCA' and status = 'A')
""")

conn.commit()

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_users')

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
 
j = json.dumps(objects_list, indent=4)

with open(outfolder + '/sc_users.json', 'w') as f:
	f.write(j)


# ****************************** SC_pi_all ********************************
cursor = conn.cursor()
cursor.execute("""
DROP TABLE SC_pi_all
select
  lower(last_name) + '_' + (case when PREFERRED_NAME = '' or PREFERRED_NAME is null
  then substring(lower(FIRST_NAME),1,1)
  else substring(lower(PREFERRED_NAME),1,1) collate Latin1_General_BIN
  end) as pi_dept,
  FH_CENTERALIAS as uid,
  "NAME" as displayName,
  LAST_NAME as sn,
  case when PREFERRED_NAME = '' or PREFERRED_NAME is null
  then FIRST_NAME
  else PREFERRED_NAME collate Latin1_General_BIN
  end as givenName,
  FH_EMAIL_ADDR1 as mail,
  JOBTITLE as jobTitle,
  DESCR as department,
  FH_DIVISION as division
into SCICOMP.dbo.SC_pi_all
from SCICOMP.dbo.PS_FH_STAFF
where (((JOB_FUNCTION = 'FAC' and PAYGROUP = 'FHC') or JOBTITLE = 'Full Member') and EMPL_STATUS = 'A')
group by DEPTID, FH_CENTERALIAS, PREFERRED_NAME, "NAME", LAST_NAME, FIRST_NAME, FH_EMAIL_ADDR1, JOBTITLE, DESCR, FH_DIVISION
""")

conn.commit()

cursor = conn.cursor()
cursor.execute('SELECT * FROM SC_pi_all')

rows = cursor.fetchall()

objects_list = []
objects_list_today = []
for row in rows:
        d = collections.OrderedDict()
        d['pi_dept'] = row[0]
        d['uid'] = row[1]
        d['displayName'] = row[2]
        d['sn'] = row[3]
        d['givenName'] = row[4].strip()
        d['mail'] = row[5]
        d['jobtitle'] = row[6]
        d['department'] = row[7]
        d['division'] = row[8]
        objects_list.append(d)

conn.close()

j = json.dumps(objects_list, indent=4)

with open(outfolder + '/pi_all.json', 'w') as f:
        f.write(j)

sys.exit()

