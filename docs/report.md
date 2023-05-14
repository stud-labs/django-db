

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

## Представления интерфейса таблиц/объектов БД

(доделаю, допишу)

## Порождение выходных документов

(аналогично)

# Ипользованные ресурсы
(это не надо в отчет)

0. Zerotier VPN https://www.zerotier.com/ (номер сети не публикую здесь)
1. PgAdmin4 - http://192.168.191.46:8888/ (пользователь ```stud@isu.ru```)
2. Терминальный доступ - ```ssh 192.168.191.46 -l isu```
3. Удобный консольный клиент ```pgcli <dbstudent или ваша БД> dbstudent```. Пример ```pgcli test dbstudent```.
4. Проект https://github.com/stud-labs/django-db/ (Django 4.0)
5. Документация по Django - https://docs.djangoproject.com/en/4.2/
6. Генератор проектов Django - https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html
