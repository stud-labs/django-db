## Встроенные процедуры для таблицы ```Employee```

Данная таблица является зависимой от таблицы ```Department``` через ```FOREIGN KEY```, что должно быть учтено в процедурах изменения набора кортежей.

### Представление для таблицы ```Employee```

Суть данного представления (View) заключается в порождении виртуальной таблицы, удобной для отображения всей 
информации о служащем, включая отдел (```Department```), где он работает. Представление, затем, может быть 
дополнительно упорядочено, спроецировано и т.д. в зависимости от потребностей клиентской программы.

```sql
CREATE OR REPLACE VIEW public.emp_in_dep
 AS
 SELECT e.personname,
    e.birthdate,
    e.email,
    e.jobposition,
    e.tablenumber,
    e.department,
    d.name
   FROM employee e
     JOIN department d ON d.number = e.department;

ALTER TABLE public.emp_in_dep
    OWNER TO dbstudent;
```

### Добавление нового служащего

При добавлении нового служащего надо проверить следующие данные:

1. Не должно быть повторного табельного номера (первичный ключ).
2. Не должно быть повторений адреса email (не реализовано).
3. Отдел, куда добавляется сотрудник должен существовать.

```sql
CREATE OR REPLACE PROCEDURE public."INSERT_EMPLOYEE"(
	IN mpersonname character varying,
	IN mbirthdate date,
	IN memail character varying,
	IN mjobposition character varying,
	IN mtablenumber integer,
	IN mdepartment uuid)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
	IF EXISTS (SELECT tablenumber FROM Employee WHERE tablenumber=mtablenumber)
	THEN
		RAISE EXCEPTION 'There is Employee with table number %. No insertion wasperformed!', mtablenumber;
	ELSE
		IF NOT EXISTS (SELECT "number" from department WHERE "number"=mdepartment)
		THEN
			RAISE EXCEPTION 'There is no department identified by %.', mdepartment;
		ELSE
			INSERT INTO public.employee
				(personname, birthdate, email, jobposition, tablenumber, department)
				VALUES
				(mpersonname, mbirthdate, memail, mjobposition, mtablenumber, mdepartment);
		END IF;
	END IF;
END
$BODY$;
ALTER PROCEDURE public."INSERT_EMPLOYEE"(character varying, date, character varying, character varying, integer, uuid)
    OWNER TO dbstudent;

COMMENT ON PROCEDURE public."INSERT_EMPLOYEE"(character varying, date, character varying, character varying, integer, uuid)
    IS 'Insert new Employee';
```

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
dbstudent@(none):test> call "UPDATE_EMPLOYEE"(
     'Jud Lee the 4-th',
     '1977-02-01', 
     'jud@example.com',
     'Janitor',
     501 
 );
CALL
Time: 0.002s
dbstudent@(none):test> select * from emp_in_dep;
+------------------+------------+-----------------+-------------+-------------+----------------------------------->
| personname       | birthdate  | email           | jobposition | tablenumber | department                        >
|------------------+------------+-----------------+-------------+-------------+----------------------------------->
| Jud Lee the 4-th | 1977-02-01 | jud@example.com | Janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de>
| Samanta Fox 4    | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de>
| Suzy             | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db898>
+------------------+------------+-----------------+-------------+-------------+----------------------------------->
SELECT 3
Time: 0.007s
```

#### Реакция на неправильные входные данные

Исходное состояние таблицы ```Employee```

```text
dbstudent@(none):test> select * from emp_in_dep;
+------------------+------------+-----------------+-------------+-------------+----------------------------------->
| personname       | birthdate  | email           | jobposition | tablenumber | department                        >
|------------------+------------+-----------------+-------------+-------------+----------------------------------->
| Jud Lee the 4-th | 1977-02-01 | jud@example.com | Janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de>
| Samanta Fox 4    | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de>
| Suzy             | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db898>
+------------------+------------+-----------------+-------------+-------------+----------------------------------->
SELECT 3
Time: 0.007s
```

Обновление несуществующего служащего

```text
dbstudent@(none):test> call "UPDATE_EMPLOYEE"(
     'Jud Lee the 4-th',
     '1977-02-01', 
     'jud@example.com',
     'Janitor',
     505
 );
There is no Employee with table number 505.
CONTEXT:  функция PL/pgSQL "UPDATE_EMPLOYEE"(character varying,date,character varying,character varying,integer), >
Time: 0.002s
```
Удаление несуществующего служащего

```text
dbstudent@(none):test> call "DELETE_EMPLOYEE"(505);
There is no Employee with table number 505!
CONTEXT:  функция PL/pgSQL "DELETE_EMPLOYEE"(integer), строка 5, оператор RAISE
Time: 0.002s

```

Добавление а) нового служащего под существующим табельным номером и б) 

```text
dbstudent@(none):test> call "INSERT_EMPLOYEE"(
     'Jud Lee',
     '1978-01-01',
     'jud@example.com',
     'janitor',
     502,
     UUID('b9ccd2e0-5e75-4740-86df-7a050071de72')
 );
There is no department identified by b9ccd2e0-5e75-4740-86df-7a050071de72.
CONTEXT:  функция PL/pgSQL "INSERT_EMPLOYEE"(character varying,date,character varying,>
Time: 0.003s
dbstudent@(none):test> call "INSERT_EMPLOYEE"(
     'Jud Lee',
     '1978-01-01',
     'jud@example.com',
     'janitor',
     501,
     UUID('b9ccd2e0-5e75-4740-86df-7a050071de72')
 );
There is Employee with table number 501. No insertion wasperformed!
CONTEXT:  функция PL/pgSQL "INSERT_EMPLOYEE"(character varying,date,character varying,>
Time: 0.003s
```
