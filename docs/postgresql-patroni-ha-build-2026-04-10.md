# PostgreSQL Patroni HA 구축 기록 (2026-04-10)

## 개요

구성 완료:
- `postgres01` (`192.168.50.16`) → 초기 Primary, 이후 switchover 후 Replica 예정
- `postgres02` (`192.168.50.17`) → 초기 Replica, 이후 switchover 후 Leader 승격 성공
- `luna` (`192.168.50.56`) → etcd 단일 노드 DCS
- PostgreSQL `17.9`
- OS `Oracle Linux 9.7`
- HA 매니저 `Patroni`

최종적으로 다음이 확인되었다.
- Patroni 2노드 HA 구성 성공
- Replica streaming 정상
- `patronictl switchover` 성공

---

## 1. etcd 준비

Luna 서버(`192.168.50.56`)에 etcd `v3.5.13` 설치 후 systemd 서비스 등록.

정상 확인:
```bash
etcdctl --endpoints=http://127.0.0.1:2379 endpoint health
etcdctl --endpoints=http://127.0.0.1:2379 put test/hello world
etcdctl --endpoints=http://127.0.0.1:2379 get test/hello
```

주의사항:
- 초기 설정에서 포트 `2379` 충돌이 있었음
- 클러스터 옵션을 과하게 넣지 말고 단일 노드 standalone으로 단순화해야 안정적으로 기동됨

---

## 2. PostgreSQL 사전 점검 결과

두 노드 공통:
- PostgreSQL `17.9`
- data directory: `/var/lib/pgsql/17/data`
- hba file: `/var/lib/pgsql/17/data/pg_hba.conf`
- `wal_level = replica`
- `max_wal_senders = 10`
- `hot_standby = on`
- `wal_log_hints = off` (초기값, 이후 `on`으로 변경 필요)
- `python3` 존재, `pip3` 없음

---

## 3. Patroni 설치 전 핵심 조치

### 3.1 wal_log_hints 활성화
`pg_rewind` 사용을 위해 Primary 후보 노드에서 `wal_log_hints=on` 필요.

```bash
sudo -u postgres psql -c "ALTER SYSTEM SET wal_log_hints = on;"
sudo systemctl restart postgresql-17
sudo -u postgres psql -tAc "SHOW wal_log_hints;"
```

### 3.2 pip3 설치 및 Patroni 설치
Oracle Linux 9 기준:

```bash
sudo dnf install -y python3-pip python3-devel
sudo pip3 install patroni[etcd3] psycopg2-binary
patroni --version
```

### 3.3 기존 PostgreSQL 서비스 중지 시점
Patroni 기동 직전에:

```bash
sudo systemctl stop postgresql-17
sudo systemctl disable postgresql-17
```

---

## 4. Patroni 구성 시 실제로 겪은 문제와 해결

### 4.1 `/etc/patroni/patroni.yml` 비어 있음
증상:
- Patroni 시작 실패
- `Config is empty.`

해결:
- `tee <<'EOF'` 방식으로 파일 다시 작성
- 저장 후 `head`, `wc -l`로 내용 확인

### 4.2 `postgres` 비밀번호 불일치
증상:
- Patroni가 localhost:5432 접속 시 `password authentication failed for user "postgres"`

해결:
- 실제 PostgreSQL 계정 비밀번호를 Patroni 설정과 맞춤
- 특수문자 `!` 는 bash history expansion 문제를 유발하므로 단순 비밀번호 사용 권장

권장 예시:
- `postgres` → `Pg2024@`
- `replicator` → `Rep2024@`

### 4.3 `replicator` 인증 실패
증상:
- Replica 노드에서 `replicator` 계정의 인증 실패
- Primary의 `pg_hba.conf` 에 replication 허용 부족

Primary(`.16`) 조치:
```bash
sudo -u postgres psql -c "ALTER ROLE replicator WITH REPLICATION LOGIN PASSWORD 'Rep2024@';"
echo "host replication replicator 192.168.50.17/32 md5" | sudo tee -a /var/lib/pgsql/17/data/pg_hba.conf
echo "host all postgres 192.168.50.17/32 md5" | sudo tee -a /var/lib/pgsql/17/data/pg_hba.conf
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

### 4.4 Replica 로컬 `Ident` 인증 실패
증상:
- `localhost:5432` 에서 `replicator`의 `Ident` 인증 실패
- `pg2` 가 `Replica stopped` 상태

원인:
- Replica(`.17`)의 실제 `pg_hba.conf` 에 localhost replication 규칙이 `ident/peer` 로 남아 있었음

해결 (`.17`):
```bash
sudo cp /var/lib/pgsql/17/data/pg_hba.conf /var/lib/pgsql/17/data/pg_hba.conf.bak
sudo sed -i '1ilocal   replication     replicator                                md5' /var/lib/pgsql/17/data/pg_hba.conf
sudo sed -i '2ihost    replication     replicator        127.0.0.1/32          md5' /var/lib/pgsql/17/data/pg_hba.conf
sudo sed -i '3ihost    all             postgres          127.0.0.1/32          md5' /var/lib/pgsql/17/data/pg_hba.conf
sudo systemctl restart patroni
```

이후 `pg2` 가 `streaming` 상태로 정상 전환됨.

---

## 5. 최종 Patroni 구성 핵심

노드별 차이만 반영:

### postgres01
- `name: pg1`
- REST API: `192.168.50.16:8008`
- PostgreSQL connect address: `192.168.50.16:5432`

### postgres02
- `name: pg2`
- REST API: `192.168.50.17:8008`
- PostgreSQL connect address: `192.168.50.17:5432`

공통:
- etcd: `192.168.50.56:2379`
- `wal_log_hints: on`
- `use_pg_rewind: true`
- `use_slots: true`

---

## 6. 최종 검증 결과

정상 상태:
```text
pg1 = Leader / running
pg2 = Replica / streaming
```

복제 확인:
```bash
sudo -u postgres psql -c "SELECT client_addr, state, sync_state, sent_lsn, write_lsn, flush_lsn, replay_lsn FROM pg_stat_replication;"
```

Switchover 성공:
```bash
patronictl -c /etc/patroni/patroni.yml switchover
```

Switchover 후 확인된 상태:
- `pg2` 가 Leader 로 승격 성공
- `pg1` 이 Replica 로 재합류 가능 상태

---

## 7. 운영 중 배운 점

1. Patroni 문제는 `systemd` 보다 `patroni.yml`, 비밀번호, `pg_hba.conf` 가 원인인 경우가 많음
2. `!` 포함 비밀번호는 bash에서 잘 꼬이므로 피하는 것이 좋음
3. Replica가 `stopped` 일 때는 원격 replication보다 로컬 `pg_hba.conf` 의 localhost 인증 규칙을 먼저 의심할 것
4. `patronictl list` 결과만 보지 말고 `journalctl -u patroni` 와 PostgreSQL 로그를 같이 봐야 함
5. switchover 테스트까지 해야 HA 구성이 진짜 검증됨

---

## 8. 다음 권장 작업

1. `pg1` 재합류 상태 최종 확인 (`Replica / streaming`)
2. HAProxy 또는 VIP 구성으로 단일 접속 엔드포인트 제공
3. Patroni REST API(8008) 접근 정책 정리
4. 장애 대응 runbook 작성
5. etcd 단일 노드 구조를 추후 다중 노드로 확장 검토
