## Встроенные процедуры для таблицв ```Department```

(Здесь я их пропускаю, т.к. они проще, чем те, что у ```Employee```, за исключением удаления)

. . . . .

### Процедура удаления отдела

При удаление отдела необходимо проверить:

1. Существование отдела (по его ```UUID```);
2. Существование сотрудников в отделе.

Если одно о из условий не соблюдается, выдать информативное сообщение.

```plpgsql
CREATE OR REPLACE PROCEDURE public."DELETE_DEPARTMENT"(
	IN mnumber uuid)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
 	IF NOT EXISTS (SELECT number FROM department WHERE number=mnumber)
 	THEN
 		RAISE EXCEPTION 'There is no department with id %.', mnumber;
 	END IF;
	IF EXISTS (SELECT tablenumber FROM employee e WHERE e.department=mnumber)
	THEN
		RAISE EXCEPTION 'There are employees in the depatment %. No deletion done!', mnumber;
	END IF;
	DELETE FROM department WHERE number=mnumber;
END

$BODY$;
ALTER PROCEDURE public."DELETE_DEPARTMENT"(uuid)
    OWNER TO dbstudent;

COMMENT ON PROCEDURE public."DELETE_DEPARTMENT"(uuid)
    IS 'Удаляет отдел, если это семантически возможно.';
```

### Тестирование встроенных процедур для таблицы ```Department```

Пусть задано начальное состояние таблицы отделов. В таблица содержит семнтически повторяющиеся
данные - несколько разных отделов с одинаковым имененм. Это и есть последствие бездумного использования
оператора ```INSERT INTO ...``` без контроля входных данных.

Вообще, дополнительный контроль можно добавить к таблице в виде
ограничений (```... CONSTRAINT ...``` ```UNIQUE```), тогда при добавлении, в частности, будет
автоматически контролироваться "уникальность" значения поля среди кортежей. При нарушеии этого ограничения будет создаваться исключение, его можно "показывать" пользователю, но пользователь врят ли поймет что-то вроде "невозможно добавить запись: дублирование значения колонки 'name'"... и побежит к
админу/разработчику... т.е. к вам с притензиями к работе программного обеспечения.

Итак, сделаем так, покажем как использование встроенной процедуры позволяет избегать неловких ситуаци вышеописанного рода. (Очевидно, раз мы не реализовали все три процедуры DML, здесь показываем
тестирование только одной).

Повторю - исходная "кривая" таблица.

```text
dbstudent@(none):test> select * from department;
+--------------------------------------+--------------+
| number                               | name         |
|--------------------------------------+--------------|
| b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT         |
| 69fa8510-0cc9-4235-8aef-ee2e84acad51 | IMIT         |
| 285242ac-fa97-4ccb-b56f-d8651db8982d | IMIT         |
| 007557e5-beca-4891-ae44-0448c777437e | Geographical |
+--------------------------------------+--------------+
SELECT 4
Time: 0.006s

```

Пытаемя удалить несуществующий отдел.

```txt
dbstudent@(none):test> call "DELETE_DEPARTMENT"(UUID('b9ccd2e0-5e75-4740-86df-7a050071de70'));
There is no department with id b9ccd2e0-5e75-4740-86df-7a050071de70.
CONTEXT:  функция PL/pgSQL "DELETE_DEPARTMENT"(uuid), строка 5, оператор RAISE
Time: 0.002s
```

Да. Может быть стоило сделать параметр процедуры типа ```VARCHAR`` (```CHARACTER VARYING```) и потом
преобразовать его при помощи ```UUID(...)```....

Провериим удаление отдела с существующим сотрудниками.

```txt
dbstudent@(none):test> call "DELETE_DEPARTMENT"(UUID('b9ccd2e0-5e75-4740-86df-7a050071de7f'));
There are employees in the depatment b9ccd2e0-5e75-4740-86df-7a050071de7f. No deletion done!
CONTEXT:  функция PL/pgSQL "DELETE_DEPARTMENT"(uuid), строка 9, оператор RAISE
Time: 0.002s
```

В залючение, успешное добавление.

```text
dbstudent@(none):test> call "DELETE_DEPARTMENT"(UUID('69fa8510-0cc9-4235-8aef-ee2e84acad51'));
CALL
Time: 0.002s
dbstudent@(none):test> select * from department;
+--------------------------------------+--------------+
| number                               | name         |
|--------------------------------------+--------------|
| b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT         |
| 285242ac-fa97-4ccb-b56f-d8651db8982d | IMIT         |
| 007557e5-beca-4891-ae44-0448c777437e | Geographical |
+--------------------------------------+--------------+
SELECT 3
Time: 0.006s
```

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

Проблемы, выявленные в процессе выполнения операции указываются при помощи исключений с
содержательными сообщениями.

```plpgsql
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

### Удаление служащего

При удалении служащего необходимо проверить его наличие в таблице ```Employee```. Если его там нет, вывести
информативное сообщение при помощи создания исключения.


```plpgsql
CREATE OR REPLACE PROCEDURE public."DELETE_EMPLOYEE"(
	IN mtablenumber integer)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
	IF NOT EXISTS (SELECT tablenumber FROM Employee WHERE tablenumber=mtablenumber)
	THEN
		RAISE EXCEPTION 'There is no Employee with table number %!', mtablenumber;
	ELSE
		DELETE FROM public.employee WHERE tablenumber=mtablenumber;
	END IF;
END
$BODY$;
ALTER PROCEDURE public."DELETE_EMPLOYEE"(integer)
    OWNER TO dbstudent;
```

### Обновление служащего

При обновлении служащего проверяется его существование по табельному номеру (едиственный параметр процедуры).

```plpgsql
CREATE OR REPLACE PROCEDURE public."UPDATE_EMPLOYEE"(
	IN mpersonname character varying,
	IN mbirthdate date,
	IN memail character varying,
	IN mjobposition character varying,
	IN mtablenumber integer)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
-- tablenumber is the primary key, so it is not updatable
	IF EXISTS (SELECT tablenumber FROM Employee WHERE tablenumber=mtablenumber)
	THEN
		UPDATE public.employee
			SET
			personname=mpersonname, birthdate=mbirthdate,
			email=memail, jobposition=mjobposition  -- ,
												-- tablenumber=?, department=?
			WHERE tablenumber = mtablenumber;
	ELSE
		RAISE EXCEPTION 'There is no Employee with table number %.', mtablenumber;
	END IF;
END
$BODY$;
ALTER PROCEDURE public."UPDATE_EMPLOYEE"(character varying, date, character varying, character varying, integer)
    OWNER TO dbstudent;

COMMENT ON PROCEDURE public."UPDATE_EMPLOYEE"(character varying, date, character varying, character varying, integer)
    IS 'Update Employee data';
```


### Тестирование добавления, удаления, обновления процедур над таблицей Employee

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

Добавление а) добавление служащего в несуществующий отдел,
б) нового служащего под существующим табельным номером.

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
