'use strict'
const fp = require('fastify-plugin')

// 환율 API: 한국수출입은행 (무료, 인증키 필요없는 대안으로 exchangerate-api 사용)
const CACHE_KEY = 'exchange:usd:krw'
const CACHE_TTL = 3600 // 1시간

async function exchangeRoutes(fastify) {

    // USD/KRW 환율 조회
    fastify.get('/', async (request, reply) => {
        try {
            // Redis 캐시 확인
            const cached = await fastify.redis.get(CACHE_KEY)
            if (cached) {
                return JSON.parse(cached)
            }

            // 캐시 없으면 fetch
            const data = await fetchExchangeRate()
            await fastify.redis.setEx(CACHE_KEY, CACHE_TTL, JSON.stringify(data))
            return data
        } catch (err) {
            fastify.log.error(err, 'Exchange rate fetch error')
            reply.code(500).send({ error: '환율 정보를 가져올 수 없습니다.' })
        }
    })

    // 환율 히스토리 (최근 7일)
    fastify.get('/history', async (request, reply) => {
        try {
            const historyKey = 'exchange:usd:krw:history'
            const cached = await fastify.redis.get(historyKey)
            if (cached) {
                return JSON.parse(cached)
            }
            return { history: [] }
        } catch (err) {
            fastify.log.error(err, 'Exchange history error')
            reply.code(500).send({ error: '환율 히스토리를 가져올 수 없습니다.' })
        }
    })

    // 1시간마다 환율 갱신 (서버 시작 시 즉시 1회 + setInterval)
    fastify.addHook('onReady', async () => {
        await refreshRate(fastify)
        setInterval(() => refreshRate(fastify), CACHE_TTL * 1000)
    })
}

async function fetchExchangeRate() {
    // Open ExchangeRate API (무료, 키 불필요)
    const res = await fetch('https://open.er-api.com/v6/latest/USD')
    const json = await res.json()

    if (json.result !== 'success') {
        throw new Error('Exchange API error')
    }

    const rate = json.rates.KRW
    const now = new Date()

    return {
        base: 'USD',
        target: 'KRW',
        rate: rate,
        rateFormatted: rate.toLocaleString('ko-KR', { maximumFractionDigits: 2 }),
        updatedAt: now.toISOString(),
        updatedAtKR: now.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }),
        source: 'open.er-api.com'
    }
}

async function refreshRate(fastify) {
    try {
        const data = await fetchExchangeRate()
        await fastify.redis.setEx(CACHE_KEY, CACHE_TTL, JSON.stringify(data))

        // 히스토리에 추가 (최근 168개 = 7일 * 24시간)
        const historyKey = 'exchange:usd:krw:history'
        let history = []
        const cached = await fastify.redis.get(historyKey)
        if (cached) {
            history = JSON.parse(cached)
        }
        history.push({
            rate: data.rate,
            time: data.updatedAt
        })
        // 최근 168개만 유지
        if (history.length > 168) {
            history = history.slice(-168)
        }
        await fastify.redis.setEx(historyKey, 86400 * 7, JSON.stringify({ history }))

        fastify.log.info(`Exchange rate updated: 1 USD = ${data.rateFormatted} KRW`)
    } catch (err) {
        fastify.log.error(err, 'Exchange rate refresh failed')
    }
}

module.exports = exchangeRoutes
