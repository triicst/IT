#include <cstdlib>
#include <iostream>
#include <pqxx/pqxx>

using namespace std;
using namespace pqxx;

class databaseConnection
{
public:
    pqxx::connection* conn;
    void SetConnection(){
        conn=new pqxx::connection(
            "host=mydb "
            "port=32061 "
            "dbname=jd-test");

    }

    void Disconnect(){
        conn->disconnect();
    }

    pqxx::result
    Query(std::string strSQL){
        //SetConnection();
        pqxx::work trans(*conn,"trans");

        pqxx::result res=trans.exec(strSQL);

        trans.commit();
        return res;
    }
    
    void
    Insert(string sql){
        pqxx::work W(*conn);
        W.exec(sql);
        W.commit();
    }
};

int main()
{
    pqxx::result r;

    databaseConnection pdatabase;
    pdatabase.SetConnection();
    string sql = "INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) "
         "VALUES ('Paul 2', 32, 'California', 20000.00 ); "
         "INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) "
         "VALUES ('Allen 2', 25, 'Texas', 15000.00 ); "
         "INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY)"
         "VALUES ('Teddy 2', 23, 'Norway', 20000.00 );"
         "INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY)"
         "VALUES ('Mark 2', 25, 'Rich-Mond ', 65000.00 );";

    pdatabase.Insert(sql);
    r = pdatabase.Query("select * from company");
    
    for (auto row: r) {
        std::cout << "Row: ";
        for ( auto field: row)
            std::cout << field.c_str() << " ";
        std::cout << std::endl;
    }
    return 0;
}
