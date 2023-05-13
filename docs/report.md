

### Тестирование добавления, удаление, обновления процедур над таблицей Employee

```text
dbstudent@(none):test> select * from emp_in_dep;
+---------------+------------+-----------------+-------------+-------------+-------------------------------------->
| personname    | birthdate  | email           | jobposition | tablenumber | department                           >
|---------------+------------+-----------------+-------------+-------------+-------------------------------------->
| Jud Lee       | 1978-01-01 | jud@example.com | janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de7f >
| Samanta Fox 4 | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f >
| Suzy          | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db8982d >
+---------------+------------+-----------------+-------------+-------------+-------------------------------------->
SELECT 3
Time: 0.008s
dbstudent@(none):test> call "DELETE_EMPLOYEE"(501);
CALL
Time: 0.001s
dbstudent@(none):test> select * from emp_in_dep;
+---------------+-----------+--------+-------------+-------------+--------------------------------------+------+
| personname    | birthdate | email  | jobposition | tablenumber | department                           | name |
|---------------+-----------+--------+-------------+-------------+--------------------------------------+------|
| Samanta Fox 4 | <null>    | <null> | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT |
| Suzy          | <null>    | <null> | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db8982d | IMIT |
+---------------+-----------+--------+-------------+-------------+--------------------------------------+------+
SELECT 2
Time: 0.007s
dbstudent@(none):test> call "INSERT_EMPLOYEE"(
     'Jud Lee',
     '1978-01-01',
     'jud@example.com',
     'janitor',
     501,
     UUID('b9ccd2e0-5e75-4740-86df-7a050071de7f')
 );
CALL
Time: 0.002s
dbstudent@(none):test> select * from emp_in_dep;
+---------------+------------+-----------------+-------------+-------------+-------------------------------------->
| personname    | birthdate  | email           | jobposition | tablenumber | department                           >
|---------------+------------+-----------------+-------------+-------------+-------------------------------------->
| Jud Lee       | 1978-01-01 | jud@example.com | janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de7f >
| Samanta Fox 4 | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f >
| Suzy          | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db8982d >
+---------------+------------+-----------------+-------------+-------------+-------------------------------------->
SELECT 3
Time: 0.007s
```


