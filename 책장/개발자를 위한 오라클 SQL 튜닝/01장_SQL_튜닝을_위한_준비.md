# 1장. SQL 튜닝을 위한 준비

> 📖 출처: **개발자를 위한 오라클 SQL 튜닝** (이경오 저)
> 📄 PDF 페이지: 12 ~ 19

---

4 
l l 
하
 
4 
I ‘ 
때
 
이
 
SQL 튜닝을위한준비 
SQL 튜닝 실습을 진행하기 위해서는 다음의 3가지가 필요합니다 
• 대용량 데이터를 저장할 
저장소(테이블스페이스)와 해당 저장소를 사용할 
사용자 계정 
• SQL문만으로 대용량의 테이블을 구성하는 방법 
• 오라클의 통계정보를 분석하는 방법 
이번 장에서 이 3가지에 대해 자세히 다루게 됩니다. 이번 장을 완벽히 이해한 후 
본격적인 튜닝 학습을 시작하기 바랍니다 
R뀔l 테이블 스페이스 및 계정 생성 
1.1.1 테이블 스떼이스 생성 
테이블 스페이스Table Space는 테이블을 저장하는 공간입니다. 오라클은 테이블 스 
페이스 내에 테이블을 저장하며 테이블에는 데이터가 저장됩니다. 실습을 진행하 
기 위해서 별도의 테이블스페이스를생성합니다. 테이블스페이스의 생성 방법은 
다음과같습니다. 
(1) 관리자 권한으로 로그인 
‘sysdba’ 권한으로 접속합니다. 
sqlplus "/as sysdba“ 
1 SQL 튜닝을 위한준비 - 013

---
<!-- PDF p.13 -->

(2) 테이블 스페이스 생성 
‘dbmsexpert’라는 오라클 인스턴스에 총 4GB 용량의 테이블 스페이스를 생성 
하였습니다. 
CREATE TABLESPACE DBMSEXPERT DATA 
DATAFILE 'C:\app\dbmsexpert\oradata\orcl \DBMSEXPERT DATA.DBF' SIZE 4G 
AUTOEXTEND ON NEXT 1G MAXSIZE UNLIMITED 
LOGGING 
ONLINE 
PE타R째MAN메ENT 
EXTENT MANAGEMENT LOCAL AUTOALLOCATE 
BLOCKSIZE 8K 
SEGMENT SPACE MANAGEMENT AUTO 
FLASHBACK ON; 
(3) 임시 테이블 스페이스 생성 
‘dbmsexpert’라는 오리클 
인스턴스에 총 1GB 용량의 임시 테이블 스페이스를 
생성하였습니다. 
CREATE TEMPORARY TABLESPACE DBMSEXPERT TMP 
TEMPFILE ’C \app\dbmsexpert\oradata\orcl\DBMSEXPERT TMP.DBF ’ SIZE 1G 
AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED; 
1.1.2 사용자 져l정 생성 
앞에서 생성한 테이블 스페이스를 기본 설정으로 하는 오라클 계정을 생성합니 
다.생성방법은다음과같습니다. 
(1 ) 관리자 권한으로 로그인 
‘sysdba’ 권한으로 접속합니다. 
sqlplus "/as sysdba" 
01 -

---
<!-- PDF p.14 -->

(2) 사용자계정생성 
‘DBMSEXPERT _DATA ’ 와 ‘DBMSEXPERT_TMP’ 테이블 스페이스를 
Default로 하는 ‘DBMSEXPERT’ 계정을 신규로 생성하였습니다. 지금부 
터 ‘DBMSEXPERT’ 계정으로 로그인하여 생성하는 테이블 및 인텍스는 모두 
‘DBMSEXPERT_DATA’에 생성됩니다. 해당 계정으로 작업하다 임시 영역이 
필요한 경우에는 ‘DBMSEXPERT_TMP’ 영역을 사용하게 됩니다. 
CREATE USER DBMSEXPERT IDENTIFIED BY DBMSEXPERT 
DEFAULT TABLESPACE DBMSEXPERT DATA 
TEMPORARY TABLESPACE DBMSEXPERT TMP 
PROFILE DEFAULT 
ACCOUNT UNLOCK; 
(3) 권한주기 
‘DBMSEXPERT’ 계정에 권한을 
주었습니다. 
GRANT RESOURCE TO DBMSEXPERT; 
GRANT CONNECT TO DBMSEXPERT; 
GRANT CREATE VIEW TO DBMSEXPERT; 
GRANT CREATE SYNONYM TO DBMSEXPERT; 
(4) 샘성된 계정으로 접속 
생성된 계정으로 오라클에 접속합니다 
훌웹l 실습테이블구성 
1.2.1 NOLOGGING 모드 설정 
오라클에서 테이블에 NOLOGGING 모드를 설정하면 해당 테이블에 INSERT 작업 
시 Redo 로그 작업을 최소화합니다. 따라서 대용량의 데이터를 INSERT 작업할 
1 SQL 튜닝을 위한준비 - 015

---
<!-- PDF p.15 -->

때 데이터 입력 시간을줄일수있습니다 사용법은다음과같습니다 대용량의 데 
이터를 INSERT 전에 해당 테이블을 NOLOGGING 모드로 설정합니다 
ALTER TABLE 테이블영 NOLOGGING; 
1.2.2 APPEND 힌트 
오라클이 테이블에 데이터를 입력할 때 다음 단계를 거치게 됩니다. 
1) 데이터 버머 캐시Dala ßuffer Cache를 경유합니다. 
2) 테이블 세그먼트의 비어 있는 블록Free Blod을 
검색합니다. 
3) 비어 있는블록에 데이터를저장합니다 
APPEND 힌트를 사용한다면 세그먼트의 HWMHigh \\'aler ^lark 바로 뒤부터 데이터 
를 입력하게 되는데，HWM은 세그먼트의 가장 끝이라고 이해하시면 됩니다. 또 
한， 데이터 버퍼 캐시를 경유하지 않고 바로 데이터를 저장하게 되므로 데이터의 
입력시간을단축할수있습니다. 
APPEND 힌트를 사용하려면 다음과 같이 INSERT 바로 뒤에 APPEND 힌트를 입력 
합니다 
INSERT /*+ APPEND */ INTO 테이블영 
1.2.3 데이터 복제 
대용량의 테이블을구성하기 위해서는데이터 복제 기법을정확히 알아야합니다. 
카티션 곱 조인 (Cartesian Product Join) 
N건의 데이터로 구성된 
‘A’라는 테이블과 M건의 데이터를 가진 
‘B’라는 테이블 
을 아무런 조인 조건 없이 조인하면 
‘N건 xM건’의 데이터를 출력하게 됩니다. 
016 -

---
<!-- PDF p.16 -->

다음 예제에서 테이블 
A에 100건， 테이블 
B에 1，000건의 데이터가 있다고 가정 
하면， 총 
10만 
건(100건 x 1 ，000건 = 100 ，000건)의 결과 건수가 나오게 됩니다. 
SELECT * FROM A, B; 
계층형쿼리사용 
오라클에서 사용하는 계층형 쿼리를 이용하여 인위적으로 여러 개(N)의 행을 출 
력할수 
있습니다. 다음 예제는 총 
1.000개의 행을출력하게 됩니다. 
SELECT * FROM DUAL CONNECT BY LEVEL <= 1000; 
카티션 곱 조인과 
계층형 쿼리의 흔용 
카티션곱조인과계층형 쿼리를혼용하면특정 테이블의 내용을복제할수있습 
니다. 다음 예제에서 테이블 
‘A’에 100건의 데이터가 있다고 가정하면， 총 
200건 
(1 00건 x 2 = 200건)의 행이 생기고 테이블 
‘A’ 의 내용을 
복제합니다. 
SELECT * FROM A, (SELECT LEVEL FROM DUAL CONNECT BY LEVEL <= 2); 
1.2.4 RANDOM 함수의 사용 
테이블구성 시 특정 값을 인위적으로 만들기 위해서 RANDOM 함수를 이용합니다. 
랜덤숫자 
다음은 랜덤 숫자를 발생시키는 예제로， 1-100까지의 숫자 중 특정 숫자를 
리턴 
합니다 기본으로 실수를 리턴하기 때문에 TRUNC 힘수로 덮어씌어 주변 정수를 
리턴하게됩니다. 
SELECT TRUNCWBMS_RANDOM.VALUE(l , 100)) FROM DUAL; 
1 SQL 튜닝을 위한 준비 01

---
<!-- PDF p.17 -->

랜덤문자열 
랜덤 문자열을 발생시키는 예제로， 대문자로 된 10자리의 랜덤 문자열을 리턴합 
니다 
SELECT DBMS_RANDOM. STRING ( 'U ‘ ι 10) FROM DUAL; 
다음 예제는 소문자로 된 10자리의 랜덤 문자열을 리턴합니다. 
SELECT DBMS_RANDOM.STRING ( 'L ’, 10) FROM DUAL; 
실행 계획 및 통계정보 생성 
1.3.1 실행 계확 
오라클의 옵티마이저Optimi ze r는 사용자가 호출한 
SQL에 대해 최적의 실행 계획을 
도출해 줍니다. 도출 기준은 
SQL문 
자체 분석과 각종 
통계정보입니다. 
실행 계획이 도출되면 해당 실행 계획대로 SQL문에 대한 연산을 수행하게 됩니 
다. 오리클의 옵티마이저는 타 DBMS보다 월등한 성능을 자랑하며 아무리 복잡 
한SQL문이라도최소한의 비용으로해당결과를도출할수 
있습니다. 
하지만 옵티마이저가 모든 SQL문에 대해서 최적의 실행 계획을 도출하는 것은 
아닙니다. 때때로 옵티마이저도 비효율적인 실행 계획을 도출하며 해당 
SQL문은 
DBMS에 과부하의 원인이 되기도 합니다. 실행 계획을 분석하여 옵티마이저가 
미처 최적화하지 못한 부분을 찾아 튜닝하는 것이 이 책의 주 목적입니다(이 책은 
SQL 기초를 다루는 책이 아니므로 실행 계획을출력하는 방법은 다루지 않았습니다). 
018 -

---
<!-- PDF p.18 -->

1.3.2 실행 겨l 확 
실행 계획 분석은 다음의 두 가지 기본 원칙을 바탕으로 
합니다. 
• Operation 항목 중 가장 오른쪽에 있는 문자열부터 수행합니다 
Operation 항목 중 가장 오른쪽에 있는 문자열이 두 개 이상이라면(즉， 같은 Depth에 있 
다면) 위에서부터 수행합니다 
디음 
SQL문에 대한 실행 계획을분석해 보겠습니다. 
SQL문 
SELECT * 
FROM 
EMP A. DEPT B 
WHERE 
A.DEPTNO 
B.DEPTNO; 
실행계획 
0 
SELECT STATEMENT 
HASH JOIN 
2 
3 
수행순서(l D 기준) 
2 •
3 •
1 •
O 
실행계획설명 
TABLE ACCESS FULL 
TABLE ACCESS FULL 
DEPT 
EMP 
7 
7 
3 
3 
2 
가로를 기준으로 가장 오른쪽에 위치한 연산이 2 번과 
3 번입니다 동일한 가로 갚이일 경우 
세로를 기준으로 위부터 시작하므로 2 번 연산이 가장 먼저 시작하고， DEPT 테이블을 테이 
블 물 스캔(TABLE ACCESS FUL L)합니다 
1 SQL 튜닝을 위한준비 
‘ 019

---
<!-- PDF p.19 -->

10 
설명 
3 
2 번과 동일하게 가로를 기준으로 가장 오른쪽에 있으면서 2 번보다 아래에 있는 
3번이 수행 
됩니다 EMP 테이블을 테이블 울 스캔(TABLE ACCESS FUL L)합니다 
가로를 기준으로 
2 번과 
3 번 바로 왼쪽에 위치한 1 번을 수행합니다 2 번과 
3 번 연산을 해시 
조인(HASH JOIN )하였습니다 옵티마이저가 DEPT 테이블과 EMP 테이블의 조인 연산은 
해시 조인이 가장 유리하다고 판단하였습니다(해시 조인에 대한 설명은 3장 2절 잠고) 
0 
가로를 기준으로 1 번보다 왼쪽에 있는 0번이 수행됩니다 SELECT절에 대한 연산을 수행합 
니다 
1.3.3 통계정보 생성 
오라클의 옵티마이저가 최적의 실행 계획을 생성하기 위해서는 통계정보가 미리 
생성되어 있어야 
합니다. 통계정보의 생성 방법은 다음과 같습니다. 
(1 ) 테이블 통계정보 생성 
EMP 테이블에 대한통계정보를 
생성합니다. 
ANALYZE TABLE EMP COMPUTE STATISTICS; 
(2) 인텍스 통계정보 생성 
PK_EMP 인텍스에 대한통계정보를 생성합니다. 
ANALYZE INDEX PK EMP COMPUTE STATISTICS; 
(3) 특정 테이블과 테이블 내의 인텍스에 대한 통계정보 생성 
EMP 테이블과 EMP 테이블이 가지고 있는 모든 인텍스에 대한 통계정보를 생성 
합니다. 
ANALYZE TABLE EMP COMPUTE STATISTICS 
FOR TABLE FOR ALL INDEXES FOR ALL INDEXED COLUMNS SIZE 254; 
020