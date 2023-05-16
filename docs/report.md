

# Лабораторная работа 2 "Разработка серверной части информационной системы"

В данной лабораторной работе необходимо разработать серверную часть гипотетической информационной системы.
Перечень задач, которые требуется решить следующие:

1. Сгенерировать из *физической модели*, спроектированной в лабораторной работе 1, набор DML-запросов создания базы данных.
2. Зполнить накоторыми начальными данными талицы (в качестве примера можно использовать примеры из лабораторной работы 1).
3. Спроектировать представления (View) и встроенные процедуры для
   * подержки содержательного отображения данных таблиц для лабораторной работы 3,
   * корректного с точки зрения предметной области изменения наборов кортежей всех таблиц,
   * реализации выходных документов (регламентных отчетов).
4. Провести тестирование представлений и процедур.

(в отчете пишем уже результат работы - проектирования)

## Сценарий создания таблиц для СУБД PostgreSQL-14

### Таблица ```Depatment```

(можете расставить комментарии, как это сделалано здесь)

```sql
CREATE TABLE IF NOT EXISTS public.department
(
    "number" uuid NOT NULL DEFAULT gen_random_uuid(),   -- порождается автоматом при добавлении,
                                                        -- если не указан
    name text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Department_pkey" PRIMARY KEY ("number") -- первичный ключ
    -- по идее надо было добавить UNIQUE на name еще (см. далее)
)

-- Далее идет настройка владения таблицей и ее вербальное описание

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.department
    OWNER to dbstudent;

COMMENT ON TABLE public.department
    IS 'Department of an organization';
```

### Таблица ```Employee```

```sql
CREATE TABLE IF NOT EXISTS public.employee
(
    personname character varying(30) COLLATE pg_catalog."default",
    birthdate date,
    email character varying(30) COLLATE pg_catalog."default",
    jobposition character varying(30) COLLATE pg_catalog."default",
    tablenumber integer NOT NULL, -- естественное ограничение для первичного ключа
    department uuid NOT NULL,     -- ограничение, недозволяющее сотруднику болтаться вне отдела
    CONSTRAINT employee_tablenumber_pk PRIMARY KEY (tablenumber), -- первичный ключ
    CONSTRAINT empl_dep_fk FOREIGN KEY (department)
        REFERENCES public.department ("number") MATCH SIMPLE      -- внешний ключ на "Depatment"
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.employee
    OWNER to dbstudent;
```

Таким образом, мы представили отношение ```1:N```. Теперь будем называть таблицу ```Depatment``` "основной",
а таблицу ```Employee``` "зависимой", т.к. она ссылается полем ```department``` на основную таблицу.

Вообще, в терминологии тут бывает путаница.  Например, если удалять записи из ```Department```, то надо сначала проверить, еслть ли в ```Employee``` сотрудники, привязанные к удаляемому отделу. Получается, что результат удаления записи зависит от содержимого ```Employee```, т.е. ```Department``` зависит от ```Employee```.
С другой стороны, если мы добавляем сотрудника, то его надо добавлять в уже существующий отдел, т.е. манипуляция над ```Employee``` зависит от ```Depatment```.

Разбирайтесь внимательно в каждом конкретном случае, что имеется ввиду под *зависимостью*.

## Встроенные процедуры для таблицв ```Department``` для СУБД PostgreSQL-14

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
-- PROCEDURE: public.INSERT_EMPLOYEE(character varying, date, character varying, character varying, integer, uuid)

-- DROP PROCEDURE IF EXISTS public."INSERT_EMPLOYEE"(character varying, date, character varying, character varying, integer, uuid);

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
-- tablenumber is the primary key, so it is not updatable
-- so for the department number being a foreign key
-- add some more

	IF EXISTS (SELECT tablenumber FROM Employee WHERE tablenumber=mtablenumber)
	THEN
		RAISE EXCEPTION 'There is Employee with table number %. No insertion wasperformed!', mtablenumber;
	END IF;
	IF EXISTS (SELECT tablenumber FROM Employee WHERE mpersonname = personname)
	THEN
		RAISE EXCEPTION 'There is an employee with the same name';
	END IF;
	IF NOT EXISTS (SELECT "number" from department WHERE "number"=mdepartment)
	THEN
		RAISE EXCEPTION 'There is no department identified by %.', mdepartment;
	END IF;
	IF mtablenumber = -1
	THEN
		INSERT INTO public.employee
			(personname, birthdate, email, jobposition, tablenumber, department)
		VALUES
			(mpersonname, mbirthdate, memail, mjobposition, nextval('tablenumber_seq'), mdepartment);
	ELSE
		INSERT INTO public.employee
			(personname, birthdate, email, jobposition, tablenumber, department)
		VALUES
			(mpersonname, mbirthdate, memail, mjobposition, mtablenumber, mdepartment);
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
There is Employee with table number 501. No insertion was performed!
CONTEXT:  функция PL/pgSQL "INSERT_EMPLOYEE"(character varying,date,character varying,>
Time: 0.003s
```

## Встроенные процедуры для порождения выходных документов

Первый выходной документ (отчет) - выдать количество сотруднков в каждом отделе и всех
сотруднков отдела. Количество сотрудников будем дублировать в каждой строке, при составлении текста
отчета эту цифру можно взять в любой строке, а столбец не выводить.

Запрос реализован в виде ```plpgsql```-функции, возвращающую таблицу.  Такая функция используется в
запросе ```SELECT``` (см. в разделе тестирования примеры использования).

```plpgsql
CREATE OR REPLACE FUNCTION public."COUNT_EMP_IN_DEPS"(
	filter boolean,
	mdepartment uuid)
    RETURNS TABLE (
		personname character varying(30),
    	birthdate date,
    	email character varying(30),
    	jobposition character varying(30),
    	tablenumber integer,
    	department uuid,
    	"name" text,
		countemps bigint
	)
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
	IF filter
	THEN
		RETURN QUERY
		SELECT
			e.personname,
    		e.birthdate,
    		e.email,
    		e.jobposition,
    		e.tablenumber,
    		e.department,
    		e."name",
			ce.countemps
		FROM emp_in_dep e,
			(SELECT count(e.tablenumber) as countemps FROM emp_in_dep e
			 WHERE e.department=mdepartment GROUP BY e.department) as ce
			WHERE e.department=mdepartment;
	ELSE
		RETURN QUERY
		SELECT
			e.personname,
    		e.birthdate,
    		e.email,
    		e.jobposition,
    		e.tablenumber,
    		e.department,
    		e."name",
			ce.countemps
		FROM emp_in_dep e JOIN
			(SELECT count(e.tablenumber) as countemps, e.department as dn FROM emp_in_dep e
			 GROUP BY e.department) as ce
		ON ce.dn=e.department;
	END IF;
END
$BODY$;

ALTER FUNCTION public."COUNT_EMP_IN_DEPS"(boolean, uuid)
    OWNER TO dbstudent;
```


### Тестирование первого выходного документа

Таблица дополнена данными, чтоб в одном из отделов было несколько работников.

```text
dbstudent@(none):test> select * from emp_in_dep;
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+
| personname       | birthdate  | email           | jobposition | tablenumber | department                           | name |
|------------------+------------+-----------------+-------------+-------------+--------------------------------------+------|
| Jud Lee 4-th     | 1978-01-01 | jud@example.com | janitor     | 503         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT |
| Jud Lee 1        | 1978-01-01 | jud@example.com | janitor     | 502         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT |
| Jud Lee the 4-th | 1977-02-01 | jud@example.com | Janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT |
| Samanta Fox 4    | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT |
| Suzy             | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db8982d | IMIT |
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+
SELECT 5
Time: 0.007s
```

Запрос по одному из отделов

```text
dbstudent@(none):test> select * from "COUNT_EMP_IN_DEPS"(True, UUID('b9ccd2e0-5e75-4740-86df-7a050071de7f'));
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------+
| personname       | birthdate  | email           | jobposition | tablenumber | department                           | name | countemps |
|------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------|
| Samanta Fox 4    | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee the 4-th | 1977-02-01 | jud@example.com | Janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee 1        | 1978-01-01 | jud@example.com | janitor     | 502         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee 4-th     | 1978-01-01 | jud@example.com | janitor     | 503         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------+
SELECT 4
Time: 0.008s
```

Запрос по все разделам.

```text
dbstudent@(none):test> select * from "COUNT_EMP_IN_DEPS"(False, UUID('b9ccd2e0-5e75-4740-86df-7a050071de7f'));
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------+
| personname       | birthdate  | email           | jobposition | tablenumber | department                           | name | countemps |
|------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------|
| Samanta Fox 4    | <null>     | <null>          | <null>      | 40          | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee the 4-th | 1977-02-01 | jud@example.com | Janitor     | 501         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee 1        | 1978-01-01 | jud@example.com | janitor     | 502         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Jud Lee 4-th     | 1978-01-01 | jud@example.com | janitor     | 503         | b9ccd2e0-5e75-4740-86df-7a050071de7f | IMIT | 4         |
| Suzy             | <null>     | <null>          | <null>      | 401         | 285242ac-fa97-4ccb-b56f-d8651db8982d | IMIT | 1         |
+------------------+------------+-----------------+-------------+-------------+--------------------------------------+------+-----------+
SELECT 5
Time: 0.009s
```

### Тестирование работы запроса для  второго документа

(делается аналогично, результат в отчет)


# Лабораторная работа 3 "Разработка клиентского приложения на основе Django"

Одним из популярным подходом к разработке клиентского приложения к серверной части
информационной системы является интернет-приложение.  Основное приемущество использования
интернет-приложений - это централизованное управление приложением (одна точка доступа всем клиентам,
установка, обновление, и т.п.), пользователю достаточно использовать только браузер для решения
всех задач, и т.д. Однако, есть и некоторые проблемы, например, необходимо решать задачу разграничения
прав доступа пользователей и другие задачами защиты информации.

Стандартным методом взаимодействия Django с сервером
является *объектно-реляционное отображение* (Object-Relational Mappingб ORM).  На первом
этапе создаются классы Python, представляющие модели, потем, исходя из структуры моделей и
отношений между ними, автоматизируется большинство операций на сервере, включая выполнение
запросов ```SQL```, ```DDL```, ```DML```.  Использование ORM позволяет автоматизировать рутинные
операции с данными на сервере, автоматически создавать оптимизированные запросы в зависимости от
структуры объектных данных в так называемой *сессии*.  Получается, что с т.з. времени выполнения
запросов использование ORM повышает производительность взаимодействия с БД, но управление базой данных
согласно семантики предметной области, выражаемой встроенными процедурами (из Лабораторной работы 2), в
ORM весьма затруднительно.

В связи с тем, что в классическом арианте реализации клиент-серверных инфорационных систем, все изменения
БД реализуется через встроенные процедуры.  Будем использовать Django в нестандартном для него режиме взаимодействия с сервером в большинстве случаев.

## Первоначальные этапы развертывания Django-приложения

Следующие этапы необходимо выполнить перед тем, как переходить к работе с БД:

1. Установить Django
2. Создать приложение (сервер Django обеспечивает работу нескольких приложений, в частности БД пользователей).
3. Импорт структуры БД (в нашем случае).
4. Миграция - адаптация данных Django в БД сервера.

## Импорт структуры БД в модели Django

Как сказано выше по стандарту Django сначала создаются модели объектов БД, затем автоматически порождаются таблицы на сервере.  В нашем случае сначала была создана БД, теперь надо ее проанализировать и создать модели.
В Django для выполнения этой задачи есть утилита

```bash
$ python manage.py inspectdb > models.py # в папке приложения вашего.
```
Затем производится миграция (см. документацию по Django.).

Полученные модели отличаются тем, что их нельзя затем улучшать.  Но нам в проекте это и не нужно.

```python
from django.db import models

# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True (1)
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Department(models.Model):
    number = models.UUIDField(primary_key=True)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = "department"


class Employee(models.Model):
    personname = models.CharField(max_length=30, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    email = models.CharField(max_length=30, blank=True, null=True)
    jobposition = models.CharField(max_length=30, blank=True, null=True)
    tablenumber = models.IntegerField(primary_key=True)
    department = models.ForeignKey(
        Department, models.DO_NOTHING, db_column="department"
    )

    class Meta:
        managed = False
        db_table = "employee"
```

В строке, помеченной (1) указывается, что надо проверить, что в каждой импортированной таблице
только одино ключевое поле.

## Подключение таблиц к подсистеме администрирования

Интерфейс администрирования позволяет добавлять, удалять, изменять данные в таблицах стандартным для
Django способом.  Интерфейс удобно использовать для задач отдаки.

```python
from django.contrib import admin

from .models import Department, Employee

# Register your models here.


admin.site.register(Employee)
admin.site.register(Department)
```

## Отображение URL на представления (view)

```python
#file: urls.py

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="dep_index"),    # Домашняя страница приложения
    path("department/<str:number>/", views.emp_index, name="emp_index"),  # Перечень отделов
    path("employee/<int:tablenumber>/", views.emp_view, name="emp_view"), # Просмотр/редактирование сотрудника
    path("employee-rm/<int:tablenumber>/<int:confirm>", views.emp_rm, name="emp_rm"), # Удаление сотрудника
    path("employee/<int:tablenumber>/store/", views.emp_store, name="emp_store"), # выполнение обновления/добавления
    path("employee-add/<str:depno>/", views.emp_new, name="emp_new"),      # Добавление сотрудника
    path("department-report/<str:depno>/", views.dep_rep, name="dep_rep"), # Отчет по отделу (два варианта)
    # . . . . .
]
```

Задача данного файла оотбражать URL на процедуру обработки запроса (с вохможными дополнительными параметрами) - представление (View). Как правило представления создаются для страниц - интерфейсов пользователя и процедур манипуляции данными (в данном примере, ```views.emp_store``` и ```views.emp_rm```). Дополнительные параметры извлекаются из URL при помощи регулярных выражений и преобразования типов. Например, ```<int:tablenumber>``` извлекается в пересенную ```tablenumber``` целого типа, если удалось распознать последовательность цифр и знак между двумя символами ```/```.


## Представления интерфейса таблиц/объектов БД

Модель представления объектов предметной области, реализованная в Django, близка к Model-View-Presenter (MVP) (https://ru.wikipedia.org/wiki/Model-View-ViewModel). Бользователь видит интерфейс, т.е. HTML-страницу, сгенерированную ```view```-функцией. При нажатии кнопок ```submit``` осуществляется запуск ```view```-функций Python, модифицирующих модель (Model). Таким образом, ```veiew```-функция играют роль Presenter. А сгенерированная страница, которую видит пользователь - это View в модели MVP.

Истолрически наиболее известный (самый "ранний") шаблон проектирования пользовательского инерфейса - это MVC (Model-View-Controller) (https://ru.wikipedia.org/wiki/Model-View-Controller). Роли компонентам принято назначать согласно этому шаблону, однако название ```view``` у ```view```-функций получается опять неправильным в Django, т.к. они играют роль и Controller и подсистемы порождения View.

Есть еще один шаблон проектирования - MVVM (Model-View-ViewModel) (https://ru.wikipedia.org/wiki/Model-View-ViewModel). В нем предполагается, что интерфейс пользователя взаимодействует с виртуальным представлением модели объекта (ViewModel), представленного в интерфейсе (например, совокупности данных Отдел-Сотрудник), а уже этот ViewModel-объект взаимдействует с моделями предметной области (кортежами в БД, например, или представлением кортежей в виде экземпляров ORM). Но в случае с Django так делать не принято, т.е. создавать это промежуточный слой ViewModel.

В связи с этим обвиними разработчиков Django виноватыми за путаницу с шаблонами проектирования, ну, конечно, допустим, что, вероятно, мы не в курсе их теоретических изысканий новых шаблонов проектирования...

### Файл обработиков запросов ```views.py```

Преабула файла - импорт используемых библиотек.

```python
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.utils import InternalError

from .models import Department, Employee

from django.db import connection
from django.contrib import messages
from recordclass import recordclass
import inspect

```

Собственно представления (обработчики запросов). Первый - выводит на основной странице приложения список отделов. Выбирая указателем мыши отдел, можно осуществить переход на просмотр списка сотрудников этого отдела.

```python
# Create your views here.

def index(request):
    """Основная страница приложения по адресу /emp/
    Здесь надо сделать таблицу - перечень отделов
    """
    departments = Department.objects.all() # Используем средства Django ORM
    context = {"departments": departments} # данные для шаблона страницы

    TEMP = "emp/departments.html"          # HTML-шаблон страницы

    rc = render(request, TEMP, context)    # Подставляем данные в шаблон, генерируем страницу

    return rc
```

Представление ```index``` содержит только стандартный первый параметр ```request```, содержвщий полную информацию о запросе с вебраузера клиента. Дополнительных пераметров не предусмотрено, т.к. домашняя страница приложения ```emp``` не подразумевает какого-либо коннтекста, т.е. эта страница предназначена для ввода самого первого действия пользователя.

В данном интерфейсе список отделов представляется в виде таблицы. В каждую стоку добавляются кнопки перехода на формы, реализующиеоперации с данными таблицы отделов. После таблицы втавлена кнопка добавления нового отдела. Данным файлом используется общий для всех последующих фалов интерфйесов  шаблон, в функции кторого входит отображение сообщений об шибках и успешно выполненных операциях.

```html
<!-- emp/departments.html -->
{% extends "base.html" %}
{% block content %}

{% if departments %}
<table class="table table-striped">
    <thead>
        <tr>
            <th scope="col">Название</th>
            <th scope="col"></th>
            <th scope="col"></th>
        </tr>
    </thead>
    <tbody>
  {% for d in departments %}
  <tr>
    <td><a href="/emp/department/{{ d.number }}/">{{ d.name }}</a></td>
    <td>
      <div class="btn-group" role="group" aria-label="bg-editing">
        <a class="btn btn-primary"
           href="/emp/department/{{ d.number }}">Редактировать</a>
        <a class="btn btn-danger"
           href="/emp/department-rm/{{ d.number }}/0">Удалить</a>
      </div>
    </td>
    <td><a href="/emp/department-report/{{ d.number }}/" class="btn btn-secondary">Отчет</a></td>
  </tr>
  {% endfor %}
  <tr>
      <td></td>
      <td><a href="/emp/department-report/0/" class="btn btn-secondary">Отчет по всем отделам</a></td>
      <td><a href="/emp/department-add/" class="btn btn-success">Добавить отдел</a></td>
  </tr>
  </tbody>
</table>
{% else %}
<p>Отделы еще не заданы! {{ departments }}</p>
{% endif %}
{% endblock %}

```

(вставить примеры скринов)


Перечень сотрудников отдела определяется ```UUID```-номером отдела, который является дополнительным параметром, получаемым из интерфейса, ```HTML```-страницы.

```pyhon
def emp_index(request, number):
    """Страница списка сотрудников отдела"""
    department = get_object_or_404(Department, number=number) # получить отдел по номеру, либо
                                                              # переход на страницу 404
    employees = Employee.objects.filter(department__exact=department) # Выбор сотрудников отдела
    context = {"employees": employees, "department": department}
    return render(request, "emp/emplist.html", context)
```

Структура интерфейса отображения списка сотрудников. Отличие от предыдущего файла интерфейса - измененная структура отображения данных о сотруднике, реализованная в соответствии со структурой данных таблицы ```Employee```.

```html
<!-- emp/emplist.html -->
{% extends "base.html" %}
{% block content %}

{% if department %}
{% if employees %}

<table class="table table-striped">
    <thead>
        <tr>
            <th scope="col">#</th>
            <th scope="col">Фио</th>
            <th scope="col"></th>
        </tr>
    </thead>
    <tbody>
  {% for e in employees %}
  <tr><td>{{e.tablenumber}}</td>
      <td>
      <a href="/emp/employee/{{ e.tablenumber }}/">{{ e.personname }}</a>
      </td>
      <td>
          <div class="btn-group" role="group" aria-label="bg-editing">
              <a class="btn btn-primary"
                 href="/emp/employee/{{ e.tablenumber }}">Редактировать</a>
              <a class="btn btn-danger"
                 href="/emp/employee-rm/{{ e.tablenumber }}/0">Удалить</a>
          </div>
      </td>
  </tr>
  {% endfor %}
  <tr>
      <td></td><td></td>
      <td><a href="/emp/employee-add/{{ department.number }}" class="btn btn-success">Добавить сотрудника</a></td>
  </tr>
  </tbody>
</table>

{% else %}
<p> Список сотрудников пока пуст... </p>
<a href="/emp/employee-add/{{ department.number }}" class="btn btn-success">Добавить сотрудника</a>
{% endif %}
{% else %}
<p>Отдел не найден!</p>
{% endif %}

{% endblock %}
```

Просмотр и редактирование сотрудника - отображение формы.

```pyton
def emp_view(request, tablenumber):
    """Форма - редактор сотрудника"""
    employee = Employee.objects.get(tablenumber__exact=tablenumber)
    department = Department.objects.get(number__exact=employee.department.number)
    context = {"employee": employee, "department": department}
    return render(request, "emp/empview.html", context)
```

Собственно HTML-структура формы для отображения и редактирования данных о сотруднике. Необходимо обратить внимание на строку, помеченную (1). В этой строке производится привязка формы к сессии пользователя - вариант защиты информации: система препятствует использованию HTML формы другими соединениями/сайтами для помещения данных в БД. Если удалить эту строку, будет выдаваться сообщени о невозможности обработать данные формы.

```html
<!-- emp/empview.html -->
{% extends "base.html" %}
{% block content %}

{% if employee %}
{% if department %}

<form action="{% url 'emp_store' employee.tablenumber %}" method="post">
    {% csrf_token %}  <!-- (1) -->
    <legend><h1>Сотрудник отдела '{{ department.name }}' </h1></legend>
    {% if error_message %}<p><strong>{{ error_message }}</strong></p>{% endif %}
    <div class="form-group">
        <label for="personname">ФИО:</label>
        <input type="text" name="personname"
               class="form-control"
               placeholder="Введите ФИО"
               id="personname" value="{{ employee.personname|default:'' }}"/>
    </div>
    <div class="form-group">
        <label for="birthdate">Дата рождения ГГГГ-ММ-ДД:</label>
        <input type="text" name="birthdate"
               class="form-control"
               placeholder="Введите дату рождения"
               id="birthdate" value="{{ employee.birthdate|default:''|date:"Y-m-d" }}"/>
    </div>
    <div class="form-group">
        <label for="email">Email-адрес:</label>
        <input type="text" name="email"
               class="form-control"
               placeholder="person@example.com"
               id="email" value="{{ employee.email|default:'' }}"/>
    </div>
    <div class="form-group">
        <label for="jobposition">Должность:</label>
        <input type="text" name="jobposition"
               class="form-control"
               placeholder="Вахтер"
               id="jobposition" value="{{ employee.jobposition|default:'' }}"/>
    </div>
    <input type="hidden" name="tablenumber" value="{{ employee.tablenumber|default:'' }}"/>
    <input type="hidden" name="depatment" value="{{ employee.department.number|default:'' }}"/>
    <input type="hidden" name="depno" value="{{ department.number|default:'' }}"/>
    <input class="btn btn-primary" type="submit" value="Сохранить"/>
</form>
{% else %}
<p> Что-то не так с данными по отделу сотрудника. Обратитесь к администратору. </p>
{% endif %}
{% else %}
<p>Сотрудник не найден!</p>
{% endif %}

{% endblock %}

```

Форма добавления нового сотрудника - отображение формы. Отличие от предыдущего представления изменен процесс порождения данных контекста: сотрудник - новый пустой объект, данные отдела получаются из параметра. Интерфейс пользователя реализован при помощи предыдущего HTML-шаблона.

```python
def emp_new(request, depno):
    """Форма - добавления нового сотрудника"""
    employee = Employee(tablenumber=0)
    department = Department.objects.get(number__exact=depno)
    context = {"employee": employee, "department": department}
    return render(request, "emp/empview.html", context)
```

Процедура добавления/изменения сотрудника, которая запускается из вышеуказанных форм ввода данных. По идее, эта процедура играет роль ```Controller```, еслирассматривать интерфейс в рамках модели MVC (https://ru.wikipedia.org/wiki/Model-View-Controller). Собственно, здесь видно, что модели интерфейса Django трудно однозначно отнести к MVC, MVVM, MVP (https://ru.wikipedia.org/wiki/Model-View-Presenter) и другим вариантам реализации.

```python
def emp_store(request, tablenumber):
    """Процедура сохранения данных сотрудника"""
    flds='personname birthdate email jobposition tablenumber'
    # employee = Employee.objects.get(tablenumber__exact=tablenumber)
    vls = [request.POST[k] for k in flds.split()]
    # employee.personname = request.POST["personname"]
    # employee.save()
    with connection.cursor() as cursor:
        if tablenumber!=0:
            try:
                cursor.execute('call "UPDATE_EMPLOYEE"(%s,%s,%s,%s,%s);',vls)
                cursor.execute('commit;')
                messages.success(request,"The employee has been updated!")
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)
        else:
            try:
                depmo = request.POST["depno"]
                vls[4] = -1
                cursor.execute('call "INSERT_EMPLOYEE"(%s,%s,%s,%s,%s,%s);',vls+[depmo])
                cursor.execute('commit;')
                messages.success(request,"The employee has been added!")
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)

    return HttpResponseRedirect(reverse("dep_index"))
    # return HttpResponseRedirect(reverse("emp_view"), args=(tablenumber,))
```

Данное представление поддерживает работу формы удаления. Отличие от предыдущих - двухэтапный процесс: 1) вывод данных о сотруднике и 2) подтверждение удаления. Фаза процесса определяется параметром ```confirm```.

```python
def emp_rm(request, tablenumber, confirm):
    """Форма-запрос на подтверждение удаления сотрудника """
    if confirm!=1:
        employee = Employee.objects.get(tablenumber__exact=tablenumber)
        department = Department.objects.get(number__exact=employee.department.number)
        context = {"employee": employee, "department": department}
        return render(request, "emp/emprm.html", context)
    else:
        with connection.cursor() as cursor:
            try:
                cursor.execute('call "DELETE_EMPLOYEE"(%s);', (tablenumber,))
                cursor.execute('commit;')
                messages.success(request,"The employee has been deleted!")
                return HttpResponseRedirect(reverse("dep_index"))
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)
```

Функция, представляющая результаты запроса ```SELECT ...``` в виде набора экземпляров класса.

```python
def namedtuplefetchall(cursor, fields = [], f=None):
    """
    Return all rows from a cursor as a namedtuple.
    Assume the column names are unique.
    """
    desc = cursor.description
    nt_result = recordclass("Result", [col[0] for col in desc] + fields)
    vs = [None] * len(fields)
    def _(row):
        ntr = nt_result(*list(row)+vs)
        if callable(f):
            return f(ntr)
        else:
            return ntr
    return [_(row) for row in cursor.fetchall()]
```

## Порождение выходных документов

Вывод отчета по количеству сотруднков в отделе/отделах. Вариант отчета зависит от параметра ```depno```. Перед выводом в HTML-шаблон экземпляры дополнительно размечаются - указывается кортеж, идущий последним в списке кортежей (данных о сотруднике), относящихся к одному отделу.

```python
def dep_rep(request, depno):
    """Report 1 generator for a departement or departments.
    If depno == 0 generate for all the departments
    """
    filter = False
    department = None
    try:
        department = Department.objects.get(number__exact=depno)
        filter = True
    except ValidationError:
        depno="285242ac-fa97-4ccb-b56f-000000000000" # невозможный UUID
        pass

    with connection.cursor() as cursor:
        cursor.execute('SELECT * from "COUNT_EMP_IN_DEPS"(%s,%s)', (filter,depno))
        def iid(x):
            return x

        def f(r):
            global pd

        result = namedtuplefetchall(cursor, ["last"], iid)
        if result:
            pd = result[0].department
            ll = len(result)-1
            for i,r in enumerate(result):
                r.last=False
                if pd != r.department:
                    result[i-1].last = True
                    pd = r.department
                if i==ll:
                    r.last = True
        context = {"result":result, "department":department}
        return render(request, "emp/deprep.html", context)
```

Шаблон представления реультата отчета (не зависит от варианта Выходного документа 1). Контекстом документа является результат выполнения запроса (встроенной функции ```"COUNT_EMP_IN_DEPS"(...)```). Встроенная ```pgplsql```-функция в PostgreSQL выполняется в запросе ```SELECT ... FROM <вызов функции> ...``` и, соответственно, возвращает таблицу. Как было сказано чуть выше, таблица преобразуется в набор классов, что позвояет с коретжами обращатся аналогично моделям Djabgo внутри HTML-шаблона. После помеченных кортежей (поле ```last```) добавляется строка с итогом по отделу (код между метками (*)).

```html
<!-- emp/deprep.html -->
{% extends "base.html" %}
{% block content %}

{% if result %}

{% if department is not None %}
<H>Отчет по отделу {{ depatment.name }}</H>
{% else %}
<H>Отчет по всем отделам</H>
{% endif %}

<table class="table table-striped">
    <thead>
        <tr>
            <th scope="col">#</th>
            <th scope="col">ФИО</th>
            <th scope="col">Дата рождения</th>
            <th scope="col">Email</th>
            <th scope="col">Должность</th>
            {% if department is None %}
            <th scope="col">Отдел</th>
            {% endif %}
        </tr>
    </thead>
    <tbody>
  {% for e in result %}
  <tr><td>{{e.tablenumber}}</td>
      <td>
      <a href="/emp/employee/{{ e.tablenumber }}/">{{ e.personname }}</a>
      </td>
      <td>
        {{e.birthdate}}
      </td>
      <td>
        {{e.email}}
      </td>
      <td>
        {{e.jobposition}}
      </td>
      {% if department is None %}
      <td>{{e.name}}</td>
      {% endif %}
  </tr>
  {% if e.last %} <!-- (*) -->
  <tr>
    <td></td>
    <td><strong>Всего</strong></td>
    <td></td>
    <td></td>
    <td>{{e.countemps}}</td>
    {% if department is None %}
    <td></td>
    {% endif %}
  </tr>
  {% endif %}     <!-- (*) -->
  {% endfor %}
  </tbody>
</table>

{% else %}
<p> Пустой отчет, видимо нет сотрудников в отделе ... </p>
{% endif %}
{% endblock %}
```

(скрин)

## UML-модели полученной клиентской подсистемы

(USE-case - диаграма)

(Диаграмма "классов")

(необходимо мне доделать, а вам сделать.)

# Заключение

В результате выполнения ряда лабораторных работ по курсу "Базы данных" решены следующие задачи

1. Изучена предметная область реляционных баз данных;
2. Представлена в виде информационной модели задача лабораторной работы (вариант ХХ). Для этого

   * осуществлен анализ вербального (словесного) представления задачи,
   * разработана ER-диаграмма представления данных для реляционной БД,
   * преобразование ER-диаграммы в физическую модель БД,
   * представлены варианты начального заполнения таблиц БД данными;

3. Разработана (сгенерирована и доработана) структура БД (набор запросов DDL);
4. Осуществлен ввод первоначальных данных;
5. Разработаны и протестированы представления, встроенные процедуры и функции на сервере (серверная част гипотетической инфорационной системы);
6. Создана клиентская подсистема на основе Django-4.0, позволяющая получать входные данные от пользователя и производить внесение изменений в

# Ипользованные ресурсы
(это не надо в отчет, пример оформления не соответствует ГОСТ)

0. Zerotier VPN https://www.zerotier.com/ (номер сети не публикую здесь)
1. PgAdmin4 - http://192.168.191.46:8888/ (пользователь ```stud@isu.ru```)
2. Терминальный доступ - ```ssh 192.168.191.46 -l isu```
3. Удобный консольный клиент ```pgcli <dbstudent или ваша БД> dbstudent```. Пример ```pgcli test dbstudent```.
4. Проект https://github.com/stud-labs/django-db/ (Django 4.0)
5. Документация по Django - https://docs.djangoproject.com/en/4.2/
6. Генератор проектов Django - https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html
7. Модель представления (публикации) объектов MVVM - https://ru.wikipedia.org/wiki/Model-View-ViewModel
8. UMLET - система для рисования диаграмм UML - https://www.umlet.com/
