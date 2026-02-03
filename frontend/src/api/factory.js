/**
 * API工厂函数 - 统一CRUD操作模式
 */
import request from './http'

/**
 * 创建统一的API接口
 * @param {string} baseUrl - API基础路径 (例如: '/api/v1/topics/')
 * @returns {Object} 包含CRUD操作的API对象
 */
export function createAPI(baseUrl) {
  // 确保baseUrl以/结尾
  const base = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`

  return {
    /**
     * 获取列表数据
     * @param {Object} params - 查询参数 (page, page_size, search, filters等)
     * @returns {Promise} 返回包含results和count的对象
     */
    getList(params = {}) {
      return request({
        url: base,
        method: 'get',
        params
      })
    },

    /**
     * 获取单条详情
     * @param {number|string} id - 资源ID
     * @returns {Promise} 返回详情数据
     */
    getDetail(id) {
      return request({
        url: `${base}${id}/`,
        method: 'get'
      })
    },

    /**
     * 创建新资源
     * @param {Object} data - 创建数据
     * @returns {Promise} 返回创建的资源
     */
    create(data) {
      return request({
        url: base,
        method: 'post',
        data
      })
    },

    /**
     * 更新资源
     * @param {number|string} id - 资源ID
     * @param {Object} data - 更新数据
     * @returns {Promise} 返回更新后的资源
     */
    update(id, data) {
      return request({
        url: `${base}${id}/`,
        method: 'put',
        data
      })
    },

    /**
     * 部分更新资源
     * @param {number|string} id - 资源ID
     * @param {Object} data - 更新数据
     * @returns {Promise} 返回更新后的资源
     */
    patch(id, data) {
      return request({
        url: `${base}${id}/`,
        method: 'patch',
        data
      })
    },

    /**
     * 删除资源
     * @param {number|string} id - 资源ID
     * @returns {Promise}
     */
    delete(id) {
      return request({
        url: `${base}${id}/`,
        method: 'delete'
      })
    },

    /**
     * 执行自定义action
     * @param {number|string} id - 资源ID
     * @param {string} actionName - action名称
     * @param {Object} data - 请求数据
     * @param {string} method - HTTP方法 (默认post)
     * @returns {Promise}
     */
    action(id, actionName, data = {}, method = 'post') {
      return request({
        url: `${base}${id}/${actionName}/`,
        method,
        data
      })
    },

    /**
     * 执行列表级别的自定义action
     * @param {string} actionName - action名称
     * @param {Object} data - 请求数据
     * @param {string} method - HTTP方法 (默认post)
     * @returns {Promise}
     */
    listAction(actionName, data = {}, method = 'post') {
      return request({
        url: `${base}${actionName}/`,
        method,
        data
      })
    }
  }
}

/**
 * 创建带统计功能的API
 * @param {string} baseUrl - API基础路径
 * @returns {Object} 包含CRUD操作和统计功能的API对象
 */
export function createStatsAPI(baseUrl) {
  const api = createAPI(baseUrl)

  return {
    ...api,

    /**
     * 获取统计数据
     * @param {Object} params - 查询参数
     * @returns {Promise}
     */
    getStats(params = {}) {
      return request({
        url: `${baseUrl}stats/`,
        method: 'get',
        params
      })
    }
  }
}
