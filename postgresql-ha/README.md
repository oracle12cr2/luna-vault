# PostgreSQL HA 구성 가이드 (Patroni + etcd + HAProxy)

> 📝 작성: 루나 (2026-03-16)
> 🏗️ 인프라: 192.168.50.x 대역

---

## 목차

1. [HA 아키텍처 선택지](#ha-아키텍처-선택지)
2. [추천 구성: Patroni + etcd + HAProxy](#추천-구성)
3. [최소 구성 (2노드) vs 권장 구성 (3노드)](#최소-vs-권장-구성)
4. [인프라 구성안](#인프라-구성안)
5. [구축 순서](#구축-순서)
6. [Oracle RAC vs PostgreSQL HA 비교](#oracle-rac-vs-postgresql-ha-비교)
7. [학습 로드맵](#학습-로드맵)

---

## HA 아키텍처 선택지

| 방식 | 특징 | 복잡도 | 추천 |
|------|------|--------|------|
| **Streaming Replication + Patroni** | 자동 Failover, etcd 기반 | ★★★ | ⭐ **가장 추천** |
| **Streaming Replication + repmgr** | 자동 Failover, 간단 | ★★☆ | 입문용 |
| **PgBouncer + HAProxy** | Connection Pooling + LB | ★★☆ | 위 조합과 같이 사용 |
| **Citus** | 분산 DB (샤딩) | ★★★★ | 대규모용 |
| **PostgreSQL BDR** | Multi-Master | ★★★★★ | 엔터프라이즈 |

---

## 추천 구성

### Patroni + etcd + HAProxy

```
                    ┌─────────┐
                    │ HAProxy │  ← VIP / Load Balancer
                    │ (.14)   │
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
         │ PG #1  │ │ PG #2  │ │ PG #3  │
         │Primary │ │Standby │ │Standby │
         │Patroni │ │Patroni │ │Patroni │
         └────┬───┘ └───┬────┘ └───┬────┘
              │         │          │
         ┌────▼─────────▼──────────▼────┐
         │     etcd Cluster (3노드)      │
         │   Leader Election / DCS       │
         └──────────────────────────────┘
```

### 왜 Patroni인가?
- Oracle RAC의 CRS와 유사한 역할 (자동 Failover, Health Check)
- etcd = OCR/Voting Disk 역할 (클러스터 상태 관리)
- 커뮤니티 활발, Zalando(유럽 최대 이커머스)에서 개발/운영
- 자동 pg_rewind로 구 Primary 재합류 지원

---

## 최소 vs 권장 구성

### 2노드 구성 (최소)

```
         ┌────────┐     ┌────────┐
         │ PG #1  │     │ PG #2  │
         │Primary │────▶│Standby │
         │Patroni │     │Patroni │
         └────┬───┘     └───┬────┘
              │             │
         ┌────▼─────────────▼────┐
         │   etcd (기존 redis 겸용) │
         └───────────────────────┘
```

| 항목 | 2노드 | 3노드 |
|------|-------|-------|
| PostgreSQL VM | 2대 | 3대 |
| 자동 Failover | ✅ 가능 | ✅ 가능 |
| Split-brain 방지 | ⚠️ etcd가 판정 | ✅ 과반수 투표 |
| 읽기 분산 | Standby 1대 | Standby 2대 |
| Standby 장애 내성 | ❌ Standby 죽으면 단독 | ✅ 1대 죽어도 Standby 유지 |
| 실무 안정성 | 학습/개발용 충분 | 운영 권장 |

**결론: 학습 목적이면 2노드로 충분해!**
- Primary 1대 + Standby 1대
- etcd는 redis01/02/03 중 하나에 단독으로 돌려도 됨 (학습용)
- 나중에 3노드로 확장 쉬움

### 2노드에서 주의할 점
- etcd 단일 노드 = SPOF(Single Point of Failure)
  - etcd 죽으면 Failover 판정 불가
  - 학습용이면 OK, 운영이면 etcd 3노드 필수
- Standby 장애 시 Primary만 남음 → 복제 없는 상태

---

## 인프라 구성안

### 2노드 구성 (추천 - 학습용)

| 역할 | VM | IP | 비고 |
|------|----|----|------|
| PG Primary + Patroni | postgres01 (기존) | 192.168.50.16 | 기존 활용 |
| PG Standby + Patroni | postgres02 (신규) | 192.168.50.17 | VM 1대만 추가 |
| etcd | redis01 (기존 겸용) | 192.168.50.3 | 단독 etcd |
| HAProxy | haproxy (기존) | 192.168.50.14 | 기존 활용 |

### 3노드 구성 (운영 권장)

| 역할 | VM | IP | 비고 |
|------|----|----|------|
| PG Primary + Patroni | postgres01 | 192.168.50.16 | 기존 |
| PG Standby + Patroni | postgres02 | 192.168.50.17 | 신규 |
| PG Standby + Patroni | postgres03 | 192.168.50.18 | 신규 |
| etcd 클러스터 | redis01/02/03 겸용 | .3/.4/.5 | 기존 3대 활용 |
| HAProxy | haproxy | 192.168.50.14 | 기존 |

---

## 구축 순서

### 1단계: VM 준비 & PostgreSQL 설치

```bash
# Rocky/RHEL 9 기준
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf install -y postgresql16-server postgresql16-contrib
# Patroni가 initdb 하므로 수동 initdb 하지 않음
```

### 2단계: etcd 설치 (redis01 또는 3노드)

#### 단일 노드 (학습용)
```bash
sudo dnf install -y etcd

# /etc/etcd/etcd.conf
cat > /etc/etcd/etcd.conf << 'EOF'
ETCD_NAME="etcd1"
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"
ETCD_ADVERTISE_CLIENT_URLS="http://192.168.50.3:2379"
ETCD_LISTEN_PEER_URLS="http://0.0.0.0:2380"
ETCD_INITIAL_ADVERTISE_PEER_URLS="http://192.168.50.3:2380"
ETCD_INITIAL_CLUSTER="etcd1=http://192.168.50.3:2380"
ETCD_INITIAL_CLUSTER_STATE="new"
ETCD_INITIAL_CLUSTER_TOKEN="pg-cluster-token"
EOF

sudo systemctl enable --now etcd
etcdctl endpoint health
```

#### 3노드 클러스터 (운영용)
```bash
# redis01/02/03 각각에 설치
# ETCD_INITIAL_CLUSTER에 3노드 모두 기술
ETCD_INITIAL_CLUSTER="etcd1=http://192.168.50.3:2380,etcd2=http://192.168.50.4:2380,etcd3=http://192.168.50.5:2380"
```

### 3단계: Patroni 설치 & 구성

```bash
# 모든 PG 노드에 설치
pip3 install patroni[etcd] psycopg2-binary

# systemd 서비스 등록
cat > /etc/systemd/system/patroni.service << 'EOF'
[Unit]
Description=Patroni PostgreSQL HA
After=network.target etcd.service

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni/config.yml
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF
```

#### Primary (postgres01) config.yml
```yaml
scope: pg-cluster
name: pg1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 192.168.50.16:8008

etcd3:
  hosts: 192.168.50.3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        max_connections: 200
        shared_buffers: 2GB
        effective_cache_size: 6GB
        work_mem: 16MB
        maintenance_work_mem: 512MB
        wal_level: replica
        max_wal_senders: 5
        max_replication_slots: 5
        hot_standby: "on"
        wal_log_hints: "on"
        archive_mode: "on"
        archive_command: "/bin/true"

  initdb:
    - encoding: UTF8
    - data-checksums
    - locale: ko_KR.UTF-8

  pg_hba:
    - host replication replicator 192.168.50.0/24 md5
    - host all all 192.168.50.0/24 md5
    - host all all 0.0.0.0/0 md5

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 192.168.50.16:5432
  data_dir: /var/lib/pgsql/16/data
  bin_dir: /usr/pgsql-16/bin
  pgpass: /tmp/pgpass0
  authentication:
    superuser:
      username: postgres
      password: "postgres_password"
    replication:
      username: replicator
      password: "rep_password"
  parameters:
    unix_socket_directories: "/var/run/postgresql"
```

#### Standby (postgres02) config.yml
```yaml
# 동일 구조, 아래만 변경
name: pg2

restapi:
  connect_address: 192.168.50.17:8008

postgresql:
  connect_address: 192.168.50.17:5432
  data_dir: /var/lib/pgsql/16/data
```

### 4단계: Patroni 시작

```bash
# Primary 먼저
sudo systemctl enable --now patroni  # postgres01

# 잠시 대기 후 Standby
sudo systemctl enable --now patroni  # postgres02

# 상태 확인
patronictl -c /etc/patroni/config.yml list
# +--------+--------+---------+---------+----+-----------+
# | Member | Host   | Role    | State   | TL | Lag in MB |
# +--------+--------+---------+---------+----+-----------+
# | pg1    | .16    | Leader  | running |  1 |           |
# | pg2    | .17    | Replica | running |  1 |         0 |
# +--------+--------+---------+---------+----+-----------+
```

### 5단계: HAProxy 설정

```cfg
# /etc/haproxy/haproxy.cfg 에 추가

# Primary (읽기/쓰기)
listen postgres-primary
    bind *:5432
    mode tcp
    option httpchk GET /primary
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server pg1 192.168.50.16:5432 maxconn 100 check port 8008
    server pg2 192.168.50.17:5432 maxconn 100 check port 8008

# Replica (읽기 전용)
listen postgres-replica
    bind *:5433
    mode tcp
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server pg2 192.168.50.17:5432 maxconn 100 check port 8008
```

```bash
sudo systemctl reload haproxy

# 접속 테스트
psql -h 192.168.50.14 -p 5432 -U postgres  # Primary
psql -h 192.168.50.14 -p 5433 -U postgres  # Replica
```

### 6단계: Failover 테스트

```bash
# 클러스터 상태 확인
patronictl -c /etc/patroni/config.yml list

# 수동 Switchover (계획된 전환)
patronictl -c /etc/patroni/config.yml switchover
# Who is the new leader [pg2]? pg2
# Are you sure? Yes

# 자동 Failover 테스트 (비계획 장애)
# Primary에서:
sudo systemctl stop patroni
# → Standby가 자동으로 Primary 승격되는지 확인

# 구 Primary 재합류
sudo systemctl start patroni
# → pg_rewind로 자동 Standby 합류
```

---

## Oracle RAC vs PostgreSQL HA 비교

| 항목 | Oracle RAC | PostgreSQL Patroni |
|------|-----------|-------------------|
| 방식 | Active-Active | Active-Standby |
| Shared Storage | 필수 (ASM) | 불필요 |
| Failover | 자동 (CRS/CSS) | 자동 (Patroni+etcd) |
| Failover 시간 | 30초~수분 | 10~30초 |
| 읽기 분산 | 인스턴스별 분산 | HAProxy → Replica |
| 쓰기 분산 | Active-Active | Primary만 |
| 비용 | 수억원 | **무료** |
| 복잡도 | 매우 높음 | 중간 |
| DCS/투표 | OCR + Voting Disk | etcd |
| 재합류 | 인스턴스 재시작 | pg_rewind 자동 |

---

## 학습 로드맵

```
1주차: PG 기본 (설치, psql, Oracle과 SQL 차이)
  ↓
2주차: Streaming Replication 수동 구성 (pg_basebackup)
  ↓
3주차: etcd + Patroni 자동 Failover
  ↓
4주차: HAProxy + PgBouncer 연동
  ↓
5주차: 모니터링 (pg_stat_*, Grafana 연동)
  ↓
6주차: 백업/복구 (pg_dump, pg_basebackup, pgBackRest)
```

---

## 참고 자료
- [Patroni 공식 문서](https://patroni.readthedocs.io/)
- [Zalando Patroni GitHub](https://github.com/zalando/patroni)
- [etcd 공식 문서](https://etcd.io/docs/)
- [HAProxy PostgreSQL Health Check](https://www.haproxy.com/documentation/)
