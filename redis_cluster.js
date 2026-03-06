'use strict'
const fp = require('fastify-plugin')
const { createCluster } = require('redis')

async function redisPlugin(fastify) {
    const nodes = process.env.REDIS_NODES.split(',').map(node => {
        const [host, port] = node.trim().split(':')
        return { url: `redis://${host}:${port}` }
    })

    const cluster = createCluster({
        rootNodes: nodes,
        defaults: {
            password: process.env.REDIS_PASSWORD
        },
        useReplicas: false
    })

    cluster.on('error', (err) => fastify.log.error({ err }, 'Redis error'))
    await cluster.connect()
    fastify.decorate('redis', cluster)

    // 캐시 헬퍼
    fastify.decorate('cache', {
        async get(key, ttl, fn) {
            const cached = await cluster.get(key)
            if (cached) return JSON.parse(cached)
            const data = await fn()
            await cluster.setEx(key, ttl, JSON.stringify(data))
            return data
        },
        async del(key) {
            await cluster.del(key)
        },
        async delPattern(pattern) {
            const nodes = cluster.masters
            for (const node of nodes) {
                let cursor = 0
                do {
                    const result = await node.client.sendCommand(['SCAN', String(cursor), 'MATCH', pattern, 'COUNT', '100'])
                    cursor = parseInt(result[0])
                    const keys = result[1]
                    if (keys.length > 0) {
                        for (const key of keys) {
                            await cluster.del(key)
                        }
                    }
                } while (cursor !== 0)
            }
        }
    })

    fastify.addHook('onClose', async () => { await cluster.quit() })
    fastify.log.info('Redis Cluster connected')
}

module.exports = fp(redisPlugin)
